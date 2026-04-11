from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
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
