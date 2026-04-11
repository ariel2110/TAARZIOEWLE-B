
Use v16 as the baseline.

Focus:
- harden the public onboarding flow
- improve request-demo provisioning
- add deduplication checks before creating new business/customer
- improve monthly demo limit enforcement
- improve customer account provisioning rules
- improve public homepage UX around readiness vs request-demo

Do not break:
- customer identity/access model
- privacy boundaries
- admin/customer separation
- existing public home language toggle behavior

Before coding:
1. explain provisioning flow
2. list touched models/services/routes/pages
3. explain risks

After implementation:
1. summarize files changed
2. explain what to test
3. suggest the next safest improvement
