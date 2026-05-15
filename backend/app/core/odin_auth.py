"""
Odin SSO token decoder.
Stub: raises until Odin JWT public key is configured.
The caller in deps.py wraps this in try/except, so raising is safe.
"""
from __future__ import annotations


def _decode_odin_token(token: str) -> dict:
    """Decode an Odin SSO JWT. Raises ValueError until Odin signing key is wired."""
    raise ValueError("Odin SSO not yet configured on this service")
