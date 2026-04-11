
Use the current V20 starter repo and continue from the existing architecture.

Focus only on:
- package metadata driven onboarding
- persisted onboarding sessions
- public/admin compare views
- magic-link foundation
- safer provisioning direction into draft preparation

Requirements:
1. Do not break current flows
2. Preserve public request-demo flow
3. Keep package metadata in the database layer, not hardcoded only in services
4. Keep onboarding states visible and auditable
5. Prepare, but do not overbuild, the future magic-link / OTP login path

Before coding:
- show affected files
- explain data flow changes
- explain any migration needs
- explain risks

After coding:
- summarize files changed
- explain what is working now
- explain what remains for the next phase
