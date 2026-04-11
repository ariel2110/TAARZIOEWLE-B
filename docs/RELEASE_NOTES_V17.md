
# RELEASE NOTES V17

## Focus
v17 strengthens the public onboarding and request-demo flow with safer provisioning rules, basic deduplication, and a clearer onboarding lifecycle.

## What was added
- request-demo dedup logic for existing leads/businesses
- safer reuse of existing customer account when phone already exists
- onboarding state returned from public provisioning flow
- new docs for onboarding state machine and provisioning rules
- new prompt for continuing v17 hardening in VS Code

## Why this matters
This reduces accidental duplicate records and makes the public flow more realistic for real use.

## Still future work
- stronger fuzzy dedup
- real monthly demo accounting windows
- OTP / magic-link
- onboarding state machine persisted in DB
- package-aware provisioning rules
