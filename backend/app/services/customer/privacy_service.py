class PrivacyService:
    ALLOWED_CUSTOMER_ME_FIELDS = {'customer_account_id', 'business_id', 'active_site_id', 'draft_site_id', 'phone', 'email', 'contact_name', 'must_change_password', 'package_name'}

    def customer_me_view(self, data: dict) -> dict:
        return {k: v for k, v in data.items() if k in self.ALLOWED_CUSTOMER_ME_FIELDS}
