"""
Odin SSO token decoder.
Decodes RS256 JWTs issued by the Odin/AORDIIENL auth server.
Requires ODIN_JWT_PUBLIC_KEY env var (RS256 PEM public key).
"""
from __future__ import annotations

from jose import JWTError, jwt


def _decode_odin_token(token: str) -> dict:
    """Decode an Odin SSO JWT (RS256). Raises ValueError on failure."""
    from app.core.config import settings  # local import to avoid circular

    if not settings.odin_jwt_public_key:
        raise ValueError("Odin SSO not configured: set ODIN_JWT_PUBLIC_KEY")
    try:
        return jwt.decode(
            token,
            settings.odin_jwt_public_key,
            algorithms=["RS256"],
        )
    except JWTError as exc:
        raise ValueError(f"Invalid Odin token: {exc}") from exc
