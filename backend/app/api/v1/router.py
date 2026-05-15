from app.api.v1.routes.public_intake import router as public_intake_router
from app.api.v1.routes import public_portal
from app.api.v1.routes.public_inbound import router as public_inbound_router
from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.admin_businesses import router as admin_business_router
from app.api.v1.routes.admin_draft_sites import router as admin_draft_router
from app.api.v1.routes.admin_ceo import router as admin_ceo_router
from app.api.v1.routes.admin_leads import router as admin_leads_router
from app.api.v1.routes.admin_payments import router as admin_payments_router
from app.api.v1.routes.admin_analytics import router as admin_analytics_router
from app.api.v1.routes.admin_insights import router as admin_insights_router
from app.api.v1.routes.admin_targeting import router as admin_targeting_router
from app.api.v1.routes.admin_queues import router as admin_queues_router
from app.api.v1.routes.admin_communications import router as admin_communications_router
from app.api.v1.routes.admin_approvals import router as admin_approvals_router
from app.api.v1.routes.admin_feedback import router as admin_feedback_router
from app.api.v1.routes.admin_customers import router as admin_customers_router
from app.api.v1.routes.admin_customer_ops import router as admin_customer_ops_router
from app.api.v1.routes.admin_public_flow import router as admin_public_flow_router
from app.api.v1.routes.customer_portal import router as customer_portal_router
from app.api.v1.routes.admin_security import router as admin_security_router
from app.api.v1.routes.admin_workflows import router as admin_workflows_router
from app.api.v1.routes.admin_enrich import router as admin_enrich_router
from app.api.v1.routes.admin_demos import router as admin_demos_router
from app.api.v1.routes.public_demos import router as public_demos_router
from app.api.v1.routes.public_sites import router as public_sites_router
from app.api.v1.routes.admin_notifications import router as admin_notifications_router
from app.api.v1.routes.webhooks_whatsapp import router as webhooks_whatsapp_router
from app.api.v1.routes.admin_users import router as admin_users_router
from app.api.v1.routes.internal_whatsapp import router as internal_whatsapp_router
from app.api.v1.routes.admin_tasks import router as admin_tasks_router
from app.api.v1.routes.admin_whatsapp import router as admin_whatsapp_router
from app.api.v1.routes.webhooks_morning import router as webhooks_morning_router
from app.api.v1.routes.admin_api_keys import router as admin_api_keys_router
from app.api.v1.routes.admin_social import router as admin_social_router

from app.api.v1.routes.admin_domain_approvals import router as admin_domain_approvals_router
from app.api.v1.routes.admin_agent_connections import router as admin_agent_connections_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(admin_business_router)
api_router.include_router(admin_draft_router)
api_router.include_router(admin_ceo_router)
api_router.include_router(admin_leads_router)
api_router.include_router(admin_payments_router)
api_router.include_router(admin_analytics_router)
api_router.include_router(admin_insights_router)
api_router.include_router(admin_targeting_router)
api_router.include_router(admin_queues_router)
api_router.include_router(admin_communications_router)
api_router.include_router(admin_approvals_router)

api_router.include_router(admin_feedback_router)

api_router.include_router(admin_customers_router)
api_router.include_router(admin_customer_ops_router)
api_router.include_router(admin_public_flow_router)
api_router.include_router(admin_security_router)
api_router.include_router(admin_workflows_router)
api_router.include_router(admin_enrich_router)
api_router.include_router(admin_demos_router)
api_router.include_router(public_demos_router)
api_router.include_router(public_sites_router)
api_router.include_router(customer_portal_router)
api_router.include_router(admin_notifications_router)
api_router.include_router(webhooks_whatsapp_router)
api_router.include_router(admin_users_router)
api_router.include_router(admin_tasks_router)
api_router.include_router(public_inbound_router)

api_router.include_router(public_intake_router)
api_router.include_router(public_portal.router)
api_router.include_router(webhooks_morning_router)
api_router.include_router(internal_whatsapp_router)
api_router.include_router(admin_whatsapp_router)
api_router.include_router(admin_api_keys_router)
api_router.include_router(admin_social_router)
api_router.include_router(admin_domain_approvals_router)
api_router.include_router(admin_agent_connections_router)
from app.api.v1.routes.public_mall import router as public_mall_router
api_router.include_router(public_mall_router)

from app.api.v1.routes.public_site_orders import router as public_site_orders_router
api_router.include_router(public_site_orders_router)
