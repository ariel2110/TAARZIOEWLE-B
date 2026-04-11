# ARCHITECTURE

## Core stack
- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- Admin frontend: React
- Customer frontend: React
- Static site generation: template-based HTML rendering

## Major backend domains
- auth
- businesses
- draft_sites
- generator
- communications
- payments
- customer
- leads
- analytics
- insights
- llm
- ceo_agent

## Guiding rules
- thin API routes
- business logic in services
- provenance-aware data
- explicit status transitions
- auditable automation
- provider-agnostic LLM routing
