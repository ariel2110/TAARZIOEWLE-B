"""Hostinger domain & DNS service
==================================
Handles domain availability checks, registration, DNS management,
nginx virtual-host creation, and SSL via Certbot.

Safety constraints:
- Only .co.il and .com domains are purchased automatically.
  Expensive TLDs (.ai, .io, etc.) are blocked to protect the 39 NIS margin.
- Domain is always re-checked for availability immediately before purchase
  to prevent paying Morning and then failing at Hostinger.
- All subprocess calls use explicit argument lists (no shell=True).

Hostinger API docs: https://developers.hostinger.com/
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_HOSTINGER_BASE = 'https://api.hostinger.com/v1'
_TIMEOUT = 20
_ALLOWED_TLDS = {'.co.il', '.com'}
_NGINX_SITES_AVAILABLE = Path('/etc/nginx/sites-available')
_NGINX_SITES_ENABLED = Path('/etc/nginx/sites-enabled')
_STATIC_ROOT = Path('/home/tazo-web-platform/backend/app/static_sites/live')


class HostingerService:

    # ── Domain validation ─────────────────────────────────────────────────────

    def validate_domain(self, domain: str) -> tuple[bool, str]:
        """
        Check if domain is syntactically valid and belongs to an allowed TLD.
        Returns (ok, error_message).
        """
        domain = domain.strip().lower()
        # Basic sanity check
        if not re.match(r'^[a-z0-9][a-z0-9\-\.]*\.[a-z]{2,}(\.[a-z]{2})?$', domain):
            return False, 'שם דומיין לא תקין'
        tld = '.' + '.'.join(domain.rsplit('.', 2)[-2:]) if domain.count('.') >= 2 and domain.endswith('.co.il') else '.' + domain.rsplit('.', 1)[-1]
        if tld not in _ALLOWED_TLDS:
            return False, f'TLD "{tld}" לא נתמך — רק .co.il ו-.com'
        return True, ''

    def check_availability(self, domain: str) -> bool:
        """
        Check if a domain is available to register.
        Returns True if available, False if taken or API is unconfigured.
        """
        if not self._is_configured():
            logger.info('[Hostinger] Not configured — skipping availability check')
            return True  # optimistic in dev

        try:
            resp = httpx.get(
                f'{_HOSTINGER_BASE}/domains/availability',
                params={'domain': domain},
                headers=self._headers(),
                timeout=_TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Hostinger returns {available: true/false} or {data: {available: ...}}
                available = (
                    data.get('available')
                    or (data.get('data') or {}).get('available')
                )
                return bool(available)
        except Exception as exc:
            logger.warning('[Hostinger] Availability check failed: %s', exc)
        return False

    def purchase_domain(self, domain: str) -> bool:
        """
        Register the domain via Hostinger API.
        Returns True on success, False on failure.
        """
        if not self._is_configured():
            logger.warning('[Hostinger] Not configured — cannot purchase domain')
            return False

        # Never purchase expensive TLDs or syntactically bad domains
        ok, err = self.validate_domain(domain)
        if not ok:
            logger.error('[Hostinger] Domain rejected: %s (%s)', domain, err)
            return False

        # Double-check availability right before buying (prevents paying twice)
        if not self.check_availability(domain):
            logger.error('[Hostinger] Domain not available at purchase time: %s', domain)
            return False

        try:
            resp = httpx.post(
                f'{_HOSTINGER_BASE}/domains',
                json={
                    'domain': domain,
                    'period': 1,          # 1 year
                    'privacyProtection': True,
                },
                headers=self._headers(),
                timeout=_TIMEOUT,
            )
            if resp.status_code in (200, 201):
                logger.info('[Hostinger] Domain registered: %s', domain)
                return True
            logger.error('[Hostinger] Purchase failed %d: %s', resp.status_code, resp.text[:300])
        except Exception as exc:
            logger.error('[Hostinger] Purchase exception: %s', exc)
        return False

    def set_dns_a_record(self, domain: str, ip: str | None = None) -> bool:
        """
        Set (or update) DNS A record for `domain` pointing to the server's public IP.
        """
        target_ip = ip or settings.server_public_ip
        if not self._is_configured():
            logger.warning('[Hostinger] Not configured — cannot set DNS')
            return False

        try:
            resp = httpx.put(
                f'{_HOSTINGER_BASE}/domains/{domain}/dns/zone',
                json={
                    'zone': [
                        {'type': 'A', 'name': '@', 'content': target_ip, 'ttl': 14400},
                        {'type': 'A', 'name': 'www', 'content': target_ip, 'ttl': 14400},
                    ]
                },
                headers=self._headers(),
                timeout=_TIMEOUT,
            )
            if resp.status_code in (200, 201, 204):
                logger.info('[Hostinger] DNS A record set: %s → %s', domain, target_ip)
                return True
            logger.error('[Hostinger] DNS update failed %d: %s', resp.status_code, resp.text[:300])
        except Exception as exc:
            logger.error('[Hostinger] DNS exception: %s', exc)
        return False

    # ── Site deployment ───────────────────────────────────────────────────────

    def deploy_html(self, domain: str, html_content: str) -> Path:
        """Write the generated HTML to a static file served by nginx."""
        site_dir = _STATIC_ROOT / domain
        site_dir.mkdir(parents=True, exist_ok=True)
        html_path = site_dir / 'index.html'
        html_path.write_text(html_content, encoding='utf-8')
        logger.info('[Hostinger] HTML deployed to %s', html_path)
        return html_path

    def create_nginx_vhost(self, domain: str, html_root: Path) -> bool:
        """Create an nginx virtual host config for the domain."""
        config = f"""server {{
    listen 80;
    server_name {domain} www.{domain};
    root {html_root};
    index index.html;
    location / {{
        try_files $uri $uri/ /index.html;
    }}
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
}}
"""
        conf_path = _NGINX_SITES_AVAILABLE / f'{domain}.conf'
        enabled_path = _NGINX_SITES_ENABLED / f'{domain}.conf'
        try:
            conf_path.write_text(config)
            if not enabled_path.exists():
                enabled_path.symlink_to(conf_path)
            self._nginx_reload()
            logger.info('[Hostinger] nginx vhost created: %s', domain)
            return True
        except Exception as exc:
            logger.error('[Hostinger] nginx vhost failed: %s', exc)
            return False

    def issue_ssl_certificate(self, domain: str) -> bool:
        """Run certbot to obtain/renew an SSL certificate for the domain."""
        try:
            result = subprocess.run(
                [
                    'certbot', '--nginx',
                    '-d', domain,
                    '-d', f'www.{domain}',
                    '--non-interactive',
                    '--agree-tos',
                    '--email', 'ar.2110@gmail.com',
                    '--redirect',          # force HTTPS
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                logger.info('[Hostinger] SSL issued for %s', domain)
                return True
            logger.error('[Hostinger] certbot failed: %s', result.stderr[:500])
        except FileNotFoundError:
            logger.error('[Hostinger] certbot not found — install with: apt install certbot python3-certbot-nginx')
        except subprocess.TimeoutExpired:
            logger.error('[Hostinger] certbot timed out for %s', domain)
        except Exception as exc:
            logger.error('[Hostinger] SSL exception: %s', exc)
        return False

    # ── Full activation pipeline ──────────────────────────────────────────────

    def activate_site(self, domain: str, html_content: str) -> tuple[bool, str]:
        """
        Full site activation:
          1. Validate + re-check domain availability
          2. Purchase domain
          3. Set DNS A record
          4. Deploy HTML
          5. Create nginx vhost
          6. Issue SSL certificate
        Returns (success, live_url).
        """
        ok, err = self.validate_domain(domain)
        if not ok:
            return False, err

        logger.info('[Hostinger] Starting site activation for %s', domain)

        # Step 1: Purchase domain
        if not self.purchase_domain(domain):
            return False, f'רכישת הדומיין {domain} נכשלה'

        # Step 2: DNS A record
        self.set_dns_a_record(domain)  # non-blocking failure — proceed anyway

        # Step 3: Deploy HTML
        html_root = self.deploy_html(domain, html_content)

        # Step 4: nginx vhost
        if not self.create_nginx_vhost(domain, html_root):
            return False, 'יצירת תצורת nginx נכשלה'

        # Step 5: SSL — fire and forget; site is accessible over HTTP in the meantime
        ssl_ok = self.issue_ssl_certificate(domain)
        live_url = f'https://{domain}' if ssl_ok else f'http://{domain}'

        logger.info('[Hostinger] Site activated: %s (ssl=%s)', domain, ssl_ok)
        return True, live_url

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _is_configured(self) -> bool:
        return bool(settings.hostinger_api_token and settings.hostinger_api_token != 'your_token_here')

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {settings.hostinger_api_token}',
            'Content-Type': 'application/json',
        }

    def _nginx_reload(self) -> None:
        subprocess.run(['nginx', '-s', 'reload'], capture_output=True, timeout=10)
