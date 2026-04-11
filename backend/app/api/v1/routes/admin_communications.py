
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.communication import WhatsAppLaunchRequest, WhatsAppLaunchResponse, WhatsAppBusinessLaunchRequest, MarkOutreachSentRequest, RescheduleFollowupRequest
from app.services.communications.whatsapp_launcher_service import WhatsAppLauncherService
from app.services.communications.outreach_service import OutreachService
from app.models.user import User

router = APIRouter(prefix='/admin/communications', tags=['admin-communications'])
launcher = WhatsAppLauncherService()
outreach_service = OutreachService()


@router.post('/whatsapp-launch', response_model=WhatsAppLaunchResponse)
def whatsapp_launch(payload: WhatsAppLaunchRequest, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return WhatsAppLaunchResponse(**launcher.build_link(payload.phone, payload.message))


@router.post('/whatsapp-for-business', response_model=WhatsAppLaunchResponse)
def whatsapp_for_business(payload: WhatsAppBusinessLaunchRequest, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    message = outreach_service.build_business_message(db, payload.business_id, payload.draft_site_id, payload.message_template_key)
    if not message:
        raise HTTPException(status_code=404, detail='Business not found')
    if not message.outbound_target:
        raise HTTPException(status_code=400, detail='Business has no phone number')
    link = launcher.build_link(message.outbound_target, message.content)
    return WhatsAppLaunchResponse(**link, outreach_id=message.id)


@router.post('/outreach/{outreach_id}/mark-sent')
def mark_sent(outreach_id: int, payload: MarkOutreachSentRequest, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = outreach_service.mark_sent(db, outreach_id, payload.status)
    if not item:
        raise HTTPException(status_code=404, detail='Outreach not found')
    return {'status': item.status, 'id': item.id}


@router.post('/outreach/{outreach_id}/reschedule-followup')
def reschedule_followup(outreach_id: int, payload: RescheduleFollowupRequest, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = outreach_service.reschedule_followup(db, outreach_id, payload.note)
    if not item:
        raise HTTPException(status_code=404, detail='Outreach not found')
    return {'status': item.status, 'id': item.id}
