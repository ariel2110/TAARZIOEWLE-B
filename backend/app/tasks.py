"""
tasks.py — Celery background tasks for SiteNest.

All heavy AI operations and scheduled maintenance that would block the API
server (or should run periodically) live here:

  - generate_site_task   → 4-agent AI pipeline for one business
  - batch_generate_task  → fan-out site generation for N businesses
  - followup_task        → scan sent outreach, mark followup_due / stale
  - ceo_digest_task      → regenerate the CEO brain daily digest
"""
from __future__ import annotations

import logging
from typing import Any

from celery import Task

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


# ── Base task with common error handling ─────────────────────────────────────

class _BaseTask(Task):
    abstract = True

    def on_failure(self, exc: Exception, task_id: str, args: Any, kwargs: Any, einfo: Any) -> None:
        logger.error('[task:%s] failed — %s', task_id, exc, exc_info=True)


# ── Task 1: Generate draft site for a business ───────────────────────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.generate_site_task',
    max_retries=2,
    default_retry_delay=30,
)
def generate_site_task(self: Task, business_id: int) -> dict:
    """
    Run the 4-agent AI pipeline to generate a draft site for a business.

    Triggered from: POST /admin/tasks/generate-site/{business_id}
    Poll status at: GET  /admin/tasks/{task_id}/status

    Returns:
        {
            "status": "success" | "error",
            "business_id": int,
            "draft_site_id": int | None,
            "message": str,
        }
    """
    logger.info('[generate_site_task] starting for business_id=%d', business_id)

    try:
        from app.db.session import SessionLocal
        from app.models.business import Business
        from app.services.draft_sites.draft_site_service import DraftSiteService

        db = SessionLocal()
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                return {'status': 'error', 'business_id': business_id, 'draft_site_id': None, 'message': f'Business {business_id} not found'}

            # Run the full pipeline via DraftSiteService (creates/reuses draft, runs AI, writes HTML file)
            self.update_state(state='PROGRESS', meta={'step': 'running_ai_pipeline', 'business_id': business_id})
            draft = DraftSiteService().create_and_preview(db, business_id)

            if not draft:
                return {'status': 'error', 'business_id': business_id, 'draft_site_id': None, 'message': 'Pipeline returned no result'}

            logger.info('[generate_site_task] done — business_id=%d draft_id=%d', business_id, draft.id)
            return {
                'status': 'success',
                'business_id': business_id,
                'draft_site_id': draft.id,
                'preview_url': draft.preview_url,
                'message': f'Draft site generated successfully for {business.name}',
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error('[generate_site_task] exception for business_id=%d: %s', business_id, exc, exc_info=True)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'business_id': business_id,
                'draft_site_id': None,
                'message': f'Pipeline failed after retries: {exc}',
            }


# ── Task 5: Regenerate draft site with owner change instructions ─────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.regenerate_with_note_task',
    max_retries=2,
    default_retry_delay=30,
)
def regenerate_with_note_task(self: Task, business_id: int, regeneration_note: str) -> dict:
    """
    Re-run the AI pipeline for a business, injecting the owner's change note
    into Stage 1a so GPT-4o knows exactly what to update.

    Triggered from: POST /admin/tasks/regenerate-with-note/{business_id}
    """
    logger.info(
        '[regenerate_with_note_task] business_id=%d note_len=%d',
        business_id, len(regeneration_note or ''),
    )
    try:
        from app.db.session import SessionLocal
        from app.models.business import Business
        from app.services.draft_sites.draft_site_service import DraftSiteService

        db = SessionLocal()
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                return {
                    'status': 'error', 'business_id': business_id,
                    'draft_site_id': None,
                    'message': f'Business {business_id} not found',
                }

            self.update_state(state='PROGRESS', meta={'step': 'running_ai_pipeline', 'business_id': business_id})
            draft = DraftSiteService().create_and_preview(
                db, business_id, regeneration_note=regeneration_note
            )

            if not draft:
                return {
                    'status': 'error', 'business_id': business_id,
                    'draft_site_id': None,
                    'message': 'Pipeline returned no result',
                }

            logger.info(
                '[regenerate_with_note_task] done — business_id=%d draft_id=%d',
                business_id, draft.id,
            )
            return {
                'status': 'success',
                'business_id': business_id,
                'draft_site_id': draft.id,
                'preview_url': draft.preview_url,
                'message': f'Draft regenerated for {business.name} with custom note',
            }
        finally:
            db.close()

    except Exception as exc:
        logger.error(
            '[regenerate_with_note_task] exception for business_id=%d: %s',
            business_id, exc, exc_info=True,
        )
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'business_id': business_id,
                'draft_site_id': None,
                'message': f'Pipeline failed after retries: {exc}',
            }


@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.batch_generate_task',
    max_retries=0,
)
def batch_generate_task(self: Task, business_ids: list[int]) -> dict:
    """
    Spawn individual generate_site_task for each business_id in the list.
    Returns immediately with sub-task IDs for tracking.
    """
    sub_tasks = []
    for bid in business_ids:
        task = generate_site_task.delay(bid)
        sub_tasks.append({'business_id': bid, 'task_id': task.id})
    return {'status': 'dispatched', 'count': len(sub_tasks), 'tasks': sub_tasks}


# ── Task 3: Follow-up worker ─────────────────────────────────────────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.followup_task',
    max_retries=1,
    default_retry_delay=60,
)
def followup_task(self: Task) -> dict:
    """
    Scan sent outreach messages and mark them as followup_due or stale.

    Runs from Celery Beat every day at 09:00.
    Delegates to the existing followup_worker.run() logic (single source of truth).
    """
    logger.info('[followup_task] starting')
    try:
        from app.workers.followup_worker import run as _run_followup
        _run_followup()
        return {'status': 'ok'}
    except Exception as exc:
        logger.error('[followup_task] failed: %s', exc, exc_info=True)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {'status': 'error', 'message': str(exc)}


# ── Task 5: Inbound Magic Portal — customer-initiated full build ─────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.inbound_build_task',
    max_retries=1,
    default_retry_delay=30,
    time_limit=480,
    soft_time_limit=450,
)
def inbound_build_task(self: Task, business_id: int) -> dict:
    """
    Full AI pipeline triggered by a public inbound request (Magic Portal).

    Progress states emitted for frontend polling:
      scouting   → fetching Maps + social data
      scouted    → data ready; frontend shows phone-capture wall
      building   → Claude HTML generation in progress
      done       → draft ready

    Returns:
        {"status": "success"|"error", "preview_url": str, "draft_site_id": int}
    """
    logger.info('[inbound_build_task] starting for business_id=%d', business_id)
    try:
        import json as _json
        from app.db.session import SessionLocal
        from app.models.business import Business
        from app.models.draft_site import DraftSite
        from app.services.draft_sites.draft_site_service import DraftSiteService

        db = SessionLocal()
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                return {'status': 'error', 'business_id': business_id, 'message': f'Business {business_id} not found'}

            svc = DraftSiteService()

            # ── Stage 0 prep: get or create draft ────────────────────────────
            self.update_state(state='PROGRESS', meta={
                'step': 'scouting', 'percent': 8,
                'label': 'שואב דירוגים וביקורות מגוגל מפות...',
            })
            existing = db.query(DraftSite).filter(DraftSite.business_id == business_id).first()
            draft = existing or svc.create_for_business(db, business_id)
            if not draft:
                return {'status': 'error', 'business_id': business_id, 'message': 'Could not create draft'}

            # ── Stage 0 enrichment context (reads cache — fast) ───────────────
            enrichment = svc._build_enriched_context(db, draft)

            self.update_state(state='PROGRESS', meta={
                'step': 'social', 'percent': 22,
                'label': 'מאתר חשבון אינסטגרם וטיקטוק שלך...',
            })

            # ── Run social discovery ──────────────────────────────────────────
            from app.services.generator.autosite_pipeline_service import AutoSitePipelineService
            pipeline = AutoSitePipelineService()
            social = pipeline._stage0_social_discovery(enrichment)
            enrichment = {**enrichment, '_social': social}

            self.update_state(state='PROGRESS', meta={
                'step': 'scouted', 'percent': 40,
                'label': 'מצאנו הכל! מנתח שירותים מובילים מתוך איזי...',
            })

            # ── Stage 1a: GPT content generation ─────────────────────────────
            self.update_state(state='PROGRESS', meta={
                'step': 'content', 'percent': 55,
                'label': 'ה-AI מנתח ומבין את העסק שלך...',
            })
            raw_str = _json.dumps({
                'name': enrichment.get('name', business.name),
                'city': enrichment.get('city', business.city or ''),
                'category': enrichment.get('category', business.category or ''),
                'phone': enrichment.get('phone', business.phone or ''),
                'address': enrichment.get('address', business.address or ''),
                'rating': enrichment.get('rating'),
                'reviews_count': enrichment.get('reviews_count', 0),
                'website': enrichment.get('website', ''),
                'top_review': enrichment.get('top_review', ''),
                'opening_hours': enrichment.get('opening_hours', []),
            }, ensure_ascii=False)

            content = pipeline._stage1a_content(raw_str, social=social)

            # ── Stage 1b: Gemini design ───────────────────────────────────────
            self.update_state(state='PROGRESS', meta={
                'step': 'designing', 'percent': 68,
                'label': 'מעצב לפי צבעי המותג שלך...',
            })
            design = pipeline._stage1b_design(raw_str)

            # ── Stage 2: Claude HTML ──────────────────────────────────────────
            self.update_state(state='PROGRESS', meta={
                'step': 'building', 'percent': 80,
                'label': 'ה-AI בונה כעת את האתר שלך...',
            })
            html = pipeline._stage2_build(content, design, enrichment) if content else None

            if not html:
                # Fallback to standard DraftSiteService if custom pipeline failed
                result_draft = svc.generate_preview(db, draft.id)
            else:
                # Save HTML to draft
                from app.services.draft_sites.draft_site_service import DraftSiteService as _DSS
                import os
                draft.html_content = html
                draft.status = 'preview_ready'
                static_dir = os.path.join(os.path.dirname(__file__), 'static_sites', 'drafts')
                os.makedirs(static_dir, exist_ok=True)
                html_path = os.path.join(static_dir, f'draft_{draft.id}.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                draft.preview_url = f'/static/drafts/draft_{draft.id}.html'
                db.commit()
                result_draft = draft

            if not result_draft:
                return {'status': 'error', 'business_id': business_id, 'message': 'Pipeline returned no result'}

            self.update_state(state='PROGRESS', meta={
                'step': 'done', 'percent': 100,
                'label': '🎉 האתר מוכן!',
            })

            from app.services.public.site_domain_service import build_draft_public_url, build_draft_subdomain
            from app.models.demo_site import DemoSite
            public_url = build_draft_public_url(result_draft.id, business.name)

            # Keep /admin/demos in sync with inbound-created draft sites.
            try:
                demo_slug = build_draft_subdomain(result_draft.id, business.name)
                demo = db.query(DemoSite).filter(DemoSite.slug == demo_slug).first()
                demo_values = {
                    'slug': demo_slug,
                    'business_name': business.name,
                    'phone': business.phone,
                    'address': business.address,
                    'city': business.city,
                    'rating': enrichment.get('rating'),
                    'reviews_count': enrichment.get('reviews_count', 0),
                    'google_maps_url': enrichment.get('maps_url', ''),
                    'top_review': enrichment.get('top_review', ''),
                    'business_types': enrichment.get('business_types', ''),
                    'category': business.category,
                    'status': 'draft',
                }
                if demo:
                    for key, value in demo_values.items():
                        setattr(demo, key, value)
                else:
                    demo = DemoSite(**demo_values)
                    db.add(demo)
                db.commit()
            except Exception:
                logger.exception('[inbound_build_task] failed to sync demo row for draft_id=%d', result_draft.id)

            logger.info('[inbound_build_task] done — business_id=%d draft_id=%d', business_id, result_draft.id)
            return {
                'status': 'success',
                'business_id': business_id,
                'draft_site_id': result_draft.id,
                'preview_url': result_draft.preview_url,
                'public_url': public_url,
                'message': 'Demo site ready!',
            }
        finally:
            db.close()

    except Exception as exc:
        logger.error('[inbound_build_task] exception for business_id=%d: %s', business_id, exc, exc_info=True)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {'status': 'error', 'business_id': business_id, 'message': f'Pipeline failed: {exc}'}


# ── Task 4: CEO digest worker ────────────────────────────────────────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.ceo_digest_task',
    max_retries=1,
    default_retry_delay=120,
    time_limit=600,
    soft_time_limit=540,
)
def ceo_digest_task(self: Task) -> dict:
    """
    Regenerate the CEO daily digest (AI-powered summary of platform KPIs).

    Runs from Celery Beat every 6 hours.
    Delegates to ceo_digest_worker.run() — heavy LLM call, hence off-thread.
    """
    logger.info('[ceo_digest_task] starting')
    try:
        from app.workers.ceo_digest_worker import run as _run_digest
        _run_digest()
        return {'status': 'ok'}
    except Exception as exc:
        logger.error('[ceo_digest_task] failed: %s', exc, exc_info=True)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {'status': 'error', 'message': str(exc)}


# ── Task: Finalize deployment after successful payment ───────────────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.finalize_deployment_task',
    max_retries=3,
    default_retry_delay=60,
    time_limit=600,
    soft_time_limit=570,
)
def finalize_deployment_task(self: Task, token: str) -> dict:
    """
    End-to-end site activation triggered after a successful Morning payment.

    Steps:
      1. Load PublicIntake by token — abort if not found or not paid
      2. Validate domain (.co.il / .com only)
      3. Purchase domain via Hostinger API (with availability pre-check)
      4. Set DNS A record → server public IP
      5. Deploy generated HTML to production path (/static_sites/live/{domain}/)
      6. Create nginx virtual-host config + reload nginx
      7. Issue SSL certificate via Certbot (--nginx --redirect)
      8. Update DB: site_live_url, status = 'done'
      9. Send WhatsApp congratulations to the client via Evolution API

    If domain purchase fails (taken / API error), the admin is notified
    via WhatsApp and the task is retried up to 3 times with 60 s delay.

    Triggered from: POST /webhooks/morning (on SUCCESS for 'auto' tier)
    """
    logger.info('[finalize_deployment_task] starting for token=%s', token[:8])

    try:
        from app.db.session import SessionLocal
        from app.models.public_intake import PublicIntake
        from app.services.hostinger_service import HostingerService
        from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService
        from app.core.config import settings

        db = SessionLocal()
        try:
            intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()

            # ── Guards ────────────────────────────────────────────────────────
            if not intake:
                logger.error('[finalize_deployment_task] Intake not found: token=%s', token[:8])
                return {'status': 'error', 'message': 'intake not found', 'token': token[:8]}

            if intake.payment_status != 'paid':
                logger.error(
                    '[finalize_deployment_task] Payment not confirmed for token=%s status=%s',
                    token[:8], intake.payment_status,
                )
                return {'status': 'error', 'message': 'payment not confirmed', 'token': token[:8]}

            domain = intake.desired_domain or ''
            html_content = intake.generated_html or ''

            if not domain or not html_content:
                logger.error(
                    '[finalize_deployment_task] Missing domain or HTML for token=%s', token[:8]
                )
                return {'status': 'error', 'message': 'missing domain or html', 'token': token[:8]}

            business_name = intake.business_name or ''
            phone = intake.phone or ''
        finally:
            db.close()

        # ── Steps 2-7: Hostinger full activation ──────────────────────────────
        self.update_state(state='PROGRESS', meta={
            'step': 'activating_site', 'domain': domain, 'token': token[:8],
        })

        ok, live_url = HostingerService().activate_site(domain, html_content)

        # ── Step 8: Update DB ──────────────────────────────────────────────────
        db = SessionLocal()
        try:
            intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
            if intake:
                intake.site_live_url = live_url if ok else ''
                intake.status = 'done'
                db.commit()
        finally:
            db.close()

        # ── Step 9: WhatsApp outreach ──────────────────────────────────────────
        if ok:
            message = (
                f"🎉 מזל טוב {business_name}!\n\n"
                f"האתר שלך באוויר בכתובת החדשה:\n{live_url}\n\n"
                f"💳 המנוי שלך הוא 39 ₪/חודש — כולל אחסון, תחזוקה ועדכונים.\n\n"
                f"שנצליח ביחד 🚀\n_צוות SiteNest_"
            )
            EvolutionWhatsAppService().send_text(phone, message)
            logger.info(
                '[finalize_deployment_task] Done — domain=%s live_url=%s', domain, live_url
            )
            return {'status': 'success', 'domain': domain, 'live_url': live_url, 'token': token[:8]}

        else:
            # Notify admin; retry will re-attempt the full activation
            _admin_phone = getattr(settings, 'whatsapp_owner_phone', '')
            if _admin_phone:
                EvolutionWhatsAppService().send_text(
                    _admin_phone,
                    f"⚠️ *SiteNest — הפעלת אתר נכשלה*\n\n"
                    f"Token: `{token[:12]}...`\n"
                    f"Domain: {domain}\n"
                    f"Error: {live_url}\n\n"
                    f"המשימה תנסה שוב אוטומטית.",
                )
            raise ValueError(f'activate_site failed for {domain}: {live_url}')

    except ValueError as exc:
        # Retryable failure (domain not ready, Hostinger API issues)
        logger.error('[finalize_deployment_task] retryable error: %s', exc)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(
                '[finalize_deployment_task] max retries exceeded for token=%s', token[:8]
            )
            return {'status': 'error', 'message': str(exc), 'token': token[:8]}

    except Exception as exc:
        logger.error(
            '[finalize_deployment_task] unhandled exception for token=%s: %s',
            token[:8], exc, exc_info=True,
        )
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {'status': 'error', 'message': str(exc), 'token': token[:8]}


# ── Task: Abandonment-recovery WhatsApp (10 min after page-contacted) ─────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.send_abandonment_recovery_task',
    max_retries=1,
    default_retry_delay=60,
)
def send_abandonment_recovery_task(self: Task, client_name: str, client_phone: str) -> dict:
    """
    Sent 10 minutes after a ``sale-pages/page-contacted`` event.

    Checks whether the lead has since converted (paid) — if yes, skip.
    Otherwise sends a WhatsApp recovery message to the lead via Evolution API.

    The message body is generated by xAI Grok when the API key is configured;
    otherwise falls back to a fixed Hebrew template.
    """
    if not client_phone:
        logger.info('[abandonment_recovery] No phone — skipping')
        return {'status': 'skipped', 'reason': 'no phone'}

    # ── Conversion check: did they pay in the last 15 minutes? ────────────
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake

    db = SessionLocal()
    try:
        converted = (
            db.query(PublicIntake)
            .filter(
                PublicIntake.phone == client_phone,
                PublicIntake.payment_status == 'paid',
            )
            .first()
        )
    finally:
        db.close()

    if converted:
        logger.info(
            '[abandonment_recovery] Lead %s already converted — skipping recovery message',
            client_phone[:8],
        )
        return {'status': 'skipped', 'reason': 'already_converted'}

    # ── Build message (Grok if configured, else template) ─────────────────
    message = _build_recovery_message(client_name)

    # ── Send WhatsApp ──────────────────────────────────────────────────────
    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService

    sent = EvolutionWhatsAppService().send_text(client_phone, message)
    if sent:
        logger.info(
            '[abandonment_recovery] Recovery message sent to %s***', client_phone[:6]
        )
        return {'status': 'sent', 'phone': client_phone[:8]}

    logger.warning(
        '[abandonment_recovery] Failed to send recovery message to %s***', client_phone[:6]
    )
    return {'status': 'failed', 'phone': client_phone[:8]}


def _build_recovery_message(client_name: str) -> str:
    """
    Return a personalised recovery message.
    Uses xAI Grok API when ``settings.xai_api_key`` is set;
    falls back to a fixed Hebrew template.
    """
    from app.core.config import settings

    first_name = (client_name or '').split()[0] if client_name else 'שלום'

    if settings.xai_api_key:
        try:
            import httpx

            prompt = (
                f"Write a short, warm, conversational WhatsApp message in Hebrew "
                f"to someone named {first_name} who started building a website on SiteNest "
                f"but didn't complete payment. "
                f"The message should feel personal, not salesy. "
                f"Maximum 3 sentences. No emojis at the start. End with one relevant emoji. "
                f"Address them as '{first_name}'."
            )
            resp = httpx.post(
                'https://api.x.ai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {settings.xai_api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': 'grok-3-mini',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 120,
                    'temperature': 0.7,
                },
                timeout=20,
            )
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content'].strip()
                logger.info('[abandonment_recovery] Grok message generated (%d chars)', len(content))
                return content
            logger.warning(
                '[abandonment_recovery] Grok API returned %d — falling back to template',
                resp.status_code,
            )
        except Exception as exc:
            logger.warning('[abandonment_recovery] Grok API error: %s — using template', exc)

    # Fixed template fallback
    return (
        f"היי {first_name}, ראיתי שהתחלת לבנות אתר אבל לא סיימת. "
        f"יש משהו שאני יכול לעזור? 😊"
    )
