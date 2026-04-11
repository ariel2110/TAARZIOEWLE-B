# RELEASE NOTES V9

## Highlights
- Added Feedback Intelligence layer
- Added feedback storage, analysis, and CEO-style response stubs
- Added feedback queue support
- Added admin Feedback page
- Added governance spec for feedback and change intelligence
- Prepared the system for future natural-language site/change requests routed through CEO/approval logic

## Major Additions
- backend model: feedback_items
- backend service: feedback_service
- backend routes: /admin/feedback and /admin/feedback/{id}/analyze
- frontend-admin page: Feedback
- queue summary: feedback_review

## Notes
- Feedback analysis in v9 is heuristic/stub logic, not full multi-model intelligence yet.
- Broad changes still require approval.
- This version is designed to make it easy to capture feedback everywhere and turn it into structured work.
