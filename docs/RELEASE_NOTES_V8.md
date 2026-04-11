# RELEASE NOTES V8

## Focus
V8 focuses on making the product feel more operational and admin-usable:
- queue summaries and queue views
- approval actions with audit log entries
- richer CEO Console starter
- targeting console starter
- React Router based admin shell

## Backend
- added /admin/queues/summary and /admin/queues/{queue_type}
- added QueueService for work queues
- approval actions now create activity log entries
- CEO daily digest includes more operational pressure metrics

## Frontend Admin
- moved from single-page shell to simple routed admin starter
- added pages: Overview, Leads, Queues, Approvals, Targeting, CEO Console
- reusable shell and UI primitives added
- queue and approval workflows are now more visible

## Still intentionally limited
- no full Google OAuth flow
- no shadcn/tailwind full design system yet
- no campaign assignment actions from UI yet
- no full queue action execution layer
- no production-grade approval diff views yet
