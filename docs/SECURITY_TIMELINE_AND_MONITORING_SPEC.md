# Security Timeline and Monitoring Spec

This document defines the security monitoring layer for public onboarding and customer access.

## Goals
- show login/onboarding/delivery/rate-limit activity in one timeline
- surface suspicious phones/accounts
- give admin a control-room view into access problems

## Timeline Sources
- customer_login_events
- login_challenges
- login_delivery_attempts
- rate_limit_events
- onboarding_sessions
- demo_request_logs

## Core Views
- summary
- timeline
- suspicion watchlist
