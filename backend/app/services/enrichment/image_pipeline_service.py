"""Image pipeline — download, validate and cache business images locally.

Prevents dependency on expiring Google Places photo URLs.
Stores up to 6 images per business as a JSON list in DemoSite.gallery_urls.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(os.environ.get("STATIC_IMAGE_DIR", "app/static_sites/images"))
_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB per image
_MAX_IMAGES = 6
_TIMEOUT = 10


async def fetch_and_store_images(urls: list[str], business_slug: str) -> list[str]:
    """
    Download images from urls, store locally, return list of local/CDN URLs.
    Falls back to original URL if download fails.
    """
    if not urls:
        return []

    _STATIC_DIR.mkdir(parents=True, exist_ok=True)
    stored: list[str] = []

    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True,
                                  headers={"User-Agent": "TazoBot/1.0"}) as client:
        for raw_url in urls[:_MAX_IMAGES]:
            try:
                resp = await client.get(raw_url)
                if resp.status_code != 200:
                    stored.append(raw_url)
                    continue

                content_type = resp.headers.get("content-type", "").split(";")[0].strip()
                if content_type not in _ALLOWED_TYPES:
                    stored.append(raw_url)
                    continue

                content = resp.content
                if len(content) > _MAX_SIZE_BYTES:
                    stored.append(raw_url)
                    continue

                ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(content_type, "jpg")
                file_hash = hashlib.md5(raw_url.encode()).hexdigest()[:12]
                filename = f"{business_slug}_{file_hash}.{ext}"
                dest = _STATIC_DIR / filename

                if not dest.exists():
                    dest.write_bytes(content)

                local_url = f"/static_sites/images/{filename}"
                stored.append(local_url)

            except Exception as exc:
                logger.debug("[image-pipeline] failed to fetch %s: %s", raw_url[:80], exc)
                stored.append(raw_url)   # fallback to original

    return stored


def update_demo_site_gallery(demo_site, urls: list[str]) -> None:
    """Write gallery_urls JSON to a DemoSite instance (does not commit)."""
    demo_site.gallery_urls = json.dumps(urls[:_MAX_IMAGES], ensure_ascii=False)
    if urls and not demo_site.photo_url:
        demo_site.photo_url = urls[0]
