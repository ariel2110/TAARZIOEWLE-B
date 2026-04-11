class CEOBrainService:
    def build_summary(self, metrics: dict) -> dict:
        health = "healthy" if metrics.get("payments_pending", 0) < 5 else "warning"
        return {
            "executive_summary": "The platform is in operational starter mode. Keep lead flow moving, generate strong draft previews, and clear payment blockers quickly.",
            "health": health,
            "recommended_actions": [
                "Review high-score leads first",
                "Generate missing draft previews for outreach-ready businesses",
                "Clear pending payment confirmations",
            ],
            "metrics": metrics,
        }
