# PROVISIONING AUDIT TRAIL

## Goal
Track how a public demo request became a lead, business, or customer record.

## Current V18
- DemoRequestLog captures provisioning outcome at a lightweight level
- onboarding_state explains whether records were reused or created
- dedup_reason stores the main reuse reason when applicable

## Recommended Future Expansion
- provisioning decision entity
- before/after entity references
- policy/limit reason capture
- approval-needed hooks
