# FEEDBACK AND CHANGE INTELLIGENCE SPEC

## Purpose
This document defines the platform feedback layer.

The goal is to let the admin or customer provide fast structured feedback and open natural-language feedback on:
- generated draft sites
- outreach messages
- targeting/campaign choices
- CEO recommendations
- dashboard outputs
- customer-facing sites later on

The system should translate feedback into:
- a clear interpretation
- a suggested next action
- a scope decision (item/category/campaign/system)
- a memory or preference candidate when relevant
- an approval-needed item when relevant

---

## Core UX Pattern
Each important object may expose a feedback block with:
- Good as-is
- Needs improvement
- Not a fit / needs deeper change
- Open text feedback

The user may also write free-form instructions.

---

## Feedback Flow
1. User selects one of three quick options and/or writes open feedback.
2. Feedback is stored with target type/id and context.
3. CEO Feedback Intelligence analyzes the feedback.
4. The system returns:
   - what it understood
   - classification/category
   - proposed next action
   - whether it should apply only to this item or more broadly
5. If relevant, a recommendation or approval item may be created.
6. Feedback and outcome remain auditable.

---

## Three Quick Options
- good_as_is
- needs_improvement
- not_a_fit

These are intentionally simple and fast.

---

## Open Feedback Examples
- "האתר הזה יפה אבל נשמע גנרי מדי"
- "בפעם הבאה במוסכים תדגיש יותר טלפון ומיקום"
- "ההודעה הזו אגרסיבית מדי"
- "אל תבנה יותר טיוטות בלי תמונה ראשית"
- "המלצת המנכ״ל לא מספיק ברורה"

---

## Feedback Targets
Feedback may attach to:
- draft_site
- outreach_message
- targeting_profile
- campaign
- recommendation
- ceo_report
- business
- lead
- system_general

---

## Scope Decisions
The analysis layer should classify whether feedback applies to:
- item_only
- category_level
- campaign_level
- city_or_radius_segment
- template_level
- prompt_level
- system_level

---

## Expected AI/CEO Response
The system should answer with:
- understanding summary
- detected feedback category
- suggested next action
- suggested scope
- whether approval is needed
- whether it looks like a reusable preference

---

## Preference Capture
If feedback appears to express a repeated preference, the system may suggest saving it as:
- personal admin preference
- category preference
- campaign preference
- system policy candidate

---

## Safety Rules
Feedback should never directly apply major production changes without approval.
Small item-scoped changes may be prepared automatically, but broad or risky changes should enter recommendation/approval flows.

---

## MVP Scope
For MVP, support:
- feedback on draft sites
- feedback on CEO recommendations/reports
- feedback on outreach messages
- quick feedback + open text
- CEO interpretation response
- recommendation/approval candidate generation
