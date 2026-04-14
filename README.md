# SiteNest Platform — v28

> **פלטפורמת SaaS ישראלית** לבניית אתרי עסקים קטנים אוטומטית, עם AI, WhatsApp, ותשלומים.

---

## 🏗️ ארכיטקטורה כללית

```
┌─────────────────────────────────────────────────────┐
│  frontend-admin    (React + Vite) — admin.sitenest.site  │
│  frontend-public   (React + Vite) — sitenest.site        │
│  frontend-customer (React + Vite) — app.sitenest.site    │
├─────────────────────────────────────────────────────┤
│  backend           (FastAPI + SQLAlchemy)            │
│  └─ port 8765 — Uvicorn (2 workers)                 │
├─────────────────────────────────────────────────────┤
│  PostgreSQL        (Docker — port 5433)             │
│  Redis             (port 6379)                      │
│  Celery Worker     (Docker — queue: sitenest)       │
│  Evolution API     (Docker — port 8181, WhatsApp)   │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 הפעלה מהירה (VPS / Production)

```bash
# 1. שירות backend
systemctl start sitenest-backend

# 2. PostgreSQL + Celery + Evolution (Docker Compose)
docker compose up -d

# 3. בדיקת בריאות
curl https://api.sitenest.site/health
```

---

## 💻 הפעלה מקומית (פיתוח)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # מלא את המשתנים
alembic upgrade head
uvicorn app.main:app --reload --port 8765

# Frontend Admin
cd frontend-admin
npm install && npm run dev   # http://localhost:5173

# Frontend Public
cd frontend-public
npm install && npm run dev   # http://localhost:5174
```

---

## 🔑 משתני סביבה חיוניים (`.env`)

| משתנה | תיאור |
|-------|-------|
| `USE_POSTGRES` | `true` ב-production |
| `POSTGRES_HOST/PORT/DB/USER/PASSWORD` | PostgreSQL credentials |
| `JWT_SECRET_KEY` | מפתח חתימת JWT |
| `ADMIN_DEV_TOKEN` | טוקן פיתוח (לא זמין ב-production) |
| `OPENAI_API_KEY` | GPT-4o — כתיבת תוכן |
| `ANTHROPIC_API_KEY` | Claude — ארכיטקטורת אתר |
| `GEMINI_API_KEY` | Gemini — סינון לידים |
| `XAI_API_KEY` | Grok — ניהול מכירות WhatsApp |
| `EVOLUTION_API_URL/KEY/INSTANCE` | WhatsApp gateway |
| `MORNING_API_KEY/SECRET` | תשלומים (Morning/GreenInvoice) |
| `FACEBOOK_ACCESS_TOKEN` | טוקן עמוד פייסבוק (long-lived) |
| `FACEBOOK_APP_ID/SECRET` | לרענון אוטומטי כל 50 יום |
| `GOOGLE_PLACES_API_KEY` | Google Places — לידים |
| `HOSTINGER_API_TOKEN` | רכישת דומיינים אוטומטית |

---

## 📋 נתיבי API עיקריים

### Public (ללא auth)
| Method | Path | תיאור |
|--------|------|-------|
| POST | `/api/v1/public/build-instant` | יצירת ליד + site scope |
| GET | `/api/v1/public/places-autocomplete` | חיפוש עסקים |
| POST | `/api/v1/public/request-magic-link` | שליחת magic link |
| POST | `/api/v1/public/consume-magic-link` | מימוש magic link |

### Admin (JWT required)
| Method | Path | תיאור |
|--------|------|-------|
| GET | `/api/v1/admin/analytics/*` | CEO Analytics Dashboard |
| GET | `/api/v1/admin/social/facebook-stats` | סטטיסטיקת פייסבוק |
| POST | `/api/v1/admin/social/facebook-refresh-token` | רענון טוקן ידני |
| GET/POST | `/api/v1/admin/api-keys` | ניהול מפתחות API |
| GET | `/api/v1/internal/whatsapp-qr` | QR לחיבור WhatsApp |
| POST | `/api/v1/internal/approve-message/{token}` | אישור הודעת WhatsApp |

### Webhooks
| Method | Path | תיאור |
|--------|------|-------|
| POST | `/api/v1/webhooks/morning` | תשלום מאושר ← Morning |
| POST | `/api/v1/webhooks/whatsapp` | עדכוני delivery ← WhatsApp |

---

## 🤖 Celery Tasks

| Task | תזמון | תיאור |
|------|-------|-------|
| `followup_task` | כל 24 שעות | מעקב לידים וחידוש |
| `ceo_digest_task` | כל 6 שעות | דוח CEO |
| `facebook_token_refresh_task` | כל 50 יום | רענון טוקן פייסבוק אוטומטי |

---

## 🔒 אבטחה

- **Auth**: JWT Bearer tokens (httponly, exp: 720 min)
- **Admin routes**: `Depends(get_current_admin)` על כל route ניהולי
- **Webhooks**: HMAC-SHA256 signature verification
- **CORS**: origins מוגדרים, ללא `X-Forwarded-For`
- **Magic links**: POST בלבד (מניעת browser prefetch)
- **Secrets**: `.env` לא ב-git, `ADMIN_DEV_TOKEN` מושבת ב-production

---

## 📁 מבנה הפרויקט

```
site-nest-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/      # FastAPI endpoints
│   │   ├── core/               # config, security, celery
│   │   ├── models/             # SQLAlchemy models
│   │   ├── services/           # business logic
│   │   └── tasks.py            # Celery tasks
│   ├── alembic/                # DB migrations
│   └── .env.example
├── frontend-admin/             # React admin dashboard
├── frontend-public/            # React public landing
├── frontend-customer/          # React customer portal
├── docs/                       # ספציפיקציות + release notes
├── docker-compose.yml
└── Makefile
```

---

## 📄 תיעוד נוסף

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — ארכיטקטורת מלאה
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — הוראות deployment
- [`docs/SECURITY.md`](docs/SECURITY.md) — מדיניות אבטחה
- [`docs/RELEASE_NOTES_V28.md`](docs/RELEASE_NOTES_V28.md) — שינויים אחרונים
- [`PROJECT_BLUEPRINT.md`](PROJECT_BLUEPRINT.md) — vision & roadmap
- [`PHASE_HANDOFF.md`](PHASE_HANDOFF.md) — handoff בין שלבי פיתוח

---

## גרסה נוכחית

**v28** | אפריל 2026 | commit `HEAD` | branch `main`
