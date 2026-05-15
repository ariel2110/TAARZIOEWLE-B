from __future__ import annotations

import re
import unicodedata

PUBLIC_SITE_ROOT = 'TAZO-WEB.site'
RESERVED_SUBDOMAINS = {'www', 'api', 'admin', 'customer'}


def normalize_dns_label(text: str) -> str:
    base = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode('ascii').lower()
    base = re.sub(r'[^a-z0-9]+', '-', base).strip('-')
    base = re.sub(r'-{2,}', '-', base)
    return base


def build_draft_subdomain(draft_id: int, business_name: str | None = None) -> str:
    prefix = normalize_dns_label(business_name or '')
    if not prefix:
        prefix = 'site'
    # Keep room for suffix and stay within DNS label limit.
    prefix = prefix[:48].strip('-') or 'site'
    return f'{prefix}-{draft_id}'


def build_draft_public_url(draft_id: int, business_name: str | None = None, *, scheme: str = 'https') -> str:
    sub = build_draft_subdomain(draft_id, business_name)
    return f'{scheme}://{sub}.{PUBLIC_SITE_ROOT}'


def build_demo_public_url(slug: str, *, scheme: str = 'https') -> str:
    safe_slug = normalize_dns_label(slug)[:63].strip('-') or 'demo'
    return f'{scheme}://{safe_slug}.{PUBLIC_SITE_ROOT}'


def parse_subdomain_from_host(host: str) -> str | None:
    hostname = (host or '').split(':', 1)[0].strip().lower()
    suffix = f'.{PUBLIC_SITE_ROOT}'
    if not hostname.endswith(suffix):
        return None
    sub = hostname[: -len(suffix)]
    if not sub or '.' in sub:
        return None
    if sub in RESERVED_SUBDOMAINS:
        return None
    return sub
