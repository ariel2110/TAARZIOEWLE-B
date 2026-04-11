
from __future__ import annotations

class StatusTransitionGuardService:
    BUSINESS_ALLOWED = {
        'new': {'reviewed'},
        'reviewed': {'ready_for_draft'},
        'ready_for_draft': {'draft_created'},
        'draft_created': {'outreach_ready', 'delete_requested', 'expired'},
        'outreach_ready': {'contacted', 'delete_requested', 'expired'},
        'contacted': {'replied_positive', 'replied_negative', 'asked_human', 'delete_requested', 'expired'},
        'replied_positive': {'payment_pending'},
        'asked_human': {'payment_pending'},
        'payment_pending': {'paid'},
        'paid': {'active'},
        'active': {'paused'},
        'paused': {'active'},
    }

    APPROVAL_ALLOWED = {
        'proposed': {'under_review', 'rejected'},
        'under_review': {'approved', 'rejected'},
        'approved': {'applied'},
        'applied': {'rolled_back'},
    }

    def can_transition(self, entity: str, current: str, target: str) -> tuple[bool, str]:
        mapping = self.BUSINESS_ALLOWED if entity == 'business' else self.APPROVAL_ALLOWED if entity == 'approval' else {}
        allowed = mapping.get(current, set())
        if target in allowed:
            return True, 'allowed'
        return False, f'Transition {entity}: {current} -> {target} is not allowed by starter guard policy.'
