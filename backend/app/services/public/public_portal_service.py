
from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.customer_account import CustomerAccount
from app.models.lead_record import LeadRecord
from app.models.business import Business
from app.models.demo_request_log import DemoRequestLog
from app.models.provisioning_decision_log import ProvisioningDecisionLog
from app.models.package_plan import PackagePlan
from app.models.onboarding_session import OnboardingSession
from app.models.login_challenge import LoginChallenge
from app.services.auth.customer_auth_service import CustomerAuthService
from app.services.auth.login_challenge_service import LoginChallengeService
from app.services.auth.login_delivery_service import LoginDeliveryService
from app.services.common.rate_limit_service import RateLimitService
from app.services.public.onboarding_transition_service import OnboardingTransitionService


class PublicPortalService:
    MAGIC_LINK_MINUTES = 20

    def __init__(self) -> None:
        self.challenge_service = LoginChallengeService()
        self.delivery_service = LoginDeliveryService()
        self.rate_limit_service = RateLimitService()
        self.transition_service = OnboardingTransitionService()

    def _list_package_plans(self, db: Session) -> list[PackagePlan]:
        items = db.query(PackagePlan).filter(PackagePlan.is_active == True).order_by(PackagePlan.id.asc()).all()
        if items:
            return items
        # fallback safety for starter repo when seed not run yet
        return [
            PackagePlan(name='Demo', monthly_demo_limit=2, description='Public demo access', is_default=True, is_active=True, customer_portal_enabled=True, requires_contact_verification=False, billing_mode='demo'),
            PackagePlan(name='Starter', monthly_demo_limit=2, description='Starter access', is_default=False, is_active=True, customer_portal_enabled=True, requires_contact_verification=True, billing_mode='subscription'),
            PackagePlan(name='Business', monthly_demo_limit=4, description='Business access', is_default=False, is_active=True, customer_portal_enabled=True, requires_contact_verification=True, billing_mode='subscription'),
            PackagePlan(name='Pro', monthly_demo_limit=6, description='Pro access', is_default=False, is_active=True, customer_portal_enabled=True, requires_contact_verification=True, billing_mode='subscription'),
        ]

    def _default_package_name(self, db: Session) -> str:
        plans = self._list_package_plans(db)
        for p in plans:
            if getattr(p, 'is_default', False):
                return p.name
        return plans[0].name if plans else 'Demo'

    def package_plans(self, db: Session):
        return [
            {
                'name': p.name,
                'monthly_demo_limit': p.monthly_demo_limit,
                'description': p.description,
                'is_default': p.is_default,
                'is_active': p.is_active,
                'customer_portal_enabled': getattr(p, 'customer_portal_enabled', True),
                'requires_contact_verification': getattr(p, 'requires_contact_verification', False),
                'billing_mode': getattr(p, 'billing_mode', 'demo'),
            } for p in self._list_package_plans(db)
        ]

    def _resolve_package_name(self, db: Session, customer_phone: str | None, requested_package: str | None = None) -> str:
        if requested_package:
            return requested_package
        if customer_phone:
            account = db.query(CustomerAccount).filter(CustomerAccount.phone == customer_phone).first()
            if account and account.package_name:
                return account.package_name
        return self._default_package_name(db)

    def _limit_for_package(self, db: Session, package_name: str) -> int:
        plan = db.query(PackagePlan).filter(PackagePlan.name == package_name, PackagePlan.is_active == True).first()
        if plan:
            return plan.monthly_demo_limit
        # fallback to default
        return 2

    def _current_month_count(self, db: Session, customer_phone: str | None) -> int:
        if not customer_phone:
            return 0
        start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        q = db.query(DemoRequestLog).filter(DemoRequestLog.customer_phone == customer_phone, DemoRequestLog.created_at >= start)
        return q.count()

    def _get_or_create_session(self, db: Session, *, customer_phone: str, business_name: str, package_name: str | None = None) -> OnboardingSession:
        session = db.query(OnboardingSession).filter(
            OnboardingSession.customer_phone == customer_phone,
            OnboardingSession.business_name == business_name,
        ).order_by(OnboardingSession.id.desc()).first()
        if session:
            return session
        session = OnboardingSession(
            customer_phone=customer_phone,
            business_name=business_name,
            current_state='intake_preview',
            package_name=package_name,
            next_action='Complete intake preview',
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def _update_session(self, db: Session, session: OnboardingSession, *, new_state: str, next_action: str | None = None,
                        package_name: str | None = None, lead_id: int | None = None, business_id: int | None = None,
                        customer_account_id: int | None = None, last_preview_score: int | None = None, notes: str | None = None):
        ok, err = self.transition_service.validate(session.current_state, new_state)
        if not ok:
            raise ValueError(err)
        session.previous_state = session.current_state
        session.current_state = new_state
        if next_action is not None:
            session.next_action = next_action
        if package_name is not None:
            session.package_name = package_name
        if lead_id is not None:
            session.lead_id = lead_id
        if business_id is not None:
            session.business_id = business_id
        if customer_account_id is not None:
            session.customer_account_id = customer_account_id
        if last_preview_score is not None:
            session.last_preview_score = last_preview_score
        if notes is not None:
            session.notes = notes
        db.add(session)
        db.commit()
        db.refresh(session)
        return session


    def _public_challenge_limit(self, db: Session, customer_phone: str, challenge_type: str) -> tuple[bool, int, int]:
        return self.rate_limit_service.check_and_record(
            db,
            scope='public_challenge',
            key=f"{challenge_type}:{customer_phone}",
            action='request',
            window_minutes=settings.public_challenge_window_minutes,
            max_per_window=settings.public_challenge_max_per_window,
            detail='public challenge request',
        )

    def _package_gate_summary(self, db: Session, package_name: str | None) -> tuple[bool, str]:
        if not package_name:
            package_name = self._default_package_name(db)
        plan = db.query(PackagePlan).filter(PackagePlan.name == package_name, PackagePlan.is_active == True).first()
        if not plan:
            return True, 'No active package plan found; falling back to default public access.'
        if not getattr(plan, 'customer_portal_enabled', True):
            return False, f'Package {package_name} currently does not allow portal login requests.'
        if getattr(plan, 'billing_mode', 'demo') not in {'demo', 'subscription', 'manual'}:
            return False, f'Package {package_name} has an unsupported billing mode for public login flow.'
        return True, f'Package {package_name} allows public login flow.'

    def home_content(self, db: Session):
        default_pkg = self._default_package_name(db)
        default_limit = self._limit_for_package(db, default_pkg)
        return {
            'title': 'LocalBiz AutoSite Platform',
            'subtitle': 'מערכת חכמה שמרכזת איסוף מידע ציבורי, זיהוי חוסרים, יצירת אתר הדגמה, תפעול פניות, וניהול לקוחות במקום אחד.',
            'admin_email': settings.admin_seed_email,
            'admin_name': settings.admin_seed_name,
            'monthly_demo_limit': default_limit,
            'features': [
                'איסוף מידע ציבורי והשלמת חוסרים לעסק',
                'יצירת אתר הדגמה איכותי עם מבנה מקצועי',
                'פנייה מבוססת וואטסאפ ומעקב תגובות',
                'אזור לקוח מוגבל ומאובטח',
                'מנכ״ל AI שמנטר, מסכם וממליץ',
            ],
            'steps': [
                'מזינים את פרטי העסק שכבר ידועים לכם.',
                'המערכת בודקת אילו נתונים קיימים ומה עדיין חסר לאתר חזק.',
                'לאחר השלמה, אפשר לבקש אתר הדגמה ולבחון איך העסק יכול להיראות.',
                'המערכת תומכת גם בהמשך הדרך: פניות, תשלום, הפעלה, ופורטל לקוח.'
            ],
            'faq': [
                {'q': 'האם אפשר לבקש הדגמת אתר בלי להכניס הכול?', 'a': 'כן. אפשר להזין רק מה שיש, והמערכת תגיד בדיוק מה חסר כדי להגיע להדגמה חזקה יותר.'},
                {'q': 'האם מגבלת הדגמות תלויה בחבילה?', 'a': 'כן. המערכת שומרת policy ברמת חבילה, ולכן לקוחות שונים עשויים לקבל מגבלת הדגמות שונה.'},
                {'q': 'האם הלקוח רואה את כל המידע?', 'a': 'לא. כל לקוח רואה רק את מה ששייך אליו. מידע פנימי נשמר לאדמין ולמערכת בלבד.'},
            ],
        }

    def login_options(self):
        return {
            'admin_email': settings.admin_seed_email,
            'customer_login_methods': ['טלפון + סיסמה זמנית ייחודית', 'Magic link בסיסי', 'OTP בסיסי'],
            'customer_default_onboarding': 'לכל לקוח נוצרת גישה ראשונית ייחודית. בכניסה הראשונה הוא מתבקש להחליף סיסמה.'
        }

    def demo_request_availability(self, db: Session, customer_phone: str | None, package_name: str | None = None):
        resolved_package = self._resolve_package_name(db, customer_phone, package_name)
        monthly_limit = self._limit_for_package(db, resolved_package)
        current = self._current_month_count(db, customer_phone)
        remaining = max(0, monthly_limit - current)
        return {
            'customer_phone': customer_phone,
            'package_name': resolved_package,
            'monthly_demo_limit': monthly_limit,
            'current_month_count': current,
            'remaining_demo_requests': remaining,
            'can_request_demo_site': remaining > 0,
            'policy_note': f'Package {resolved_package} currently allows up to {monthly_limit} demo requests in the active monthly window.',
        }

    def _find_existing_business(self, db: Session, payload):
        q = db.query(Business)
        if payload.phone:
            existing = q.filter(Business.phone == payload.phone).first()
            if existing:
                return existing, 'Matched existing business by phone'
        if payload.business_name and (payload.city or settings.default_city):
            existing = q.filter(Business.name == payload.business_name, Business.city == (payload.city or settings.default_city)).first()
            if existing:
                return existing, 'Matched existing business by name and city'
        return None, None

    def _find_existing_lead(self, db: Session, payload):
        q = db.query(LeadRecord)
        if payload.phone:
            existing = q.filter(LeadRecord.phone == payload.phone).first()
            if existing:
                return existing, 'Matched existing lead by phone'
        if payload.business_name and (payload.city or settings.default_city):
            existing = q.filter(LeadRecord.imported_name == payload.business_name, LeadRecord.city == (payload.city or settings.default_city)).first()
            if existing:
                return existing, 'Matched existing lead by name and city'
        return None, None

    def _create_decision_log(self, db: Session, *, customer_phone: str, decision_type: str, onboarding_state: str,
                             package_name: str | None = None, lead_id=None, business_id=None, customer_account_id=None,
                             decision_reason: str | None = None, previous_state: str | None = None,
                             next_action: str | None = None, notes: str | None = None):
        row = ProvisioningDecisionLog(
            customer_phone=customer_phone,
            decision_type=decision_type,
            onboarding_state=onboarding_state,
            package_name=package_name,
            lead_id=lead_id,
            business_id=business_id,
            customer_account_id=customer_account_id,
            decision_reason=decision_reason,
            previous_state=previous_state,
            next_action=next_action,
            notes=notes,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def intake_preview(self, db: Session, payload):
        pulled_fields = {
            'business_name': payload.business_name,
            'city': payload.city or settings.default_city,
            'category': payload.category,
            'phone': payload.phone,
            'address': payload.address,
            'website_url': payload.website_url,
            'facebook_url': payload.facebook_url,
            'instagram_url': payload.instagram_url,
            'contact_name': payload.contact_name,
            'owner_email': payload.owner_email,
        }
        missing_fields = []
        if not payload.phone:
            missing_fields.append('phone')
        if not payload.address:
            missing_fields.append('address')
        if not payload.category:
            missing_fields.append('category')
        if not payload.facebook_url:
            missing_fields.append('facebook_url')
        if not payload.instagram_url:
            missing_fields.append('instagram_url')
        if not payload.contact_name:
            missing_fields.append('contact_name')
        readiness_score = max(20, 100 - len(missing_fields) * 12)
        strengths = []
        if payload.phone:
            strengths.append('יש טלפון ליצירת קשר ישירה באתר.')
        if payload.address:
            strengths.append('יש כתובת/מיקום שמחזק אמון מקומי.')
        if payload.facebook_url or payload.instagram_url:
            strengths.append('יש פרופיל חברתי שיכול לשפר אמון ותוכן חזותי.')
        if payload.category:
            strengths.append('הקטגוריה ידועה ולכן ניתן להתאים מבנה תוכן ותבנית טובים יותר.')

        customer_phone = payload.customer_phone or payload.phone
        availability = self.demo_request_availability(db, customer_phone)
        improvements = []
        if 'phone' in missing_fields:
            improvements.append('הוסף מספר טלפון ראשי כדי לאפשר CTA חזק ליצירת קשר באתר.')
        if 'facebook_url' in missing_fields or 'instagram_url' in missing_fields:
            improvements.append('הוסף פייסבוק או אינסטגרם כדי לשפר אמון, גלריה ותוכן חברתי.')
        if 'address' in missing_fields:
            improvements.append('הוסף כתובת מלאה או לפחות אזור שירות כדי לשפר אמון מקומי ומקטע מיקום.')
        if 'category' in missing_fields:
            improvements.append('בחר קטגוריה כדי שהמערכת תתאים תבנית, שירותים ושפה שיווקית מדויקים יותר.')
        if not strengths:
            strengths.append('כדאי להשלים לפחות טלפון, קטגוריה וכתובת כדי להגיע להדגמה חזקה באמת.')

        next_step = 'השלם את החוסרים המרכזיים ואז בקש אתר הדגמה דרך כניסת לקוח.' if availability['can_request_demo_site'] else 'הגעת למגבלת ההדגמות החודשית עבור החבילה הנוכחית. ניתן להמשיך דרך אזור הלקוח או לשדרג חבילה.'
        if customer_phone:
            session = self._get_or_create_session(db, customer_phone=customer_phone, business_name=payload.business_name, package_name=availability['package_name'])
            self._update_session(db, session, new_state='intake_preview', next_action='Complete missing fields and request demo', last_preview_score=readiness_score)
        return {
            'business_name': payload.business_name,
            'normalized_city': payload.city or settings.default_city,
            'normalized_category': payload.category,
            'pulled_fields': pulled_fields,
            'missing_fields': missing_fields,
            'readiness_score': readiness_score,
            'monthly_demo_limit': availability['monthly_demo_limit'],
            'current_month_count': availability['current_month_count'],
            'can_request_demo_site': availability['can_request_demo_site'],
            'next_step': next_step,
            'suggested_improvements': improvements,
            'strengths': strengths,
        }

    def _log_demo_request(self, db: Session, *, customer_phone: str, payload, onboarding_state: str, lead_id=None, business_id=None, customer_account_id=None, dedup_reason=None, status='demo_requested', notes=None, previous_state=None, next_action=None, package_name_snapshot=None):
        row = DemoRequestLog(
            customer_phone=customer_phone,
            business_name=payload.business_name,
            city=payload.city or settings.default_city,
            category=payload.category,
            status=status,
            onboarding_state=onboarding_state,
            lead_id=lead_id,
            business_id=business_id,
            customer_account_id=customer_account_id,
            dedup_reason=dedup_reason,
            package_name_snapshot=package_name_snapshot,
            previous_state=previous_state,
            next_action=next_action,
            notes=notes,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row



    def _auto_prepare_draft(self, db: Session, business: Business, readiness_score: int | None = None) -> str:
        if business.status in {'new', 'reviewed'} and (readiness_score or 0) >= 60:
            business.status = 'ready_for_draft'
            db.add(business)
            db.commit()
            return 'Business moved to ready_for_draft automatically based on onboarding readiness.'
        return 'Business kept in current status pending additional review.'

    def demo_request_status(self, db: Session, customer_phone: str | None):
        q = db.query(DemoRequestLog)
        if customer_phone:
            q = q.filter(DemoRequestLog.customer_phone == customer_phone)
        rows = q.order_by(DemoRequestLog.id.desc()).limit(50).all()
        return {
            'items': [
                {
                    'id': row.id,
                    'customer_phone': row.customer_phone,
                    'business_name': row.business_name,
                    'city': row.city,
                    'category': row.category,
                    'status': row.status,
                    'onboarding_state': row.onboarding_state,
                    'lead_id': row.lead_id,
                    'business_id': row.business_id,
                    'customer_account_id': row.customer_account_id,
                    'dedup_reason': row.dedup_reason,
                    'package_name_snapshot': row.package_name_snapshot,
                    'previous_state': row.previous_state,
                    'next_action': row.next_action,
                } for row in rows
            ],
            'total': len(rows),
        }

    def demo_status_summary(self, db: Session, customer_phone: str | None):
        availability = self.demo_request_availability(db, customer_phone)
        rows = db.query(DemoRequestLog).filter(DemoRequestLog.customer_phone == customer_phone).order_by(DemoRequestLog.id.desc()).all() if customer_phone else []
        latest = rows[0] if rows else None
        session = db.query(OnboardingSession).filter(OnboardingSession.customer_phone == customer_phone).order_by(OnboardingSession.id.desc()).first() if customer_phone else None
        current_state = getattr(session, 'current_state', None) or getattr(latest, 'onboarding_state', None)
        latest_next_action = getattr(session, 'next_action', None) or getattr(latest, 'next_action', None)
        return {
            'customer_phone': customer_phone,
            'package_name': availability['package_name'],
            'current_state': current_state,
            'last_business_id': getattr(session, 'business_id', None) or getattr(latest, 'business_id', None),
            'last_customer_account_id': getattr(session, 'customer_account_id', None) or getattr(latest, 'customer_account_id', None),
            'monthly_demo_limit': availability['monthly_demo_limit'],
            'current_month_count': availability['current_month_count'],
            'remaining_demo_requests': availability['remaining_demo_requests'],
            'latest_next_action': latest_next_action,
            'history_count': len(rows),
        }

    def demo_compare(self, db: Session, customer_phone: str | None):
        status = self.demo_request_status(db, customer_phone)
        summary = self.demo_status_summary(db, customer_phone)
        availability = self.demo_request_availability(db, customer_phone, summary.get('package_name'))
        return {
            'customer_phone': customer_phone,
            'availability': availability,
            'summary': summary,
            'recent_items': status['items'][:5],
        }

    def request_demo(self, db: Session, payload):
        preview = self.intake_preview(db, payload)
        customer_phone = payload.customer_phone or payload.phone
        if not customer_phone:
            raise ValueError('Customer phone or business phone is required for demo provisioning')
        package_name = self._resolve_package_name(db, customer_phone, getattr(payload, 'package_name', None))
        availability = self.demo_request_availability(db, customer_phone, package_name)
        session = self._get_or_create_session(db, customer_phone=customer_phone, business_name=payload.business_name, package_name=package_name)

        existing_business, business_reason = self._find_existing_business(db, payload)
        existing_lead, lead_reason = self._find_existing_lead(db, payload)

        if existing_business and existing_lead:
            account = db.query(CustomerAccount).filter(CustomerAccount.phone == customer_phone).first()
            temp_password = None
            reused_existing_customer = account is not None
            if payload.create_customer_account and account is None:
                auth = CustomerAuthService()
                account, temp_password = auth.create_customer_account(
                    db,
                    business_id=existing_business.id,
                    phone=customer_phone,
                    email=payload.owner_email,
                    contact_name=payload.contact_name,
                    package_name=package_name,
                )
                reused_existing_customer = False
            dedup_reason = business_reason or lead_reason or 'Existing lead/business reused'
            self._log_demo_request(db, customer_phone=customer_phone, payload=payload, onboarding_state='existing_record_reused', lead_id=existing_lead.id, business_id=existing_business.id, customer_account_id=getattr(account, 'id', None), dedup_reason=dedup_reason, status='reused', previous_state=session.current_state, next_action='Open existing customer/business context', package_name_snapshot=package_name)
            self._create_decision_log(db, customer_phone=customer_phone, decision_type='reuse_existing_records', onboarding_state='existing_record_reused', package_name=package_name, lead_id=existing_lead.id, business_id=existing_business.id, customer_account_id=getattr(account, 'id', None), decision_reason=dedup_reason, previous_state=session.current_state, next_action='Open existing customer/business context')
            self._update_session(db, session, new_state='existing_record_reused', next_action='Open existing customer/business context', lead_id=existing_lead.id, business_id=existing_business.id, customer_account_id=getattr(account, 'id', None), last_preview_score=preview['readiness_score'])
            return {
                'ok': True,
                'message': 'Demo request matched existing records',
                'lead_id': existing_lead.id,
                'business_id': existing_business.id,
                'customer_account_id': getattr(account, 'id', None),
                'temp_password': temp_password,
                'demo_limit_remaining': availability['remaining_demo_requests'],
                'next_step': 'המערכת זיהתה רשומה קיימת וחיברה אותך לתהליך הקיים במקום ליצור כפילות.',
                'created_new_lead': False,
                'created_new_business': False,
                'reused_existing_customer': reused_existing_customer,
                'dedup_reason': dedup_reason,
                'onboarding_state': 'existing_record_reused',
                'package_name': package_name,
                'provisioning_decision_summary': 'Reused existing lead/business/customer context',
            }

        if not availability['can_request_demo_site']:
            self._create_decision_log(db, customer_phone=customer_phone, decision_type='demo_limit_block', onboarding_state='limit_reached', package_name=package_name, decision_reason='Package monthly demo limit reached', previous_state=session.current_state, next_action='Offer upgrade or wait for next cycle')
            self._update_session(db, session, new_state='limit_reached', next_action='Offer upgrade or wait for next cycle', last_preview_score=preview['readiness_score'])
            raise ValueError('Monthly demo limit reached for this customer package')

        lead = existing_lead
        created_new_lead = False
        dedup_reason = None
        if lead is None:
            lead = LeadRecord(
                imported_name=payload.business_name,
                city=payload.city or settings.default_city,
                category=payload.category,
                phone=payload.phone,
                address=payload.address,
                website_url=payload.website_url,
                score=preview['readiness_score'],
                status='qualified' if preview['readiness_score'] >= 60 else 'needs_review',
                notes='Created from public request-demo flow',
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            created_new_lead = True
        else:
            dedup_reason = lead_reason

        business = existing_business
        created_new_business = False
        if business is None:
            business = Business(
                name=payload.business_name,
                city=payload.city or settings.default_city,
                category=payload.category,
                status='ready_for_draft' if preview['readiness_score'] >= 60 else 'reviewed',
                phone=payload.phone,
                address=payload.address,
                lead_id=lead.id,
                notes='Provisioned from public request-demo flow',
            )
            db.add(business)
            db.commit()
            db.refresh(business)
            created_new_business = True
        else:
            business.lead_id = business.lead_id or lead.id
            if business.status in ('new', 'reviewed') and preview['readiness_score'] >= 60:
                business.status = 'ready_for_draft'
            db.add(business)
            db.commit()
            db.refresh(business)
            dedup_reason = dedup_reason or business_reason

        account = db.query(CustomerAccount).filter(CustomerAccount.phone == customer_phone).first()
        temp_password = None
        reused_existing_customer = account is not None
        if payload.create_customer_account and not account:
            auth = CustomerAuthService()
            account, temp_password = auth.create_customer_account(
                db,
                business_id=business.id,
                phone=customer_phone,
                email=payload.owner_email,
                contact_name=payload.contact_name,
                package_name=package_name,
            )
            reused_existing_customer = False

        remaining_after = max(0, availability['remaining_demo_requests'] - 1)
        next_step = 'הדגמת העסק נרשמה במערכת. העסק סומן להכנת טיוטה, והלקוח יכול להיכנס עם הטלפון והסיסמה הזמנית ולבקש להמשיך.'
        onboarding_state = 'customer_account_created' if getattr(account, 'id', None) else 'demo_requested'
        if not created_new_lead or not created_new_business:
            onboarding_state = 'partially_reused'

        self._log_demo_request(db, customer_phone=customer_phone, payload=payload, onboarding_state=onboarding_state, lead_id=lead.id, business_id=business.id, customer_account_id=getattr(account, 'id', None), dedup_reason=dedup_reason, status='provisioned', previous_state=session.current_state, next_action='Prepare draft and customer handoff', package_name_snapshot=package_name)
        self._create_decision_log(db, customer_phone=customer_phone, decision_type='provision_demo_request', onboarding_state=onboarding_state, package_name=package_name, lead_id=lead.id, business_id=business.id, customer_account_id=getattr(account, 'id', None), decision_reason=dedup_reason or 'Fresh provisioning flow', previous_state=session.current_state, next_action='Prepare draft and customer handoff', notes='Created or reused core records from public demo request')
        self._update_session(db, session, new_state=onboarding_state, next_action='Prepare draft and customer handoff', package_name=package_name, lead_id=lead.id, business_id=business.id, customer_account_id=getattr(account, 'id', None), last_preview_score=preview['readiness_score'])
        return {
            'ok': True,
            'message': 'Demo request provisioned successfully',
            'lead_id': lead.id,
            'business_id': business.id,
            'customer_account_id': getattr(account, 'id', None),
            'temp_password': temp_password,
            'demo_limit_remaining': remaining_after,
            'next_step': next_step,
            'created_new_lead': created_new_lead,
            'created_new_business': created_new_business,
            'reused_existing_customer': reused_existing_customer,
            'dedup_reason': dedup_reason,
            'onboarding_state': onboarding_state,
            'package_name': package_name,
            'provisioning_decision_summary': 'Provisioned demo request and prepared next action',
        }


    def request_magic_link(self, db: Session, customer_phone: str, business_name: str | None = None, source_ip: str | None = None, session_key: str | None = None):
        allowed, current, max_allowed = self.rate_limit_service.check_public_login_rate(db, phone=customer_phone, source_ip=source_ip, session_key=session_key, action='magic_link_request', window_minutes=settings.public_challenge_window_minutes, max_per_window=settings.public_challenge_max_per_window)
        if not allowed:
            self.delivery_service.prepare_delivery(db, customer_phone=customer_phone, challenge_type='magic_link', challenge_id=None, was_rate_limited=True, detail='magic link request blocked by rate limit')
            raise ValueError('Magic link request rate limited')
        account = db.query(CustomerAccount).filter(CustomerAccount.phone == customer_phone, CustomerAccount.is_active == True).first()
        if not account:
            raise ValueError('No active customer account found for this phone')
        allowed_by_package, note = self._package_gate_summary(db, account.package_name)
        if not allowed_by_package:
            raise ValueError(note)
        session = self._get_or_create_session(db, customer_phone=customer_phone, business_name=business_name or f'customer-{account.business_id}', package_name=account.package_name)
        challenge = self.challenge_service.create_magic_link(db, customer_phone=customer_phone, customer_account_id=account.id, onboarding_session_id=session.id)
        self._update_session(db, session, new_state='magic_link_requested', next_action='Use magic link to enter customer portal', customer_account_id=account.id)
        delivery = self.delivery_service.dispatch_preview(db, challenge_type='magic_link', customer_phone=customer_phone, challenge_id=challenge.id, payload_preview=challenge.token[:8] + '…')
        return {
            'ok': True,
            'customer_phone': customer_phone,
            'onboarding_state': session.current_state,
            'token_preview': challenge.token[:8] + '…',
            'expires_in_minutes': self.MAGIC_LINK_MINUTES,
            'next_step': 'Magic link prepared and logged in delivery abstraction layer.',
            'challenge_id': challenge.id,
            'delivery_status': delivery.status,
            'rate_limit_remaining_hint': max(0, max_allowed - (current + 1)),
        }

    def request_otp(self, db: Session, customer_phone: str, business_name: str | None = None, source_ip: str | None = None, session_key: str | None = None, extension: str | None = None):
        allowed, current, max_allowed = self.rate_limit_service.check_public_login_rate(db, phone=customer_phone, source_ip=source_ip, session_key=session_key, action='otp_request', window_minutes=settings.public_challenge_window_minutes, max_per_window=settings.public_challenge_max_per_window)
        if not allowed:
            self.delivery_service.prepare_delivery(db, customer_phone=customer_phone, challenge_type='otp', challenge_id=None, was_rate_limited=True, detail='otp request blocked by rate limit')
            raise ValueError('OTP request rate limited')
        account = db.query(CustomerAccount).filter(CustomerAccount.phone == customer_phone, CustomerAccount.is_active == True).first()
        if not account:
            raise ValueError('No active customer account found for this phone')
        allowed_by_package, note = self._package_gate_summary(db, account.package_name)
        if not allowed_by_package:
            raise ValueError(note)
        session = self._get_or_create_session(db, customer_phone=customer_phone, business_name=business_name or f'customer-{account.business_id}', package_name=account.package_name)
        challenge = self.challenge_service.create_otp(db, customer_phone=customer_phone, customer_account_id=account.id, onboarding_session_id=session.id)
        self._update_session(db, session, new_state='otp_requested', next_action='Use OTP to enter customer portal', customer_account_id=account.id)
        # Encode optional extension into payload_preview (e.g. "OTP:1234;ext=2")
        ext_suffix = f';ext={str(int(extension))}' if extension and extension.strip('0') else ''
        delivery = self.delivery_service.dispatch_preview(db, challenge_type='otp', customer_phone=customer_phone, challenge_id=challenge.id, payload_preview=f'OTP:{challenge.code}{ext_suffix}')
        return {
            'ok': True,
            'customer_phone': customer_phone,
            'onboarding_state': session.current_state,
            'otp_preview': '****',  # masked for security — code must not reach the frontend
            'expires_in_minutes': self.challenge_service.OTP_MINUTES,
            'next_step': 'OTP prepared and logged in delivery abstraction layer.',
            'challenge_id': challenge.id,
            'delivery_status': delivery.status,
            'rate_limit_remaining_hint': max(0, max_allowed - (current + 1)),
        }

    def verify_otp(self, db: Session, customer_phone: str, code: str):
        return self.challenge_service.verify_otp(db, customer_phone=customer_phone, code=code)

    def consume_magic_link(self, db: Session, token: str):
        return self.challenge_service.consume_magic_link(db, token)

    def login_security_monitoring_summary(self, db: Session, customer_phone: str | None = None):
        challenges_q = db.query(LoginChallenge)
        deliveries_q = db.query(LoginDeliveryAttempt)
        events_q = db.query(__import__('app.models.rate_limit_event', fromlist=['RateLimitEvent']).RateLimitEvent)
        if customer_phone:
            challenges_q = challenges_q.filter(LoginChallenge.customer_phone == customer_phone)
            deliveries_q = deliveries_q.filter(LoginDeliveryAttempt.customer_phone == customer_phone)
            events_q = events_q.filter(__import__('app.models.rate_limit_event', fromlist=['RateLimitEvent']).RateLimitEvent.key.contains(customer_phone))
        return {
            'customer_phone': customer_phone,
            'total_challenges': challenges_q.count(),
            'active_challenges': challenges_q.filter(LoginChallenge.is_active == True, LoginChallenge.consumed_at.is_(None)).count(),
            'total_deliveries': deliveries_q.count(),
            'rate_limited_deliveries': deliveries_q.filter(LoginDeliveryAttempt.was_rate_limited == True).count(),
            'rate_limit_events': events_q.count(),
        }
