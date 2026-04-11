import json
import re


class ContextBuilder:
    def build(self, raw: dict) -> dict:
        # Basic draft-site fields
        name = raw.get('name') or raw.get('site_title') or 'עסק'
        site_title = raw.get('site_title') or name
        hero_title = raw.get('hero_title') or name
        about_text = raw.get('about_text') or ''
        is_demo = raw.get('is_demo', True)

        # Business fields
        phone = raw.get('phone') or ''
        city = raw.get('city') or ''
        address = raw.get('address') or city or ''
        rating = raw.get('rating')
        reviews_count = raw.get('reviews_count') or 0
        website = raw.get('website') or ''
        category = raw.get('category') or ''
        business_types = raw.get('business_types') or ''
        tagline = raw.get('tagline') or ''
        services = raw.get('services') or raw.get('services_list') or []
        wa_admin_phone = raw.get('wa_admin_phone') or '972546363350'

        # Enrichment — from raw_json if provided, or top-level keys
        enrich = raw.get('enrichment') or {}
        if isinstance(enrich, str):
            try:
                enrich = json.loads(enrich)
            except Exception:
                enrich = {}

        maps_url = raw.get('maps_url') or enrich.get('google_maps_url') or ''
        top_review = raw.get('top_review') or enrich.get('top_review') or ''
        opening_hours = raw.get('opening_hours') or enrich.get('opening_hours') or []
        if isinstance(opening_hours, str):
            opening_hours = [opening_hours]

        return {
            'site_title': site_title,
            'hero_title': hero_title,
            'about_text': about_text,
            'is_demo': is_demo,
            'name': name,
            'phone': phone,
            'city': city,
            'address': address,
            'rating': rating,
            'reviews_count': reviews_count,
            'website': website,
            'category': category,
            'business_types': business_types,
            'tagline': tagline,
            'services': services,
            'maps_url': maps_url,
            'top_review': top_review,
            'opening_hours': opening_hours,
            'wa_admin_phone': wa_admin_phone,
        }
