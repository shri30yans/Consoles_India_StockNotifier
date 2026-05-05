"""Password hashing and JWT access tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi.security import HTTPBearer

from commerce_platform.web.config import WebConfig

bearer = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def encode_access_token(user_id: int, email: str, role: str, web: WebConfig) -> str:
    exp = datetime.now(tz=timezone.utc) + timedelta(seconds=web.jwt_expire_seconds)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": exp,
    }
    return jwt.encode(payload, web.jwt_secret, algorithm=web.jwt_alg)
