
class OnboardingTransitionService:
    ALLOWED = {
        'intake_preview': {'demo_requested', 'magic_link_requested', 'otp_requested'},
        'demo_requested': {'lead_created', 'business_created', 'customer_account_created', 'ready_for_draft'},
        'lead_created': {'business_created', 'ready_for_draft'},
        'business_created': {'customer_account_created', 'ready_for_draft'},
        'customer_account_created': {'magic_link_requested', 'otp_requested', 'ready_for_draft'},
        'magic_link_requested': {'magic_link_verified', 'ready_for_draft'},
        'otp_requested': {'otp_verified', 'ready_for_draft'},
        'magic_link_verified': {'ready_for_draft', 'portal_access_ready'},
        'otp_verified': {'ready_for_draft', 'portal_access_ready'},
        'ready_for_draft': {'portal_access_ready', 'draft_prepared'},
        'draft_prepared': {'portal_access_ready'},
        'portal_access_ready': set(),
    }

    def validate(self, previous: str | None, new: str) -> tuple[bool, str | None]:
        if not previous:
            return True, None
        allowed = self.ALLOWED.get(previous, set())
        if new in allowed or new == previous:
            return True, None
        return False, f'Invalid onboarding transition: {previous} -> {new}'
