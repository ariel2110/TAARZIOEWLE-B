# Abuse Scoring Spec

Abuse/suspicion scoring is a lightweight heuristic layer.

## Inputs
- repeated login failures
- blocked logins
- rate limit hits
- failed/rate-limited delivery attempts

## Output
- suspicion_score
- suspicion_tier: low / medium / high

## Use
- admin monitoring
- CEO alerts later
- future hardening and lockout policies
