Use v22 as the current working base.
Focus on:
- deepening rate limiting and anti-abuse
- replacing preview delivery with a provider abstraction implementation
- improving customer access hardening
- enriching public/admin compare views around onboarding and login challenges
- connecting package metadata to more real gating behavior

Before coding:
1. review current v22 architecture
2. show risky areas still missing
3. propose the next hardening steps
Then implement incrementally without breaking current behavior.
