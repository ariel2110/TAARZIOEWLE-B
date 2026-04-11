
# ONBOARDING STATE MACHINE

## Purpose
Define the public-to-customer onboarding states so the system can explain where a prospect/customer is in the flow.

## Suggested states
- intake_started
- readiness_checked
- demo_requested
- existing_record_reused
- partially_reused
- customer_account_created
- waiting_for_review
- draft_preparation_ready
- draft_generated
- customer_followup_ready

## Notes
- In v17 the state is returned from provisioning logic, but not yet stored as a dedicated state machine entity.
- Future versions should persist transitions and expose timeline/history.
