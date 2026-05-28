#!/usr/bin/env python3
"""
regen_premium_sites.py
----------------------
Regenerate HTML content for all existing DemoSite records using the updated
premium category templates.

Run inside the backend container:
    docker exec localbiz-backend python3 scripts/regen_premium_sites.py

Options:
    --dry-run   Print what would be regenerated without writing to DB
    --batch N   Process N sites per batch (default: 50)
    --slug SLUG  Regenerate only the site with this slug
"""

import sys, time, logging, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.demo_site import DemoSite
from app.services.generator.template_render_service import TemplateRenderService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("regen")

renderer = TemplateRenderService()


def _build_context(site: DemoSite) -> dict:
    return {
        "slug":           site.slug,
        "business_name":  site.business_name,
        "tagline":        site.tagline or "",
        "phone":          site.phone or "",
        "address":        site.address or "",
        "city":           site.city or "",
        "rating":         site.rating or 0,
        "reviews_count":  site.reviews_count or 0,
        "google_maps_url": site.google_maps_url or "",
        "top_review":     site.top_review or "",
        "business_types": site.business_types or "",
        "category":       site.category or "",
        "photo_url":      site.photo_url or "",
        "website":        site.website or "",
    }


def regen_all(dry_run: bool, batch_size: int, slug_filter: str | None) -> None:
    db: Session = SessionLocal()
    try:
        query = db.query(DemoSite)
        if slug_filter:
            query = query.filter(DemoSite.slug == slug_filter)

        total = query.count()
        log.info("Found %d site(s) to regenerate (dry_run=%s)", total, dry_run)

        processed = updated = errors = 0
        offset = 0

        while offset < total:
            batch = query.order_by(DemoSite.id).offset(offset).limit(batch_size).all()
            if not batch:
                break

            for site in batch:
                try:
                    ctx = _build_context(site)
                    new_html = renderer.render(ctx)

                    if dry_run:
                        log.info("[DRY-RUN] Would regen: %s (%s / %s)",
                                 site.slug, site.category or "—", site.city or "—")
                    else:
                        site.html_content = new_html  # type: ignore[attr-defined]
                        updated += 1

                    processed += 1
                except Exception as exc:
                    errors += 1
                    log.error("Error regenerating %s: %s", site.slug, exc)

            if not dry_run:
                try:
                    db.commit()
                    log.info("Batch committed: offset=%d processed=%d updated=%d errors=%d",
                             offset, processed, updated, errors)
                except Exception as exc:
                    db.rollback()
                    log.error("Commit failed at offset=%d: %s", offset, exc)

            offset += batch_size
            time.sleep(0.05)  # gentle pause between batches

        log.info("Done. processed=%d updated=%d errors=%d", processed, updated, errors)

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate all DemoSite HTML with premium templates")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing to DB")
    parser.add_argument("--batch", type=int, default=50, help="Sites per DB batch (default: 50)")
    parser.add_argument("--slug", type=str, default=None, help="Regenerate only this slug")
    args = parser.parse_args()

    regen_all(dry_run=args.dry_run, batch_size=args.batch, slug_filter=args.slug)
