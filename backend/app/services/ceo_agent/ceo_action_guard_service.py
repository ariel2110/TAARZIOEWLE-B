SAFE_ACTIONS = {
    "create_internal_planner_task",
    "reprioritize_internal_alert",
    "mark_followup_due",
    "queue_recommendation_for_review",
}


class CEOActionGuardService:
    def can_auto_execute(self, action_key: str) -> bool:
        return action_key in SAFE_ACTIONS
