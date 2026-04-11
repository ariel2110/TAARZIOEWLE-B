
# LOGIN CHALLENGE FLOW SPEC

## Purpose
Define the low-friction login challenge flow used for customer access from public/demo onboarding.

## Supported challenge types
- magic_link
- otp

## Current starter behavior
- requests create a challenge record
- previous active challenges of same type are deactivated
- a token or OTP preview is returned for development
- consume/verify endpoints complete the challenge and may return a customer access token

## Future enhancements
- real SMS / email delivery
- rate limiting
- challenge attempt counters
- lockout rules
- stronger audit / device metadata
