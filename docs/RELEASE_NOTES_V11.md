# RELEASE NOTES V11

## Focus
Customer identity, customer access, privacy, and account-to-site mapping.

## Added
- CustomerAccount model
- CustomerLoginEvent model
- Admin customer management endpoints
- Customer login by phone + unique temporary password
- Customer must_change_password flow
- Customer /me endpoint
- Customer change-password endpoint
- Customer/business/site linkage foundations
- Docs for customer identity and privacy/visibility

## Notes
This version intentionally avoids a shared default password for all customers.
Each customer receives a unique temporary password and must change it on first login.
