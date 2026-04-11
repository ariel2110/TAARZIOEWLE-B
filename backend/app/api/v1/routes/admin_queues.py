
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.queue import QueueSummaryItem, QueueEntityItem, QueueActionRequest
from app.services.common.queue_service import QueueService
from app.services.leads.lead_import_service import LeadImportService
from app.services.draft_sites.draft_site_service import DraftSiteService
from app.services.payments.payment_service import PaymentService
from app.services.businesses.business_service import BusinessService
from app.services.targeting.targeting_service import TargetingService
from app.services.feedback.feedback_service import FeedbackService
from app.models.user import User

router = APIRouter(prefix='/admin/queues', tags=['admin-queues'], dependencies=[Depends(get_current_admin)])
service = QueueService()
lead_service = LeadImportService()
draft_service = DraftSiteService()
payment_service = PaymentService()
business_service = BusinessService()
targeting_service = TargetingService()
feedback_service = FeedbackService()

@router.get('/summary', response_model=list[QueueSummaryItem])
def summary(db: Session = Depends(get_db)):
    return service.summary(db)

@router.get('/{queue_type}', response_model=list[QueueEntityItem])
def queue_items(queue_type: str, db: Session = Depends(get_db)):
    return service.queue_items(db, queue_type)

@router.post('/{queue_type}/{entity_id}/action')
def queue_action(queue_type: str, entity_id: int, payload: QueueActionRequest, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    action = payload.action
    if queue_type == 'lead_review':
        if action == 'qualify_lead':
            item = lead_service.qualify(db, entity_id)
            if not item: raise HTTPException(status_code=404, detail='Lead not found')
            return {'status': 'ok', 'action': action, 'lead_id': item.id}
        if action == 'assign_campaign':
            item = lead_service.assign_campaign(db, entity_id, payload.campaign_id, payload.targeting_profile_id)
            if not item: raise HTTPException(status_code=404, detail='Lead not found')
            return {'status': 'ok', 'action': action, 'lead_id': item.id}
        if action == 'convert_to_business':
            item = lead_service.convert_to_business(db, entity_id)
            if not item: raise HTTPException(status_code=404, detail='Lead not found')
            return {'status': 'ok', 'action': action, 'business_id': item.id}
    if queue_type == 'outreach_ready':
        if action == 'assign_campaign':
            item = business_service.assign_campaign(db, entity_id, payload.campaign_id, payload.targeting_profile_id)
            if not item: raise HTTPException(status_code=404, detail='Business not found')
            return {'status': 'ok', 'action': action, 'business_id': item.id}
        if action == 'mark_outreach_sent':
            item = business_service.mark_outreach_ready(db, entity_id)
            if not item: raise HTTPException(status_code=404, detail='Business not found')
            return {'status': 'ok', 'action': action, 'business_id': item.id}
    if queue_type == 'payments':
        if action == 'confirm_payment':
            item = payment_service.confirm_payment(db, entity_id)
            if not item: raise HTTPException(status_code=404, detail='Payment not found')
            return {'status': 'ok', 'action': action, 'payment_id': item.id}
        if action == 'move_to_activation':
            payment = payment_service.confirm_payment(db, entity_id)
            if not payment or not payment.business_id: raise HTTPException(status_code=404, detail='Payment not found')
            business = business_service.move_to_activation(db, payment.business_id)
            return {'status': 'ok', 'action': action, 'business_id': business.id}
    if queue_type == 'feedback_review' and action == 'analyze_feedback':
        item = feedback_service.analyze(db, entity_id)
        if not item: raise HTTPException(status_code=404, detail='Feedback not found')
        return {'status': 'ok', 'action': action, 'feedback_id': item.id}
    if queue_type == 'expiring_drafts' and action == 'mark_outreach_ready':
        draft = draft_service.get_draft(db, entity_id)
        if not draft: raise HTTPException(status_code=404, detail='Draft not found')
        business = business_service.mark_outreach_ready(db, draft.business_id)
        return {'status': 'ok', 'action': action, 'business_id': business.id}
    raise HTTPException(status_code=400, detail=f'Unsupported action for queue {queue_type}: {action}')
