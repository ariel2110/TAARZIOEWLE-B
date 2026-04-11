
Use the current v21 codebase and deepen these areas without breaking architecture:

1. OTP / magic-link flow
- improve challenge delivery abstraction
- add rate limiting hooks
- add expiry and invalidation rules
- make admin/customer visibility clear

2. State transition guards
- expand guarded transitions
- centralize transition validation
- avoid invalid onboarding jumps

3. Package metadata linkage
- use package metadata more consistently in public onboarding and customer access decisions

4. Public/admin compare views
- improve compare visibility for onboarding, requests, sessions, and challenges

5. Draft-prep automation
- turn strong onboarding results into clearer draft-prep readiness workflows

Before coding:
1. explain affected models/services/routes/pages
2. list risks
3. explain how you will preserve backward compatibility
