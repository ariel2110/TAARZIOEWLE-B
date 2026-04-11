
import app.models
from sqlalchemy.orm import Session
from app.services.auth.customer_auth_service import CustomerAuthService

from app.models.user import User
from app.models.lead_record import LeadRecord
from app.models.business import Business
from app.models.draft_site import DraftSite
from app.models.payment_record import PaymentRecord
from app.models.approval_item import ApprovalItem
from app.models.targeting_profile import TargetingProfile
from app.models.campaign import Campaign
from app.models.feedback_item import FeedbackItem
from app.models.generated_insight import GeneratedInsight
from app.models.package_plan import PackagePlan
from app.models.onboarding_session import OnboardingSession


def seed_demo_data(db: Session):
    if db.query(User).count() > 0:
        return

    admin = User(email='admin@example.com', full_name='Admin User', role='admin')
    db.add(admin)

    package_plans = [
        PackagePlan(name='Demo', monthly_demo_limit=2, description='Public demo access', is_default=True, is_active=True, customer_portal_enabled=True, requires_contact_verification=False, billing_mode='demo'),
        PackagePlan(name='Starter', monthly_demo_limit=2, description='Starter access', is_default=False, is_active=True, customer_portal_enabled=True, requires_contact_verification=True, billing_mode='subscription'),
        PackagePlan(name='Business', monthly_demo_limit=4, description='Business access', is_default=False, is_active=True, customer_portal_enabled=True, requires_contact_verification=True, billing_mode='subscription'),
        PackagePlan(name='Pro', monthly_demo_limit=6, description='Pro access', is_default=False, is_active=True, customer_portal_enabled=True, requires_contact_verification=True, billing_mode='subscription'),
    ]
    db.add_all(package_plans)

    profile1 = TargetingProfile(name='Beauty Gush Dan 8km', city='Ramat Gan', radius_km=8, category_list=['beauty'], min_reviews=10, min_rating=4.0, requires_no_website=True, requires_phone=True, score_threshold=50, active=True)
    profile2 = TargetingProfile(name='Garages Petah Tikva 10km', city='Petah Tikva', radius_km=10, category_list=['garages'], min_reviews=5, min_rating=3.5, requires_no_website=True, requires_phone=True, score_threshold=45, active=True)
    db.add_all([profile1, profile2])
    db.flush()

    campaign1 = Campaign(name='Beauty Gush Dan Week 1', targeting_profile_id=profile1.id, status='running', goals_json={'drafts': 10, 'outreach': 10})
    campaign2 = Campaign(name='Garages Petah Tikva Pilot', targeting_profile_id=profile2.id, status='draft', goals_json={'drafts': 5, 'outreach': 5})
    db.add_all([campaign1, campaign2])
    db.flush()

    leads = [
        LeadRecord(imported_name='Noa Beauty Studio', city='Ramat Gan', category='beauty', phone='052-1111111', address='Herzl 10', score=78, status='needs_review', campaign_id=campaign1.id, targeting_profile_id=profile1.id),
        LeadRecord(imported_name='Shai Garage', city='Petah Tikva', category='garages', phone='053-2222222', address='Jabotinsky 44', score=66, status='qualified', campaign_id=campaign2.id, targeting_profile_id=profile2.id),
        LeadRecord(imported_name='Clean Laundry', city='Tel Aviv', category='laundries', phone='054-3333333', address='Dizengoff 80', score=57, status='imported'),
    ]
    db.add_all(leads)
    db.flush()

    businesses = [
        Business(name='Noa Beauty Studio', city='Ramat Gan', category='beauty', phone='052-1111111', address='Herzl 10', status='outreach_ready', lead_id=leads[0].id, campaign_id=campaign1.id, targeting_profile_id=profile1.id),
        Business(name='Shai Garage', city='Petah Tikva', category='garages', phone='053-2222222', address='Jabotinsky 44', status='draft_created', lead_id=leads[1].id, campaign_id=campaign2.id, targeting_profile_id=profile2.id),
    ]
    db.add_all(businesses)
    db.flush()

    drafts = [
        DraftSite(business_id=businesses[0].id, site_title='Noa Beauty Draft', status='published_preview', preview_url='/static/drafts/draft_1.html', primary_color='#ec4899', is_demo=True, noindex=True, hero_title='Noa Beauty Studio', about_text='Premium beauty services in Ramat Gan.'),
        DraftSite(business_id=businesses[1].id, site_title='Shai Garage Draft', status='pending_payment', preview_url='/static/drafts/draft_2.html', primary_color='#2563eb', is_demo=True, noindex=True, hero_title='Shai Garage', about_text='Trusted local garage in Petah Tikva.'),
    ]
    db.add_all(drafts)

    payments = [
        PaymentRecord(business_id=businesses[1].id, amount=49, provider='manual', internal_status='pending', external_reference='PAY-001'),
    ]
    db.add_all(payments)

    approvals = [
        ApprovalItem(approval_type='template_change', title='Update beauty hero copy default', summary='Improve trust tone for beauty sites', status='under_review', approval_required=True, rationale='Beauty drafts with stronger trust language performed better.', evidence_json={'sample_size': 12, 'improvement': '+14% reply rate'}, before_json={'hero_style': 'generic'}, after_json={'hero_style': 'trust_first'}, confidence_score=0.82, payload_json={'scope': 'beauty'}),
        ApprovalItem(approval_type='lead_scoring_change', title='Increase weight for review count in garages', summary='Garages with 10+ reviews show stronger conversion', status='proposed', approval_required=True, rationale='Recent garages cohort converted better above 10 reviews.', evidence_json={'sample_size': 7, 'payment_conversion': 'higher'}, before_json={'review_weight': 10}, after_json={'review_weight': 16}, confidence_score=0.74, payload_json={'scope': 'garages'}),
    ]
    db.add_all(approvals)

    feedback = [
        FeedbackItem(target_type='draft_site', target_id=1, quick_rating='needs_improvement', open_feedback='The beauty site looks good but the headline needs more trust and local tone.', feedback_status='analyzed', analysis_category='hero_copy', suggested_scope='category_template', ceo_response='I classified this as a trust-messaging issue and suggest improving the beauty hero pattern.', action_hint='Create approval candidate', preference_candidate=True),
    ]
    db.add_all(feedback)

    insights = [
        GeneratedInsight(insight_type='campaign_signal', title='Beauty campaign is outperforming garages on reply rate', summary='Ramat Gan beauty segment is showing stronger reply behavior.', status='proposed')
    ]
    db.add_all(insights)

    onboarding = [
        OnboardingSession(customer_phone='052-1111111', business_name='Noa Beauty Studio', current_state='customer_account_created', previous_state='demo_requested', package_name='Starter', business_id=businesses[0].id, last_preview_score=78, next_action='Prepare draft and customer handoff'),
    ]
    db.add_all(onboarding)

    db.commit()


def seed_customer_access(db):
    biz = db.query(Business).first()
    if not biz:
        return None
    exists = db.query(app.models.CustomerAccount).filter(app.models.CustomerAccount.business_id == biz.id).first()
    if exists:
        return exists
    account, _temp = CustomerAuthService().create_customer_account(
        db=db,
        business_id=biz.id,
        phone=biz.phone or '0500000000',
        contact_name='Demo Customer',
        package_name='Starter'
    )
    return account
