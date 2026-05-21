---
applyTo: "**"
description: "Tazo Web (tazo-web.com | 76.13.48.23) — FastAPI marketplace, Celery+Redis background jobs, OpenAI integration, Apify scraping, Shadow Store engine, 3 React frontends. Apply to all files in TAARZIOEWLE-B."
---

# Tazo Web — Development Instructions

**Node**: Tazo Web | **Domain**: tazo-web.com | **IP**: 76.13.48.23  
**Role**: Consumer marketplace, frontend shell, Shadow Store micro-frontend engine.

---

## Stack Contracts

| Layer | Technology | Rule |
|-------|-----------|------|
| Runtime | Python 3.12 + FastAPI + Uvicorn | All endpoints `async def`; sync Celery tasks in `backend/services/` |
| Frontends | React + TypeScript (3 apps: admin, customer, public) | `frontend-admin`, `frontend-customer`, `frontend-public` |
| Database | PostgreSQL 16 (port 5433) | Alembic only. Auto-migration on container start is allowed for dev; never in prod |
| Queue | Redis-alpine (port 6380) + Celery | Celery queue name: `TAZO-WEB`, concurrency=2, Celery Beat for scheduled jobs |
| AI/Scraping | OpenAI API + Apify client | All AI calls server-side. Apify for merchant data enrichment in Shadow Store pipeline |
| Auth | JWT (python-jose+crypto) + bcrypt | Passwords hashed with bcrypt rounds=12. JWT access: 15 min, refresh: 7 days |

---

## The Shadow Store Engine — Core Rules

The Shadow Store is Tazo Web's growth engine. When a user searches for a merchant that does not exist in the platform:

1. **Detection**: `/api/v1/shadow/check` receives `{query, place_id}` — checks Postgres for existing merchant
2. **Apify Enrichment**: If not found, dispatch Celery task `enrich_merchant_data` — scrapes Google Places/Maps via Apify for name, address, phone, category
3. **OpenAI Generation**: Celery task `generate_store_content` calls OpenAI to produce: store description, menu stubs, SEO meta tags — in target locale (Hebrew/English)
4. **Micro-Frontend Provision**: Postgres record created with `status: "shadow"` — public frontend renders stub store page at `/store/{slug}`
5. **Odin Onboarding Trigger**: HTTP POST to `https://tazo-app.com/api/v1/shadow/onboard` with merchant data + requester phone — Odin dispatches WhatsApp notification to merchant via Tazo Sync
6. **User Notification**: WebSocket push OR return `store_slug` to frontend immediately — user sees "דף עסק נוצר, ממתין לאישור הבעלים"

```python
# Correct: Shadow Store pipeline dispatch
@router.post("/api/v1/shadow/provision")
async def provision_shadow_store(
    payload: ShadowProvisionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    existing = await get_merchant_by_place_id(db, payload.place_data.place_id)
    if existing:
        return {"store_slug": existing.slug, "status": "existing"}
    
    # Create shadow record synchronously (return fast)
    shadow = await create_shadow_merchant(db, payload.place_data)
    
    # All enrichment is async via Celery
    enrich_merchant_data.delay(shadow.id, payload.place_data.dict())
    background_tasks.add_task(notify_odin_onboarding, shadow.id, payload.requester_phone)
    
    return {"store_slug": shadow.slug, "status": "shadow_created"}
```

---

## Celery Rules

- All tasks in `backend/services/tasks.py` — never define tasks inline in route handlers
- Tasks must be idempotent — check for duplicate execution via Redis key before processing
- Beat schedule defined in `backend/core/celery_app.py` — no dynamic schedule changes at runtime
- Task timeouts: enrichment tasks max 30s, OpenAI generation max 60s
- Dead-letter: failed tasks after 3 retries logged to Postgres `task_failures` table

```python
# Correct: Celery task with idempotency
@celery_app.task(bind=True, max_retries=3, soft_time_limit=30)
def enrich_merchant_data(self, merchant_id: str, place_data: dict):
    lock_key = f"enriching:{merchant_id}"
    if redis_client.set(lock_key, "1", ex=120, nx=True) is None:
        return  # Already processing
    try:
        # ... Apify call
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
    finally:
        redis_client.delete(lock_key)
```

---

## Frontend Rules (3 Apps)

- `frontend-public`: Landing pages + Shadow Store stub pages. Zero business jargon. One CTA per screen. Trust Center at `/faq` — FAQs and 30 business scenarios live ONLY here.
- `frontend-customer`: Authenticated consumer marketplace. Search, cart, order tracking.
- `frontend-admin`: Merchant and platform admin dashboard. Full data management.
- Each app builds independently — no shared `dist/` output
- TypeScript strict mode — no `any`
- Inline styles acceptable for Shadow Store dynamic components (server-generated slugs)

---

## Security Mandates

- **CORS**: `frontend-admin` origin, `frontend-customer` origin, `frontend-public` origin — explicit allowlist only. Never `*`.
- **OpenAI key**: `OPENAI_API_KEY` from environment. Never in source. Never returned in any API response.
- **Apify token**: `APIFY_API_TOKEN` from environment. Apify actor calls fire-and-forget via Celery — never in request path.
- **Shadow Store abuse**: `/api/v1/shadow/provision` rate-limited at 1 req/10s per IP — prevent mass fake merchant generation.
- **Merchant data validation**: All Apify-returned data sanitized before DB insert — strip HTML, validate phone format, truncate fields to schema limits.
- **PostgreSQL port 5433**: Never exposed outside Docker network. Bind to `127.0.0.1` only in compose.

---

## API Design Rules

- All routes under `/api/v1/`
- Multi-origin CORS configured once in `backend/core/config.py` — not per-router
- Pydantic v2 models for all request/response shapes
- OpenAI calls always have `max_tokens` set — never unbounded generation
- Async DB sessions via `AsyncSession` — never synchronous SQLAlchemy in route handlers

---

## Banned Patterns

- UX explanation text on landing pages — move to `/faq`
- Synchronous `requests` library calls — use `httpx.AsyncClient`
- OpenAI API key in frontend bundle (even as env var in Vite `VITE_*` prefix — it gets embedded in JS)
- Hardcoded Apify actor IDs — store in `settings.APIFY_ACTOR_ID`
- Shadow Store provision called without rate-limit guard
- Merchant `status: "shadow"` pages indexed by search engines — add `<meta name="robots" content="noindex">` until merchant confirms
- `any` TypeScript type in any frontend app
