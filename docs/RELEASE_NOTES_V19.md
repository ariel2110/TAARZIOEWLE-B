
# RELEASE NOTES V19

## Focus
- package-aware demo limits
- stronger public onboarding persistence
- provisioning decision logs
- better admin/public status visibility
- OTP/magic-link direction documented

## Added
- `ProvisioningDecisionLog` model
- package-aware demo limit calculation based on package name
- public status summary endpoint
- admin provisioning decisions endpoint
- richer demo request log fields: package snapshot, previous state, next action

## Notes
This version still keeps the auth/login flow simple. OTP and magic-link remain a planned direction, not a completed production flow.
