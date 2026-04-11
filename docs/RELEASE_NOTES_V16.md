
# RELEASE NOTES V16

## Focus
- Public onboarding flow connected to real provisioning steps
- Request-demo flow creates lead + business + optional customer account
- Public app supports request demo after readiness preview
- Monthly demo limit is enforced through public service logic

## Main additions
- `/public/request-demo` endpoint
- `PublicRequestDemoRequest/Response` schemas
- provisioning logic in `PublicPortalService`
- frontend-public request-demo action
- next-step messaging for onboarding

## Notes
This is still starter-grade provisioning. It is intentionally simple and should be hardened later with:
- deduplication checks
- stronger monthly limit counting policy
- OTP/magic link
- deeper package enforcement
- richer onboarding state machine
