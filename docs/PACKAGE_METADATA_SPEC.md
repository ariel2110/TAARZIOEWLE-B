
# PACKAGE METADATA SPEC

## Purpose
Define package metadata separately from hardcoded policy logic.

## Current package metadata fields
- name
- monthly_demo_limit
- description
- is_default
- is_active

## Why this matters
Package rules such as demo limits should not stay hardcoded in services.
The system should eventually derive these from package/business/subscription configuration.

## MVP/V20 scope
In V20 package metadata is stored in `package_plans` and used by the public onboarding flow.

## Future expansion
Later package metadata may also include:
- portal permissions
- editable field limits
- support SLA flags
- feature toggles
- billing linkage
