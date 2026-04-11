# RELEASE NOTES — v7

## Focus
v7 is about making the repo feel more like a real project foundation rather than only a smart starter.

## Added / improved
- PostgreSQL-first config path
- Docker Compose for postgres + backend
- backend Dockerfile
- JWT auth skeleton and `/auth/dev-login`
- improved auth dependency logic
- Alembic wired to effective database URL
- initial real schema migration
- Makefile for common tasks
- local setup helper script

## Still intentionally limited
- Google auth is still a skeleton
- frontend routing/UI is still starter-level
- approval workflow is still basic
- PostgreSQL is prepared strongly, but some code paths are still MVP/simple
