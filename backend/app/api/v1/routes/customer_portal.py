from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.api.deps import get_current_customer
from app.models.customer_account import CustomerAccount
from app.schemas.customer_portal import (
    CustomerLoginRequest,
    CustomerLoginResponse,
    CustomerMeResponse,
    CustomerChangePasswordRequest,
)
from app.services.auth.customer_auth_service import CustomerAuthService
from app.schemas.customer_portal_v12 import CustomerOverviewResponse, CustomerBasicEditCreate, CustomerChangeRequestCreate, CustomerSupportCreate
from app.services.customer.customer_portal_service import CustomerPortalService

portal_service = CustomerPortalService()

router = APIRouter(prefix='/customer', tags=['customer-portal'])
service = CustomerAuthService()


@router.post('/login', response_model=CustomerLoginResponse)
def customer_login(payload: CustomerLoginRequest, request: Request, db: Session = Depends(get_db)):
    account = service.authenticate_customer(
        db=db,
        phone=payload.phone,
        password=payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent'),
    )
    if not account:
        raise HTTPException(status_code=401, detail='Invalid phone or password')
    return CustomerLoginResponse(
        access_token=service.create_customer_access_token(account),
        customer_account_id=account.id,
        business_id=account.business_id,
        must_change_password=account.must_change_password,
    )


@router.get('/me', response_model=CustomerMeResponse)
def customer_me(account: CustomerAccount = Depends(get_current_customer)):
    return CustomerMeResponse(
        customer_account_id=account.id,
        business_id=account.business_id,
        active_site_id=account.active_site_id,
        draft_site_id=account.draft_site_id,
        phone=account.phone,
        email=account.email,
        contact_name=account.contact_name,
        must_change_password=account.must_change_password,
        package_name=account.package_name,
    )


@router.post('/change-password')
def change_password(payload: CustomerChangePasswordRequest, db: Session = Depends(get_db), account: CustomerAccount = Depends(get_current_customer)):
    try:
        updated = service.change_password(db=db, account=account, current_password=payload.current_password, new_password=payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {'ok': True, 'customer_account_id': updated.id, 'must_change_password': updated.must_change_password}


@router.get('/overview', response_model=CustomerOverviewResponse)
def customer_overview(db: Session = Depends(get_db), account: CustomerAccount = Depends(get_current_customer)):
    return portal_service.overview(db, account)


@router.get('/edit-submissions')
def customer_edit_submissions(db: Session = Depends(get_db), account: CustomerAccount = Depends(get_current_customer)):
    return portal_service.list_edit_submissions(db, account)


@router.post('/edit-submissions')
def customer_submit_basic_edit(payload: CustomerBasicEditCreate, db: Session = Depends(get_db), account: CustomerAccount = Depends(get_current_customer)):
    try:
        item = portal_service.submit_basic_edit(db, account, payload.field_key, payload.new_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {'id': item.id, 'status': item.status, 'field_key': item.field_key}


@router.get('/change-requests')
def customer_change_requests(db: Session = Depends(get_db), account: CustomerAccount = Depends(get_current_customer)):
    return portal_service.list_change_requests(db, account)


@router.post('/change-requests')
def customer_create_change_request(payload: CustomerChangeRequestCreate, db: Session = Depends(get_db), account: CustomerAccount = Depends(get_current_customer)):
    item = portal_service.create_change_request(db, account, payload.request_type, payload.title, payload.description)
    return {'id': item.id, 'status': item.status, 'title': item.title}


@router.get('/support')
def customer_support_messages(db: Session = Depends(get_db), account: CustomerAccount = Depends(get_current_customer)):
    return portal_service.list_support_messages(db, account)


@router.post('/support')
def customer_create_support(payload: CustomerSupportCreate, db: Session = Depends(get_db), account: CustomerAccount = Depends(get_current_customer)):
    item = portal_service.create_support_message(db, account, payload.subject, payload.message)
    return {'id': item.id, 'status': item.status, 'subject': item.subject}


@router.get('/timeline')
def customer_timeline(db: Session = Depends(get_db), account: CustomerAccount = Depends(get_current_customer)):
    return portal_service.timeline(db, account)


@router.get('/permissions')
def customer_permissions(db: Session = Depends(get_db), account: CustomerAccount = Depends(get_current_customer)):
    from app.services.customer.package_permission_service import PackagePermissionService
    return {
        'package_name': account.package_name,
        'permissions': PackagePermissionService().list_for_package(db, account.package_name or 'Demo')
    }

@router.get('/billing')
def customer_billing(account: CustomerAccount = Depends(get_current_customer)):
    return {
        'package_name': account.package_name,
        'billing_visibility': 'starter',
        'note': 'Starter billing visibility only. Full billing center is not enabled in this repo stage.'
    }


# ── AI Site Editor ────────────────────────────────────────────────────────────

class AiEditRequest(BaseModel):
    message: str          # customer's natural-language instruction
    section: str          # which section to edit  e.g. 'hero_title', 'about_text'
    current_value: str | None = None  # existing content of that section


class AiEditResponse(BaseModel):
    suggestion: str       # AI-generated new content
    section: str
    explanation: str      # short explanation of what it changed


class ApplyAiEditRequest(BaseModel):
    section: str
    new_value: str
    ai_suggestion: str | None = None  # store original AI suggestion for audit


EDITABLE_SECTIONS = {
    'hero_title':    'כותרת ראשית',
    'about_text':    'טקסט "אודות"',
    'site_title':    'שם האתר',
    'contact_phone': 'טלפון ליצירת קשר',
    'facebook_url':  'קישור לפייסבוק',
    'instagram_url': 'קישור לאינסטגרם',
    'tiktok_url':    'קישור לטיקטוק',
    'address':       'כתובת',
}


@router.post('/ai-edit', response_model=AiEditResponse)
def customer_ai_edit(
    payload: AiEditRequest,
    db: Session = Depends(get_db),
    account: CustomerAccount = Depends(get_current_customer),
) -> AiEditResponse:
    """Generate an AI suggestion for a site section edit based on the customer's instruction."""
    from app.services.llm.router_service import LLMRouterService
    from app.models.business import Business

    section = payload.section
    if section not in EDITABLE_SECTIONS:
        raise HTTPException(status_code=400, detail=f'Section "{section}" is not editable')

    business = db.query(Business).filter(Business.id == account.business_id).first()
    biz_name = business.name if business else 'העסק'
    biz_category = business.category if business else ''
    section_label = EDITABLE_SECTIONS[section]

    system_prompt = (
        "אתה עורך תוכן מקצועי לאתרי אינטרנט לעסקים קטנים בישראל. "
        "תפקידך הוא לשפר ולערוך טקסטים לאתרים בהתאם לבקשות הלקוח. "
        "ענה תמיד בעברית. החזר תשובה בפורמט JSON בלבד:\n"
        "{\"suggestion\": \"...\", \"explanation\": \"...\"}\n"
        "suggestion — הטקסט החדש המוכן לפרסום. explanation — משפט קצר המסביר מה שינית."
    )

    current_val_note = f'הערך הנוכחי: "{payload.current_value}"' if payload.current_value else 'אין ערך קיים'
    user_prompt = (
        f"שם העסק: {biz_name}\n"
        f"קטגוריה: {biz_category}\n"
        f"חלק באתר שצריך לשנות: {section_label}\n"
        f"{current_val_note}\n\n"
        f"בקשת הלקוח: {payload.message}\n\n"
        "צור תוכן חדש לחלק זה. החזר JSON בלבד."
    )

    llm = LLMRouterService()
    raw = llm.call_tracked('generate_site_copy', user_prompt, system=system_prompt, max_tokens=600, json_mode=True, business_id=account.business_id, stage="ai_edit")

    if not raw:
        raise HTTPException(status_code=503, detail='שירות ה-AI אינו זמין כרגע. נסה שוב עוד רגע.')

    import json
    try:
        data = json.loads(raw)
        suggestion = str(data.get('suggestion', '') or '').strip()
        explanation = str(data.get('explanation', '') or '').strip()
    except (json.JSONDecodeError, AttributeError):
        # Fallback: treat full response as suggestion
        suggestion = raw.strip()
        explanation = 'הוצע טקסט חדש על ידי AI'

    if not suggestion:
        raise HTTPException(status_code=503, detail='ה-AI לא הצליח לייצר הצעה. נסה לנסח את הבקשה מחדש.')

    return AiEditResponse(suggestion=suggestion, section=section, explanation=explanation)


@router.post('/apply-ai-edit')
def customer_apply_ai_edit(
    payload: ApplyAiEditRequest,
    db: Session = Depends(get_db),
    account: CustomerAccount = Depends(get_current_customer),
) -> dict:
    """Save an approved AI edit as a change request (pending admin review)."""
    from app.models.change_request import ChangeRequest
    from app.models.activity_log import ActivityLog

    section = payload.section
    if section not in EDITABLE_SECTIONS:
        raise HTTPException(status_code=400, detail=f'Section "{section}" is not editable')

    section_label = EDITABLE_SECTIONS[section]
    note = f'[AI עריכה] הצעה מקורית: {payload.ai_suggestion[:200]}' if payload.ai_suggestion else None

    item = ChangeRequest(
        customer_account_id=account.id,
        business_id=account.business_id,
        request_type='ai_edit',
        title=f'עדכון {section_label}',
        description=(
            f'שדה: {section}\n'
            f'ערך חדש: {payload.new_value}\n'
            + (f'הערה: {note}' if note else '')
        ),
    )
    db.add(item)
    db.add(ActivityLog(
        actor_type='customer',
        actor_id=account.id,
        business_id=account.business_id,
        action_type='customer_ai_edit_applied',
        action_payload_json={'section': section, 'value_length': len(payload.new_value)},
    ))
    db.commit()
    db.refresh(item)
    return {'ok': True, 'change_request_id': item.id, 'status': item.status}


@router.get('/site-content')
def customer_site_content(
    db: Session = Depends(get_db),
    account: CustomerAccount = Depends(get_current_customer),
) -> dict:
    """Return the editable content of the customer's active/draft site."""
    from app.models.draft_site import DraftSite
    from app.models.business import Business

    business = db.query(Business).filter(Business.id == account.business_id).first()
    draft = db.query(DraftSite).filter(DraftSite.business_id == account.business_id).order_by(DraftSite.id.desc()).first()

    return {
        'editable_sections': EDITABLE_SECTIONS,
        'current_values': {
            'hero_title':    getattr(draft, 'hero_title', None) if draft else None,
            'about_text':    getattr(draft, 'about_text', None) if draft else None,
            'site_title':    getattr(draft, 'site_title', None) if draft else None,
            'contact_phone': business.phone if business else None,
            'facebook_url':  business.facebook_url if business else None,
            'instagram_url': business.instagram_url if business else None,
            'tiktok_url':    business.tiktok_url if business else None,
            'address':       business.address if business else None,
        },
        'site_preview_url': draft.preview_url if draft else None,
        'site_status':      draft.status if draft else None,
    }
