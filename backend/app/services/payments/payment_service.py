
from sqlalchemy.orm import Session
from app.models.payment_record import PaymentRecord
from app.models.business import Business
from app.models.activity_log import ActivityLog
from app.schemas.payment import PaymentCreate


class PaymentService:
    def list_payments(self, db: Session) -> list[PaymentRecord]:
        return db.query(PaymentRecord).order_by(PaymentRecord.id.desc()).all()

    def create_payment(self, db: Session, payload: PaymentCreate) -> PaymentRecord:
        item = PaymentRecord(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def confirm_payment(self, db: Session, payment_id: int) -> PaymentRecord | None:
        item = db.query(PaymentRecord).filter(PaymentRecord.id == payment_id).first()
        if not item:
            return None
        item.internal_status = 'confirmed'
        if item.business_id:
            business = db.query(Business).filter(Business.id == item.business_id).first()
            if business:
                business.status = 'paid'
        db.add(ActivityLog(actor_type='admin', entity_type='payment_record', entity_id=item.id, action_type='payment_confirmed', summary=f'business_id={item.business_id}'))
        db.commit(); db.refresh(item)
        return item
