"""Authentication middleware for Microsoft Entra ID token validation."""

import logging
import time
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application import get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

_jwks_cache: dict[str, Any] = {}
_jwks_cache_timestamp: float = 0.0
_JWKS_CACHE_TTL_SECONDS: float = 86400.0  # 24 hours


async def _get_signing_keys(tenant_id: str) -> dict[str, Any]:
    """Fetch and cache JWKS from Microsoft Entra ID."""
    global _jwks_cache_timestamp

    now = time.monotonic()
    if (
        _jwks_cache.get("keys")
        and (now - _jwks_cache_timestamp) < _JWKS_CACHE_TTL_SECONDS
    ):
        return _jwks_cache

    jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        jwks_data = response.json()

    _jwks_cache.clear()
    _jwks_cache.update(jwks_data)
    _jwks_cache_timestamp = now
    return jwks_data


async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate bearer token from Microsoft Entra ID.

    Returns the decoded token claims on success.
    Raises HTTPException(401) on invalid/missing token.
    """
    settings = get_settings()
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token header missing key ID",
            )

        jwks_data = await _get_signing_keys(settings.azure_tenant_id)

        signing_key = None
        for key in jwks_data.get("keys", []):
            if key["kid"] == kid:
                signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break

        if not signing_key:
            _jwks_cache.clear()
            global _jwks_cache_timestamp
            _jwks_cache_timestamp = 0.0
            jwks_data = await _get_signing_keys(settings.azure_tenant_id)
            for key in jwks_data.get("keys", []):
                if key["kid"] == kid:
                    signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break

        if not signing_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find matching signing key",
            )

        issuer = f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0"
        valid_audiences = [
            settings.azure_client_id,
            f"api://{settings.azure_client_id}",
        ]
        # Accept both v1 and v2 issuer formats
        valid_issuers = [
            f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0",
            f"https://sts.windows.net/{settings.azure_tenant_id}/",
        ]
        # Decode without issuer check first, then validate manually
        claims = jwt.decode(
            token,
            key=signing_key,
            algorithms=["RS256"],
            audience=valid_audiences,
            options={"require": ["exp", "aud", "sub"], "verify_iss": False},
        )
        token_issuer = claims.get("iss", "")
        if token_issuer not in valid_issuers:
            logger.warning("Invalid issuer: %s (expected one of %s)", token_issuer, valid_issuers)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid issuer: {token_issuer}",
            )
        return claims

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Token validation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


async def get_current_user(
    request: Request,
    claims: dict = Depends(validate_token),
) -> dict:
    """Extract current user info from validated token claims."""
    return {
        "oid": claims.get("oid", ""),
        "preferred_username": claims.get("preferred_username", ""),
        "name": claims.get("name", ""),
        "sub": claims.get("sub", ""),
    }
