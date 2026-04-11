# STATUS TRANSITIONS

## Summary
Important state transitions must be enforced in backend services, never ad hoc in UI.

Lifecycle groups:
- lead: imported -> normalized -> needs_review -> qualified/rejected -> converted_to_business
- business: new -> reviewed -> ready_for_draft -> draft_created -> outreach_ready -> contacted -> payment_pending -> paid -> active
- draft site: draft -> preview_ready -> published_preview -> pending_payment -> active/expired/deleted
- payment: pending -> awaiting_confirmation -> confirmed/failed/refunded
- recommendation: proposed -> under_review -> approved/rejected -> applied -> rolled_back
