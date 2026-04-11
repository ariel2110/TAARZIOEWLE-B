
from sqlalchemy.orm import Session
from app.models.payment_record import PaymentRecord
from app.models.business import Business
from app.models.activity_log import ActivityLog
from app.schemas.payment import PaymentCreate


class PaymentService:
    def list_payments(self, db: Session, skip: int = 0, limit: int = 100) -> list[PaymentRecord]:
        return db.query(PaymentRecord).order_by(PaymentRecord.id.desc()).offset(skip).limit(limit).all()

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

        # Admin notification
        try:
            from app.services.common.notification_service import NotificationService
            biz_name = business.name if item.business_id and (business := db.query(Business).filter(Business.id == item.business_id).first()) else 'unknown'
            NotificationService().notify(
                db,
                event='payment_confirmed',
                entity_type='payment_record',
                entity_id=item.id,
                summary=f'Payment confirmed for business_id={item.business_id} ({biz_name}), amount={item.amount}',
                extra={'business_id': str(item.business_id), 'amount': str(item.amount or '')},
            )
        except Exception:  # noqa: BLE001
            pass

        return item
