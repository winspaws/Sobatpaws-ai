"""Autentikasi API key untuk integrasi app vet & dashboard admin.

Header: `X-Sobatpaws-Key: <key>` atau `Authorization: Bearer <key>`

Bila kunci tidak dikonfigurasi di environment, auth dinonaktifkan (mode dev).
"""
from __future__ import annotations

import os
from enum import Enum

from fastapi import Header, HTTPException, Request


class ClientRole(str, Enum):
    public = "public"
    vet = "vet"
    admin = "admin"


def _keys() -> tuple[str, str]:
    return (
        os.getenv("SOBATPAWS_VET_API_KEY", "").strip(),
        os.getenv("SOBATPAWS_ADMIN_API_KEY", "").strip(),
    )


def extract_api_key(
    x_sobatpaws_key: str | None = Header(None, alias="X-Sobatpaws-Key"),
    authorization: str | None = Header(None),
) -> str | None:
    if x_sobatpaws_key:
        return x_sobatpaws_key.strip()
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
        "header": "X-Sobatpaws-Key",
        "alt_header": "Authorization: Bearer <key>",
    }


def require_vet(
    x_sobatpaws_key: str | None = Header(None, alias="X-Sobatpaws-Key"),
    authorization: str | None = Header(None),
) -> ClientRole:
    """Wajib kunci vet bila SOBATPAWS_VET_API_KEY diset."""
    vet_key, _ = _keys()
    key = extract_api_key(x_sobatpaws_key, authorization)
    role = resolve_role(key)
    if vet_key and role not in (ClientRole.vet, ClientRole.admin):
        raise HTTPException(401, "API key vet/admin diperlukan (header X-Sobatpaws-Key).")
    return role


def require_admin(
    x_sobatpaws_key: str | None = Header(None, alias="X-Sobatpaws-Key"),
    authorization: str | None = Header(None),
) -> ClientRole:
    """Wajib kunci admin bila SOBATPAWS_ADMIN_API_KEY diset."""
    _, admin_key = _keys()
    key = extract_api_key(x_sobatpaws_key, authorization)
    role = resolve_role(key)
    if admin_key and role != ClientRole.admin:
        raise HTTPException(403, "API key admin diperlukan untuk endpoint ini.")
    return role


def optional_client(request: Request) -> dict:
    key = extract_api_key(
        request.headers.get("X-Sobatpaws-Key"),
        request.headers.get("Authorization"),
    )
    role = resolve_role(key)
    return {"role": role.value, "authenticated": role != ClientRole.public}
