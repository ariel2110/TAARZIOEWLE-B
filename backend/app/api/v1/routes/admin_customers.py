from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.customer_account import CustomerAccount
from app.schemas.customer_portal import CustomerCreateRequest, CustomerCreateResponse
from app.services.auth.customer_auth_service import CustomerAuthService

router = APIRouter(prefix='/admin/customers', tags=['admin-customers'])
service = CustomerAuthService()


@router.get('')
def list_customers(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    rows = db.query(CustomerAccount).order_by(CustomerAccount.id.desc()).all()
    return [
        {
            'id': r.id,
            'business_id': r.business_id,
            'phone': r.phone,
            'email': r.email,
            'contact_name': r.contact_name,
            'active_site_id': r.active_site_id,
            'draft_site_id': r.draft_site_id,
            'must_change_password': r.must_change_password,
            'is_active': r.is_active,
            'package_name': r.package_name,
        }
        for r in rows
    ]


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
