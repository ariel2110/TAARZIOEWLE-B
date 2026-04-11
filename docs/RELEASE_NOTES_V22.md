# RELEASE NOTES V22

## Focus
- rate limiting and anti-abuse foundations
- login delivery abstraction for OTP/magic-link
- package-aware public login gating
- improved admin visibility for onboarding/login flows
- hardening customer access flow

## Added
- RateLimitEvent model
- LoginDeliveryAttempt model
- RateLimitService
- LoginDeliveryService
- rate-limited public magic-link/OTP request flow
- admin endpoints for login deliveries and rate limit events
- customer password login throttling foundation

## Notes
This is still a starter implementation.
External OTP/SMS/email delivery is not connected yet.
