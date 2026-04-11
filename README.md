# LocalBiz AutoSite Platform — v20

Version: v20


v7 focuses on **real infrastructure foundations**.

What is stronger in v7:
- PostgreSQL-first config with SQLite fallback for quick dev
- Alembic starter wired more realistically
- initial real migration file
- JWT auth skeleton + dev login
- Docker Compose for Postgres + backend
- Makefile for common commands
- clearer local/VPS startup guidance

## Recommended way to start
1. Read `PROJECT_BLUEPRINT.md`
2. Read `PHASE_HANDOFF.md`
3. Read `docs/RELEASE_NOTES_V7.md`
4. Read `docs/START_IN_VSCODE.md`
5. Use `prompts/20_v7_infrastructure.md`

## Quick local path
### Option A — Docker
```bash
make up
```

### Option B — local backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.db.seed_cli
uvicorn app.main:app --reload
```

## Dev auth
Use either:
- `POST /api/v1/auth/dev-login` to get a bearer token
- or legacy headers for quick development

## Frontend admin
```bash
cd frontend-admin
npm install
npm run dev
```

## V8 Highlights
- queue APIs and routed admin UI
- approval actions with activity logs
- targeting console starter
- CEO Console starter


## v10
Use prompts/23_v10_actions_campaigns.md to continue from the current package.


## V11 customer access
- Admin can create customer accounts linked to a business and site
- Customer login is phone-based with a unique temporary password
- First login requires password change
- Customer portal remains intentionally limited and privacy-first


## V12 highlights
- customer portal depth
- customer edit submissions
- change requests
- support messages
- customer timeline
- admin customer ops visibility


## V13 focus
- Public landing page and intake preview
- Admin identity set to Ariel / ar.2110@gmail.com
- Customer and admin entry points
- Demo limit concept: up to 2 demo sites per month


## Public entry app
A new `frontend-public` starter is included for the homepage/public entry flow.


## V15 quick note
This version improves the public homepage and onboarding experience, including a richer readiness check and demo-availability preview by customer phone.


## V16
Public onboarding now connects readiness preview to a real request-demo provisioning flow that can create a lead, business, and customer account with a unique temporary password.


## v17 note
This version adds safer public request-demo provisioning with basic deduplication, reuse of existing records where possible, and onboarding state hints for the public-to-customer handoff.


## V18
- Added demo request persistence, admin visibility, and lightweight provisioning audit trail.


## V19
Adds package-aware demo limits, provisioning decision logs, and better public/admin status visibility.


## V20
Adds package metadata from the database, persisted onboarding sessions, public/admin compare views, and magic-link foundation for customer access.


## V21 notes
V21 adds a stronger public/customer access foundation with login challenges, onboarding transition guards, and richer package metadata.


## v22 highlight
This version adds starter hardening for public onboarding and customer access: rate limiting, login delivery abstraction, and package-aware challenge gating.


## Current starter version
This repo snapshot includes v24 security monitoring and abuse scoring foundations.


V25 highlights: security alerts, lockout policy summary, richer admin monitoring.


V26 highlights: workflow guards and approval apply flow.


V27 highlights: package field permissions and customer billing visibility starter.
