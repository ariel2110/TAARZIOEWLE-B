
# PROVISIONING RULES

## Purpose
Define how the public request-demo flow should create or reuse records.

## Rules in v17
1. If matching lead and business already exist, reuse them.
2. If a customer account already exists for the phone, reuse it.
3. If only lead exists, attach/create business instead of duplicating lead.
4. If only business exists, attach/create lead instead of duplicating business.
5. Only create new records when a meaningful existing match is not found.

## Matching rules (basic)
- phone exact match
- business name + city exact match

## Future improvements
- fuzzy name matching
- normalized phone matching
- stronger website/domain dedup
- persisted provisioning decision logs
