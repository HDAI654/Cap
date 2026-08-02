import logging
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.conf import Config
from src.exceptions import ForbiddenError, UnauthorizedError

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT using the Auth service public key."""
    public_key = Config.AUTH_PUBLIC_KEY
    if not public_key:
        raise UnauthorizedError("AUTH_PUBLIC_KEY is not configured.")

    try:
        return jwt.decode(
            token,
            public_key,
            algorithms=[Config.AUTH_JWT_ALGORITHM],
            options={"require": ["exp", "role"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid token.") from exc


def require_admin(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer),
    ],
) -> dict[str, Any]:
    """FastAPI dependency: valid JWT with role == ADMIN."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_access_token(credentials.credentials)
    except UnauthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    role = claims.get("role")
    if role != Config.AUTH_ADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return claims


AdminClaims = Annotated[dict[str, Any], Depends(require_admin)]
