# RELEASE NOTES — V28

**תאריך:** אפריל 2026  
**Branch:** main  
**Commits:** 5d2bb00 → HEAD

---

## סיכום גרסה

גרסה זו כוללת סבב תיקוני אבטחה מקיף (QA Report), אינטגרציית Facebook Graph API מלאה, רענון אוטומטי של טוקן כל 50 יום, ועדכונים לדאשבורד הניהולי.

---

## 🔒 תיקוני אבטחה (QA Report)

### תוקן ✅

| # | תיאור | קובץ |
|---|--------|------|
| 1 | `USE_POSTGRES=true` — הפעלת PostgreSQL ב-production | `backend/.env` |
| 2 | `internal_whatsapp.py` — החלפת auth מ-query param ל-JWT (`Depends(get_current_admin)`) | `routes/internal_whatsapp.py` |
| 3 | Evolution settings — קריאה מ-`settings` בזמן ריצה (לא ב-import time) | `routes/internal_whatsapp.py` |
| 4 | הסרת `X-Forwarded-For` מ-CORS `allow_headers` (מניעת IP spoofing) | `app/main.py` |
| 5 | `GET /consume-magic-link` → `POST` (מניעת prefetch browsers) | `routes/public_portal.py` |
| 6 | קוד unreachable ב-`_draft_html_path()` תוקן ל-if/else | `routes/public_sites.py` |
| 7 | `health.py` — `db.close()` עטוף ב-try/except (מניעת NameError) | `routes/health.py` |
| 8 | `.env` הוסר מ-git tracking | `.gitignore` |

### ממצאים פתוחים (דורשים פעולה)

| # | תיאור | עדיפות |
|---|--------|--------|
| 6 | `/public/build-instant` — חסר rate limiting | 🟠 |
| 9 | `HOSTINGER_API_TOKEN=your_token_here` — placeholder | 🟠 |
| 10 | `docker-compose.yml` — `POSTGRES_PASSWORD: localbiz` hardcoded | 🟡 |
| 12 | `admin_api_keys.py` — `_ENV_FILE` path שביר | 🟡 |
| 13 | `hmac.new()` — deprecated, להחליף ב-`hmac.HMAC()` | 🟡 |
| 14 | `admin_customers.py` — N+1 queries ב-`_row_to_dict()` | 🟡 |

---

## 📘 Facebook Graph API — אינטגרציה מלאה

### תכונות חדשות

**1. Facebook Stats Card** (`AgentsDashboard.tsx`)
- מציג שם עמוד, עוקבים, ולייקים
- ניהול מצבים: `active` / `no_token` / `token_expired` / `error`
- Fallback אוטומטי: `followers_count` → `fan_count` אם חסר
- קישורים ישירים לכלי Facebook Developers בעת תפוגת טוקן

**2. חיפוש עמוד אוטומטי** (`admin_social.py`)
- קורא ראשית ל-`/me/accounts` — עובד עם User Access Token ו-Page Access Token כאחד
- אין תלות בסוג הטוקן — מגיע לנכון בכל מקרה
- שדות: `name, fan_count, followers_count`

**3. רענון אוטומטי כל 50 יום** (`tasks.py` + `celery_app.py`)
- Celery Beat task: `facebook_token_refresh_task`
- קורא ל-`GET /v19.0/oauth/access_token?grant_type=fb_exchange_token`
- שומר טוקן חדש ב-`.env` אוטומטית
- שולח WhatsApp (Evolution) לבעלים בהצלחה ובכישלון
- Retry: 2 ניסיונות, 10 דקות המתנה בין ניסיונות
- הטוקן **לעולם לא נכתב ל-logs**

**4. Manual Trigger** (`admin_social.py`)
- `POST /api/v1/admin/social/facebook-refresh-token`
- כפתור "🔄 חדש טוקן עכשיו" בדאשבורד
- מחזיר `task_id` למעקב

### קישורי עזר (בדאשבורד)

| כלי | שימוש |
|-----|-------|
| [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken) | הארכת טוקן ל-60 יום |
| [Graph API Explorer](https://developers.facebook.com/tools/explorer) | הפקת טוקן חדש |
| [My Apps](https://developers.facebook.com/apps) | App ID + App Secret |

### הגדרה נדרשת (`.env`)

```
FACEBOOK_ACCESS_TOKEN=<long-lived token>
FACEBOOK_APP_ID=<app id>           # נדרש לרענון אוטומטי
FACEBOOK_APP_SECRET=<app secret>   # נדרש לרענון אוטומטי
```

---

## ⚙️ שינויי תשתית

- **PostgreSQL port**: 5433 (במקום 5432 כדי למנוע התנגשות עם `alpha-genesis-db`)
- **Alembic chain**: תוקן `0003_add_foreign_keys.py` down_revision
- **Redis port**: 6379 (default)
- **Celery Beat schedules**:
  - `followup-daily` — 24 שעות
  - `ceo-digest-every-6h` — 6 שעות
  - `facebook-token-refresh-every-50-days` — 50 יום

---

## 📁 קבצים שהשתנו

```
backend/app/main.py
backend/app/core/config.py
backend/app/core/celery_app.py
backend/app/api/v1/routes/admin_social.py
backend/app/api/v1/routes/admin_api_keys.py
backend/app/api/v1/routes/internal_whatsapp.py
backend/app/api/v1/routes/public_portal.py
backend/app/api/v1/routes/public_sites.py
backend/app/api/v1/routes/health.py
backend/app/tasks.py
backend/.env.example
frontend-admin/src/pages/AgentsDashboard.tsx
frontend-admin/src/services/queries.ts
```
