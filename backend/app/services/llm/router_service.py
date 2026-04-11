class LLMRouterService:
    def route(self, task_type: str) -> dict:
        default_map = {
            "generate_site_copy": {"provider": "openai", "review": "anthropic"},
            "review_generated_copy": {"provider": "anthropic", "review": None},
            "enrich_business_data": {"provider": "gemini", "review": None},
            "research_external_signal": {"provider": "xai", "review": None},
        }
        return default_map.get(task_type, {"provider": "openai", "review": None})
