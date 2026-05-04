from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from commerce_platform.platform.store.repos import UserRepo
from commerce_platform.web.auth_tokens import encode_access_token, pwd_context
from commerce_platform.web.config import WebConfig
from commerce_platform.web.deps import get_user_repo, get_web_config, require_user
from commerce_platform.web.schemas import LoginBody, RegisterBody

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(
    body: RegisterBody,
    user_repo: UserRepo = Depends(get_user_repo),
    web: WebConfig = Depends(get_web_config),
):
    if not web.open_registration:
        raise HTTPException(403, "Registration is closed")
    if await user_repo.get_by_email(body.email):
        raise HTTPException(409, "Email already registered")
    uid = await user_repo.create(body.email, pwd_context.hash(body.password))
    u = await user_repo.get_by_id(uid)
    assert u
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
    if not u or not pwd_context.verify(body.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": encode_access_token(u.id, u.email, u.role, web), "token_type": "bearer"}


me_router = APIRouter(tags=["auth"])


@me_router.get("/me")
async def me(user=Depends(require_user)):
    return {"id": user.id, "email": user.email, "role": user.role}
