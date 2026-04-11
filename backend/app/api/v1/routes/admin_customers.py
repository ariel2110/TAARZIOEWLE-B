from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.customer_account import CustomerAccount
from app.models.business import Business
from app.models.draft_site import DraftSite
from app.models.payment_record import PaymentRecord
from app.schemas.customer_portal import CustomerCreateRequest, CustomerCreateResponse
from app.services.auth.customer_auth_service import CustomerAuthService

router = APIRouter(prefix='/admin/customers', tags=['admin-customers'])
service = CustomerAuthService()


def _derive_customer_status(account: CustomerAccount, db: Session) -> str:
    """Derive a human-readable Hebrew status based on account + related records."""
    if account.active_site_id:
        # Check if there is a confirmed payment
        payment = db.query(PaymentRecord).filter(
            PaymentRecord.business_id == account.business_id,
            PaymentRecord.internal_status == 'confirmed',
        ).first()
        if payment:
            return 'לקוח במנוי' if account.package_name else 'שילם — אתר פעיל'
        return 'אתר פעיל'
    if account.draft_site_id:
        draft = db.query(DraftSite).filter(DraftSite.id == account.draft_site_id).first()
        if draft:
            if draft.status == 'approved':
                return 'אישר דמו'
            if draft.status in ('published_preview', 'draft'):
                return 'דמו נשלח'
    return 'חשבון נוצר'


def _row_to_dict(r: CustomerAccount, db: Session) -> dict:
    biz = db.query(Business).filter(Business.id == r.business_id).first() if r.business_id else None
    draft = db.query(DraftSite).filter(DraftSite.id == r.draft_site_id).first() if r.draft_site_id else None
    return {
        'id': r.id,
        'business_id': r.business_id,
        'business_name': biz.name if biz else None,
        'business_city': biz.city if biz else None,
        'business_category': biz.category if biz else None,
        'phone': r.phone,
        'email': r.email,
        'contact_name': r.contact_name,
        'active_site_id': r.active_site_id,
        'draft_site_id': r.draft_site_id,
        'draft_preview_url': draft.preview_url if draft else None,
        'draft_status': draft.status if draft else None,
        'must_change_password': r.must_change_password,
        'is_active': r.is_active,
        'package_name': r.package_name,
        'customer_status': _derive_customer_status(r, db),
        'created_at': r.created_at.isoformat() if hasattr(r, 'created_at') and r.created_at else None,
    }


@router.get('')
def list_customers(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    rows = db.query(CustomerAccount).order_by(CustomerAccount.id.desc()).offset(skip).limit(limit).all()
    return [_row_to_dict(r, db) for r in rows]


@router.post('', response_model=CustomerCreateResponse)
def create_customer(payload: CustomerCreateRequest, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    existing = db.query(CustomerAccount).filter(CustomerAccount.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail='Customer phone already exists')
    account, temp_password = service.create_customer_account(
        db=db,
        business_id=payload.business_id,
        phone=payload.phone,
        email=payload.email,
        contact_name=payload.contact_name,
        draft_site_id=payload.draft_site_id,
        active_site_id=payload.active_site_id,
        package_name=payload.package_name,
    )
    return CustomerCreateResponse(
        customer_account_id=account.id,
        business_id=account.business_id,
        phone=account.phone,
        temporary_password=temp_password,
        must_change_password=account.must_change_password,
    )


@router.post('/sync-from-demos')
def sync_customers_from_demos(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """
    Auto-register all businesses that have a draft site (demo) as customer accounts,
    skipping any that already have a customer account linked.
    Returns a summary of newly created accounts.
    """
    import secrets as _secrets
    from app.core.security import hash_password

    # Find all businesses that have at least one draft site
    businesses_with_drafts = (
        db.query(Business)
        .join(DraftSite, DraftSite.business_id == Business.id)
        .distinct()
        .all()
    )

    # Get set of business_ids already registered as customers
    existing_biz_ids = {
        r.business_id
        for r in db.query(CustomerAccount.business_id).all()
        if r.business_id
    }

    created = []
    skipped = []

    for biz in businesses_with_drafts:
        if biz.id in existing_biz_ids:
            skipped.append({'business_id': biz.id, 'name': biz.name, 'reason': 'already_exists'})
            continue

        # Use business phone; if missing generate a placeholder
        phone = (biz.phone or '').strip().replace('-', '').replace(' ', '')
        if not phone:
            phone = f'biz-{biz.id}'

        # Avoid duplicate phone across accounts
        if db.query(CustomerAccount).filter(CustomerAccount.phone == phone).first():
            skipped.append({'business_id': biz.id, 'name': biz.name, 'reason': f'phone_conflict:{phone}'})
            continue

        # Pick the latest published_preview draft, fallback to any draft
        draft = (
            db.query(DraftSite)
            .filter(DraftSite.business_id == biz.id, DraftSite.status == 'published_preview')
            .order_by(DraftSite.id.desc())
            .first()
            or db.query(DraftSite)
            .filter(DraftSite.business_id == biz.id)
            .order_by(DraftSite.id.desc())
            .first()
        )

        temp_password = _secrets.token_hex(3)
        account = CustomerAccount(
            business_id=biz.id,
            phone=phone,
            email=None,
            contact_name=biz.name,
            draft_site_id=draft.id if draft else None,
            active_site_id=None,
            package_name='Demo',
            password_hash=hash_password(temp_password),
            must_change_password=True,
            is_active=True,
        )
        db.add(account)
        db.flush()
        created.append({
            'customer_account_id': account.id,
            'business_id': biz.id,
            'name': biz.name,
            'phone': phone,
            'draft_site_id': draft.id if draft else None,
            'temporary_password': temp_password,
        })

    db.commit()
    return {
        'created': len(created),
        'skipped': len(skipped),
        'details_created': created,
        'details_skipped': skipped,
    }


@router.get('/{customer_id}/permissions')
def customer_permissions_admin(customer_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    from app.models.customer_account import CustomerAccount
    from app.services.customer.package_permission_service import PackagePermissionService
    account = db.query(CustomerAccount).filter(CustomerAccount.id == customer_id).first()
    if not account:
        raise HTTPException(status_code=404, detail='Customer not found')
    return {
        'customer_account_id': account.id,
        'package_name': account.package_name,
        'permissions': PackagePermissionService().list_for_package(db, account.package_name or 'Demo')
    }
