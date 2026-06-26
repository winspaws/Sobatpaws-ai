"""Autentikasi API key + JWT untuk integrasi app vet, admin panel, & mobile apps.

Header: X-EkosistemSatwa-Key: <key> atau Authorization: Bearer <token> atau cookie access_token

Bila kunci tidak dikonfigurasi di environment, auth dinonaktifkan (mode dev).
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# =============================================================================
# JWT Configuration
# =============================================================================

JWT_SECRET = os.getenv("EKOSISTEM_SATWA_JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("EKOSISTEM_SATWA_JWT_EXPIRY_HOURS", "24"))

security = HTTPBearer(auto_error=False)


def create_jwt_token(user_id: int, role: str = "admin") -> str:
    """Create a JWT token for admin panel integration."""
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def extract_token(
    authorization: HTTPAuthorizationCredentials | None = Depends(security),
    x_ekosistem_satwa_key: str | None = Header(None, alias="X-EkosistemSatwa-Key"),
    access_token: str | None = Cookie(None, alias="access_token"),
) -> str | None:
    """Extract token from multiple sources: Bearer header, API key header, or cookie."""
    if authorization:
        return authorization.credentials
    if x_ekosistem_satwa_key:
        return x_ekosistem_satwa_key.strip()
    if access_token:
        return access_token
    return None


def require_jwt_or_apikey(
    token: str | None = Depends(extract_token),
) -> dict:
    """Accept either JWT (from admin panel) or API key (from vet apps)."""
    if not token:
        raise HTTPException(401, "Authentication required")

    # Try JWT first
    payload = decode_jwt_token(token)
    if payload:
        return {"auth_method": "jwt", "user_id": payload["user_id"], "role": payload["role"]}

    # Fall back to API key
    role = resolve_role(token)
    if role == ClientRole.public:
        raise HTTPException(401, "Invalid API key or expired JWT token")

    return {"auth_method": "apikey", "role": role.value, "authenticated": True}


def create_jwt_response(user_id: int, role: str = "admin") -> dict:
    """Create login response with JWT token."""
    token = create_jwt_token(user_id, role)
    return {
        "success": True,
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRY_HOURS * 3600,
        }
    }


# =============================================================================
#  API Key Auth (existing)
# =============================================================================


class ClientRole(str, Enum):
    public = "public"
    vet = "vet"
    admin = "admin"


def _keys() -> tuple[str, str]:
    return (
        os.getenv("EKOSISTEM_SATWA_VET_API_KEY", "").strip(),
        os.getenv("EKOSISTEM_SATWA_ADMIN_API_KEY", "").strip(),
    )


def extract_api_key(
    x_ekosistem_satwa_key: str | None = Header(None, alias="X-EkosistemSatwa-Key"),
    authorization: str | None = Header(None),
) -> str | None:
    if x_ekosistem_satwa_key:
        return x_ekosistem_satwa_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def resolve_role(key: str | None) -> ClientRole:
    vet_key, admin_key = _keys()
    if not vet_key and not admin_key:
        return ClientRole.public
    if not key:
        return ClientRole.public
    if admin_key and key == admin_key:
        return ClientRole.admin
    if vet_key and key == vet_key:
        return ClientRole.vet
    return ClientRole.public


def auth_status() -> dict:
    vet_key, admin_key = _keys()
    return {
        "enabled": bool(vet_key or admin_key),
        "vet_key_configured": bool(vet_key),
        "admin_key_configured": bool(admin_key),
        "header": "X-EkosistemSatwa-Key",
        "alt_header": "Authorization: Bearer <token>",
        "jwt_enabled": True,
    }


def require_vet(
    x_ekosistem_satwa_key: str | None = Header(None, alias="X-EkosistemSatwa-Key"),
    authorization: str | None = Header(None),
) -> ClientRole:
    """Wajib kunci vet bila EKOSISTEM_SATWA_VET_API_KEY diset."""
    vet_key, _ = _keys()
    key = extract_api_key(x_ekosistem_satwa_key, authorization)
    role = resolve_role(key)
    if vet_key and role not in (ClientRole.vet, ClientRole.admin):
        raise HTTPException(401, "API key vet/admin diperlukan (header X-EkosistemSatwa-Key).")
    return role


def require_admin(
    x_ekosistem_satwa_key: str | None = Header(None, alias="X-EkosistemSatwa-Key"),
    authorization: str | None = Header(None),
) -> ClientRole:
    """Wajib kunci admin bila EKOSISTEM_SATWA_ADMIN_API_KEY diset."""
    _, admin_key = _keys()
    key = extract_api_key(x_ekosistem_satwa_key, authorization)
    role = resolve_role(key)
    if admin_key and role != ClientRole.admin:
        raise HTTPException(403, "API key admin diperlukan untuk endpoint ini.")
    return role


def optional_client(request: Request) -> dict:
    key = extract_api_key(
        request.headers.get("X-EkosistemSatwa-Key"),
        request.headers.get("Authorization"),
    )
    role = resolve_role(key)
    return {"role": role.value, "authenticated": role != ClientRole.public}
