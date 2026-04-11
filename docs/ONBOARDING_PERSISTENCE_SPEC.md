# ONBOARDING PERSISTENCE SPEC

## Goal
Persist public request-demo attempts so the system can:
- count monthly demo usage more accurately
- reuse previous records
- expose history to admin/CEO layers
- reduce duplicate provisioning

## Current V18 Support
- Demo request log per request
- Stores phone, business name, city, category, linked lead/business/customer when available
- Stores onboarding_state and dedup_reason

## Next Steps
- full state machine persistence
- richer attempt history
- OTP/magic-link states
- package-aware demo enforcement
