# FIELD LEVEL VISIBILITY RULES

## Purpose
Define which fields are visible to:
- admin
- customer
- CEO agent

## Customer-visible examples
- contact_name
- phone
- email
- package_name
- linked site ids/links
- own change requests
- own support messages
- own payment summaries

## Admin-only examples
- internal notes
- approval rationale internals
- full recommendation history
- internal lead scoring notes
- other customers

## CEO-agent internal visibility
The CEO agent may inspect customer-linked operational context for support, activation, churn-risk, and recommendation purposes, but must not expose cross-customer internal data to customers.
