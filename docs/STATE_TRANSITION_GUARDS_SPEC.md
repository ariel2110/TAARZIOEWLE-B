
# STATE TRANSITION GUARDS SPEC

This document defines guarded transitions for onboarding and related public provisioning flows.

## Goal
Prevent invalid state jumps and make onboarding transitions explicit, auditable, and easier to debug.

## Current guarded onboarding states
- intake_preview
- demo_requested
- lead_created
- business_created
- customer_account_created
- magic_link_requested
- otp_requested
- magic_link_verified
- otp_verified
- ready_for_draft
- draft_prepared
- portal_access_ready

## Notes
- Guards are implemented in a dedicated service.
- Invalid transitions should fail in backend services rather than being silently accepted.
- Future versions can expand this into a persisted full state machine with explicit transition logs.
