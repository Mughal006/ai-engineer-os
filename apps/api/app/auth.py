"""Clerk JWT verification dependency.

When `auth_enabled` is False (no Clerk config), a deterministic dev user
is returned so local development without Clerk still works end-to-end.
"""

from __future__ import annotations

from functools import lru_cache

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import User

DEV_CLERK_ID = "dev-user"
DEV_EMAIL = "dev@example.com"


@lru_cache(maxsize=1)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _verify_clerk_token(token: str, settings: Settings) -> dict[str, object]:
    issuer = settings.clerk_jwt_issuer.rstrip("/")
    jwks_url = f"{issuer}/.well-known/jwks.json"
    try:
        signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token).key
        decoded: dict[str, object] = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"verify_aud": False},
        )
        return decoded
    except (jwt.PyJWTError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}"
        ) from exc


def _ensure_user(
    db: Session, *, clerk_id: str, email: str, name: str | None = None
) -> User:
    user = db.query(User).filter(User.clerk_id == clerk_id).one_or_none()
    if user is None:
        user = User(clerk_id=clerk_id, email=email, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user, creating a row on first contact."""
    if not settings.auth_enabled:
        return _ensure_user(db, clerk_id=DEV_CLERK_ID, email=DEV_EMAIL, name="Dev User")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token."
        )

    token = authorization.split(" ", 1)[1].strip()
    claims = _verify_clerk_token(token, settings)
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing 'sub' claim."
        )
    email_claim = claims.get("email") or f"{clerk_id}@example.com"
    name_claim = claims.get("name")
    name = name_claim if isinstance(name_claim, str) else None
    return _ensure_user(db, clerk_id=clerk_id, email=str(email_claim), name=name)
