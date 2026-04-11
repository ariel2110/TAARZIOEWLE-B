class ContextBuilder:
    def build(self, raw: dict) -> dict:
        return {
            'site_title': raw.get('site_title') or 'Business Draft',
            'hero_title': raw.get('hero_title') or raw.get('site_title') or 'Business Draft',
            'about_text': raw.get('about_text') or 'Professional draft website generated for review and outreach.',
            'is_demo': raw.get('is_demo', True),
        }
