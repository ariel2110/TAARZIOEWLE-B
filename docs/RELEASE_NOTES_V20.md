
# RELEASE NOTES V20

## Focus
V20 strengthens the public/demo onboarding flow with:
- package metadata from the database
- persisted onboarding sessions
- public/admin compare views
- magic-link foundation
- stronger provisioning direction toward draft preparation

## Main additions
- `PackagePlan` model
- `OnboardingSession` model
- `/api/v1/public/packages`
- `/api/v1/public/request-magic-link`
- `/api/v1/public/demo-compare`
- `/api/v1/admin/public-flow/packages`
- `/api/v1/admin/public-flow/demo-compare`
- `/api/v1/admin/public-flow/onboarding-sessions`

## Why this matters
The public/demo flow is no longer driven only by hardcoded package limits and lightweight logs.
It now starts to behave more like a real onboarding system with:
- state persistence
- package metadata
- compare views
- customer-access direction

## Still intentionally not complete
- no real OTP delivery yet
- no real emailed magic-link yet
- onboarding transitions are still relatively lightweight
- package logic is still metadata-driven, not subscription-driven
