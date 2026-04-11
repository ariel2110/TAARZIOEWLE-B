
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.draft_site import DraftSite
from app.models.business import Business
from app.models.activity_log import ActivityLog
from app.schemas.draft_site import DraftSiteCreate
from app.services.generator.context_builder import ContextBuilder
from app.services.generator.template_render_service import TemplateRenderService


class DraftSiteService:
    def list_drafts(self, db: Session, skip: int = 0, limit: int = 100) -> list[DraftSite]:
        return db.query(DraftSite).order_by(DraftSite.id.desc()).offset(skip).limit(limit).all()

    def create_draft(self, db: Session, payload: DraftSiteCreate) -> DraftSite:
        item = DraftSite(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def create_for_business(self, db: Session, business_id: int) -> DraftSite | None:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return None

        # Attempt LLM-generated copy; fall back to rule-based if unavailable
        copy = None
        try:
            from app.services.generator.site_copy_generator_service import SiteCopyGeneratorService
            copy = SiteCopyGeneratorService().generate(
                name=business.name,
                city=business.city,
                category=business.category,
            )
        except Exception:
            pass

        item = DraftSite(
            business_id=business.id,
            site_title=f"{business.name} Draft Site",
            hero_title=copy.hero_title if copy else business.name,
            about_text=copy.about_text if copy else f"Landing page draft for {business.name} in {business.city or 'Israel'}.",
            status='draft',
            is_demo=True,
            noindex=True,
            primary_color='#1d4ed8',
        )
        db.add(item)
        business.status = 'draft_created'
        db.flush()
        db.add(ActivityLog(actor_type='admin', entity_type='draft_site', entity_id=item.id, action_type='draft_created', summary=f'business_id={business.id}'))
        db.commit(); db.refresh(item)
        return item

    def get_draft(self, db: Session, draft_id: int) -> DraftSite | None:
        return db.query(DraftSite).filter(DraftSite.id == draft_id).first()

    def _build_enriched_context(self, db: Session, item: DraftSite) -> dict:
        """Merge draft fields, business data, and enrichment cache into one context dict."""
        import json as _json
        import os

        raw: dict = {
            'site_title': item.site_title,
            'hero_title': item.hero_title,
            'about_text': item.about_text,
            'is_demo': item.is_demo,
            'wa_admin_phone': os.getenv('WA_ADMIN_PHONE', '972546363350'),
        }

        # Fetch Business row
        business = db.query(Business).filter(Business.id == item.business_id).first()
        if business:
            raw['name'] = business.name
            raw['site_title'] = raw['site_title'] or f"{business.name}"
            raw['hero_title'] = raw['hero_title'] or business.name
            raw['phone'] = business.phone or ''
            raw['city'] = business.city or ''
            raw['category'] = business.category or ''

        # Fetch EnrichedBizCache
        try:
            from app.models.enriched_biz_cache import EnrichedBizCache
            enrich_row = None
            if business:
                enrich_row = (
                    db.query(EnrichedBizCache)
                    .filter(EnrichedBizCache.name == business.name)
                    .first()
                )
            if enrich_row:
                raw['phone'] = raw.get('phone') or enrich_row.phone or ''
                raw['address'] = enrich_row.address or business.city if business else ''
                raw['rating'] = enrich_row.rating
                raw['reviews_count'] = enrich_row.reviews_count or 0
                raw['website'] = enrich_row.website or ''
                raw['business_types'] = enrich_row.business_types or ''
                # parse raw_json
                rj = {}
                if enrich_row.raw_json:
                    try:
                        rj = _json.loads(enrich_row.raw_json) if isinstance(enrich_row.raw_json, str) else enrich_row.raw_json
                    except Exception:
                        rj = {}
                raw['maps_url'] = rj.get('google_maps_url') or ''
                raw['top_review'] = rj.get('top_review') or ''
                raw['opening_hours'] = rj.get('opening_hours') or []
        except Exception:
            pass

        return raw

    def generate_preview(self, db: Session, draft_id: int) -> DraftSite | None:
        item = self.get_draft(db, draft_id)
        if not item:
            return None
        raw = self._build_enriched_context(db, item)
        context = ContextBuilder().build(raw)
        html = TemplateRenderService().render(context)
        out_dir = Path(__file__).resolve().parents[2] / 'static_sites' / 'drafts'
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f'draft_{item.id}.html'
        out_file.write_text(html, encoding='utf-8')
        item.preview_url = f'/static/drafts/draft_{item.id}.html'
        item.status = 'published_preview'
        db.add(ActivityLog(actor_type='system', entity_type='draft_site', entity_id=item.id, action_type='draft_preview_generated', summary=item.preview_url))
        db.commit()
        db.refresh(item)
        return item

    def create_and_preview(self, db: Session, business_id: int) -> DraftSite | None:
        """Create draft (or reuse existing) then immediately generate beautiful preview."""
        # Reuse existing draft if present
        existing = db.query(DraftSite).filter(DraftSite.business_id == business_id).first()
        item = existing or self.create_for_business(db, business_id)
        if not item:
            return None
        return self.generate_preview(db, item.id)
