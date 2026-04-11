Use the current v7 repository as the baseline.

Goal:
Strengthen the real infrastructure foundations before adding many more product features.

Focus areas:
1. PostgreSQL-first consistency
2. Alembic migration correctness
3. auth flow cleanup
4. settings/config cleanup
5. backend startup consistency
6. basic frontend auth wiring if useful
7. remove leftover create_all assumptions over time

Before coding:
1. review current infra architecture
2. identify weak infra areas
3. propose a safe cleanup plan
4. list affected files

Then implement improvements incrementally and safely.
