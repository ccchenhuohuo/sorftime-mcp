from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastmcp.server.auth.providers.jwt import JWTVerifier

from sorftime_mcp.config import Settings


def create_auth_provider(settings: Settings) -> JWTVerifier:
    return JWTVerifier(
        public_key=settings.jwt_secret,
        issuer=settings.sorftime_mcp_issuer,
        audience=settings.sorftime_mcp_audience,
        algorithm="HS256",
    )


def issue_token(*, settings: Settings, user: str, expires_days: int) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user,
        "iss": settings.sorftime_mcp_issuer,
        "aud": settings.sorftime_mcp_audience,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(days=expires_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

