Use the existing v9 starter repository and strengthen the Feedback Intelligence layer.

Goals:
- make feedback available near important objects (draft sites, outreach messages, CEO reports, recommendations)
- support 3 quick options and open natural-language feedback
- analyze feedback into category, scope, and suggested action
- surface feedback in a dedicated admin page and relevant queues
- allow the CEO/feedback layer to suggest whether feedback should apply to one item, a category, a campaign, or a broader system preference

Requirements:
- preserve current architecture
- keep logic in services
- keep important changes approval-gated
- do not silently auto-apply broad changes
- connect feedback to recommendations or approval items when relevant

Before coding:
1. show affected models/services/routes/pages
2. explain scope and safety rules
3. explain how feedback becomes insight or approval candidates

After implementation:
1. summarize files changed
2. explain what to test
3. explain what remains for deeper feedback intelligence later
