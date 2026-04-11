# LLM TASK MATRIX

## Recommended routing
- OpenAI: generation, structured outputs, operational suggestions
- Anthropic: critique, review, summarization
- Gemini: factual and geo-aware enrichment
- xAI: optional fresh research / secondary signal

## Rule
Business services must not depend directly on provider SDKs.
All LLM calls should go through router abstractions.
