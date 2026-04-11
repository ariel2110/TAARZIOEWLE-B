
from __future__ import annotations
from app.core.config import settings


class LockoutPolicyService:
    def policy_summary(self) -> dict:
        return {
            'customer_login_window_minutes': settings.customer_login_window_minutes,
            'customer_login_max_failures': settings.customer_login_max_failures,
            'public_challenge_window_minutes': settings.public_challenge_window_minutes,
            'public_challenge_max_per_window': settings.public_challenge_max_per_window,
            'lockout_note': 'Starter policy: repeated failures should move from watch to review/escalation before true hard lockout is enforced.',
            'escalation_levels': ['watch', 'review', 'restricted'],
        }
