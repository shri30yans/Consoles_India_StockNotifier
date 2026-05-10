from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request

from commerce_platform.platform.store.repos import UserRepo
from commerce_platform.web.auth_tokens import encode_access_token, hash_password, verify_password
from commerce_platform.web.config import WebConfig
from commerce_platform.web.deps import get_user_repo, get_web_config, require_user
from commerce_platform.web.schemas import LoginBody, RegisterBody

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(
    request: Request,
    body: RegisterBody,
    user_repo: UserRepo = Depends(get_user_repo),
    web: WebConfig = Depends(get_web_config),
):
    if not web.open_registration:
        raise HTTPException(403, "Registration is closed")

    ip = request.client.host if request.client else "unknown"
    if not request.app.state.rate_limiter.allow(f"ip:{ip}:register"):
        raise HTTPException(429, "Too many registration attempts; try later")

    try:
        uid = await user_repo.create(body.email, hash_password(body.password))
    except asyncpg.UniqueViolationError:
        raise HTTPException(409, "Email already registered")
    except Exception as e:
        raise HTTPException(500, str(e))

    u = await user_repo.get_by_id(uid)
    if not u:
        raise HTTPException(500, "Failed to create account")
    return {
        "access_token": encode_access_token(u.id, u.email, u.role, web),
        "token_type": "bearer",
    }


@router.post("/login")
async def login(
    body: LoginBody,
    user_repo: UserRepo = Depends(get_user_repo),
    web: WebConfig = Depends(get_web_config),
):
    u = await user_repo.get_by_email(body.email)
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": encode_access_token(u.id, u.email, u.role, web), "token_type": "bearer"}


me_router = APIRouter(tags=["auth"])


@me_router.get("/me")
async def me(user=Depends(require_user)):
    return {"id": user.id, "email": user.email, "role": user.role}
