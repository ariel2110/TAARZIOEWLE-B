
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

    def _generate_html(self, raw: dict, regeneration_note: str | None = None) -> tuple[str, str | None]:
        """Try the AI pipeline first; fall back to the static template.
        Returns (html, outreach_message_with_placeholder).
        """

        # Build raw text input for GPT-4o (mimics Google Maps listing)
        pipeline_input_parts = [
            f"Name: {raw.get('name') or raw.get('site_title', '')}",
            f"Phone: {raw.get('phone', '')}",
            f"City: {raw.get('city', '')}",
            f"Category: {raw.get('category', '')}",
            f"Address: {raw.get('address', '')}",
        ]
        if raw.get('rating'):
            pipeline_input_parts.append(f"Rating: {raw['rating']} ({raw.get('reviews_count', 0)} reviews)")
        if raw.get('top_review'):
            pipeline_input_parts.append(f"Top review: {raw['top_review']}")
        if raw.get('opening_hours'):
            hrs = raw['opening_hours']
            if isinstance(hrs, list):
                hrs = " | ".join(hrs[:3])
            pipeline_input_parts.append(f"Hours: {hrs}")
        if raw.get('website'):
            pipeline_input_parts.append(f"Website: {raw['website']}")

        pipeline_input = "\n".join(pipeline_input_parts)

        # Build enrichment dict: all structured data for the pipeline (reviews, hours, etc.)
        enrichment = {
            'top_review': raw.get('top_review') or '',
            'reviews': raw.get('reviews') or ([raw['top_review']] if raw.get('top_review') else []),
            'rating': raw.get('rating'),
            'reviews_count': raw.get('reviews_count') or 0,
            'opening_hours': raw.get('opening_hours') or [],
            # ── For Stage 0.5 (Firecrawl website scraper) ────────────────────
            'website_url': raw.get('website') or '',
            'category': raw.get('category') or '',
            'business_types': raw.get('business_types') or '',
            'name': raw.get('name') or '',
            'city': raw.get('city') or '',
        }

        try:
            from app.services.generator.autosite_pipeline_service import AutoSitePipelineService
            result = AutoSitePipelineService().run(pipeline_input, enrichment=enrichment, regeneration_note=regeneration_note)
            if result and result.html and len(result.html) > 500:
                return result.html, result.outreach_message
        except Exception:
            import logging
            logging.getLogger(__name__).info("AutoSite pipeline unavailable, using static template fallback")

        # Fallback: our own static template
        context = ContextBuilder().build(raw)
        # Attempt to enrich context with Firecrawl scrape even in fallback path
        website_url = raw.get('website') or ''
        if website_url:
            try:
                from app.services.enrichment.website_scraper_service import WebsiteScraperService
                scraped = WebsiteScraperService().scrape(
                    url=website_url,
                    category=raw.get('category', ''),
                    business_types=raw.get('business_types', ''),
                )
                if scraped.scraped_ok:
                    if scraped.hero_image_url and not context.get('hero_image_url'):
                        context['hero_image_url'] = scraped.hero_image_url
                    if scraped.gallery_images:
                        context.setdefault('gallery_images', scraped.gallery_images)
                    if scraped.about_text and not context.get('about_text'):
                        context['about_text'] = scraped.about_text
                    if scraped.tagline and not context.get('tagline'):
                        context['tagline'] = scraped.tagline
                    if scraped.menu_items and not context.get('menu_items'):
                        context['menu_items'] = scraped.menu_items
            except Exception:
                pass
        return TemplateRenderService().render(context), None

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

    def generate_preview(self, db: Session, draft_id: int, regeneration_note: str | None = None) -> DraftSite | None:
        item = self.get_draft(db, draft_id)
        if not item:
            return None

        raw = self._build_enriched_context(db, item)
        html, outreach_message = self._generate_html(raw, regeneration_note=regeneration_note)

        out_dir = Path(__file__).resolve().parents[2] / 'static_sites' / 'drafts'
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f'draft_{item.id}.html'
        out_file.write_text(html, encoding='utf-8')
        item.preview_url = f'/static/drafts/draft_{item.id}.html'
        item.status = 'published_preview'
        db.add(ActivityLog(actor_type='system', entity_type='draft_site', entity_id=item.id, action_type='draft_preview_generated', summary=(f'[note] {regeneration_note[:120]}' if regeneration_note else item.preview_url)))
        # ── Auto-create AI-generated outreach message ─────────────────────────
        if outreach_message and item.business_id:
            try:
                from app.services.public.site_domain_service import build_draft_public_url
                full_demo_url = build_draft_public_url(item.id, raw.get('name'))
                final_message = outreach_message.replace('[DEMO_LINK]', full_demo_url)

                from app.models.outreach_message import OutreachMessage as OutreachModel
                business = db.query(Business).filter(Business.id == item.business_id).first()
                outreach = OutreachModel(
                    business_id=item.business_id,
                    draft_site_id=item.id,
                    channel='whatsapp',
                    status='draft',
                    message_template_key='ai_generated_v1',
                    content=final_message,
                    outbound_target=business.phone if business else None,
                    city_context=business.city if business else None,
                    category_context=business.category if business else None,
                )
                db.add(outreach)
                db.add(ActivityLog(actor_type='system', entity_type='outreach_message', entity_id=0, action_type='ai_outreach_created', summary=f'business_id={item.business_id}'))
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Failed to create AI outreach message")

        db.commit()
        db.refresh(item)
        return item

    def create_and_preview(self, db: Session, business_id: int, regeneration_note: str | None = None) -> DraftSite | None:
        """Create draft (or reuse existing) then immediately generate beautiful preview."""
        # Reuse existing draft if present
        existing = db.query(DraftSite).filter(DraftSite.business_id == business_id).first()
        item = existing or self.create_for_business(db, business_id)
        if not item:
            return None
        return self.generate_preview(db, item.id, regeneration_note=regeneration_note)
