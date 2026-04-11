
# MAGIC LINK FOUNDATION SPEC

## Purpose
Prepare a safer future login flow for customers using magic links.

## V20 scope
V20 does not yet deliver or validate magic links end-to-end.
It adds the foundation:
- onboarding session can store a token
- token expiration time is tracked
- a public endpoint can request a magic-link token preview

## Why this matters
The current customer login flow is still phone + temporary password.
Magic-link or OTP login is a safer and more user-friendly direction for later phases.

## Future steps
- email/SMS delivery integration
- token verification endpoint
- single-use invalidation
- audit logs for token use
