# DELIVERY PROVIDER INTEGRATION LAYER

## Purpose
Define a clean abstraction for OTP and magic-link delivery so providers can be swapped without rewriting business logic.

## Core idea
Challenge creation and challenge delivery remain separate.

## Layers
1. Challenge service creates the OTP or magic-link token
2. Delivery router chooses a provider
3. Provider sends or simulates delivery
4. Attempt is logged for audit and monitoring

## Supported starter providers
- preview_provider
- console_provider

## Future providers
- sms_provider
- email_provider
- whatsapp_provider (only if policy allows)
