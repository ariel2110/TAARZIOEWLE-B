
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.payment import PaymentCreate, PaymentRead
from app.schemas.business import BusinessRead
from app.services.payments.payment_service import PaymentService
from app.services.businesses.business_service import BusinessService
from app.models.user import User

router = APIRouter(prefix='/admin/payments', tags=['admin-payments'])
service = PaymentService()
business_service = BusinessService()


@router.get('', response_model=list[PaymentRead])
def list_payments(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.list_payments(db, skip=skip, limit=limit)


@router.post('', response_model=PaymentRead)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create_payment(db, payload)


@router.post('/{payment_id}/confirm', response_model=PaymentRead)
def confirm_payment(payment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.confirm_payment(db, payment_id)
    if not item:
        raise HTTPException(status_code=404, detail='Payment not found')
    return item


@router.post('/{payment_id}/move-to-activation', response_model=BusinessRead)
def move_to_activation(payment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    payment = service.confirm_payment(db, payment_id)
    if not payment or not payment.business_id:
        raise HTTPException(status_code=404, detail='Payment/business not found')
    business = business_service.move_to_activation(db, payment.business_id)
    if not business:
        raise HTTPException(status_code=404, detail='Business not found')
    return business
