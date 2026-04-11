
# OTP / MAGIC LINK DIRECTION

## Goal
Future customer authentication should support safer low-friction methods such as:
- phone OTP
- magic link by email

## Recommended sequence
1. Current: phone + unique temporary password
2. Next: add OTP login support
3. Later: add magic link for customers who prefer email-based access

## Rules
- temporary shared passwords are never allowed
- first-login password change stays supported
- OTP/magic-link should still respect customer ↔ business ↔ site ownership mapping
