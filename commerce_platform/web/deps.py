"""FastAPI dependencies: repositories, config, auth."""

from __future__ import annotations

from pathlib import Path

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from commerce_platform.platform.store.db import Database
from commerce_platform.platform.store.repos import (
    CatalogRepo,
    ConfigSettingsRepo,
    DealRepo,
    PriceRepo,
    StockRepo,
    TrackingRepo,
    UserRepo,
)
from commerce_platform.web.auth_tokens import bearer
from commerce_platform.web.config import WebConfig


async def get_db(request: Request) -> Database:
    return request.app.state.db


async def get_config_path(request: Request) -> Path:
    return request.app.state.config_path


async def get_web_config(request: Request) -> WebConfig:
    return request.app.state.web_config


async def get_price_repo(request: Request) -> PriceRepo:
    return request.app.state.price_repo


async def get_stock_repo(request: Request) -> StockRepo:
    return request.app.state.stock_repo


async def get_user_repo(request: Request) -> UserRepo:
    return request.app.state.user_repo


async def get_tracking_repo(request: Request) -> TrackingRepo:
    return request.app.state.tracking_repo


async def get_catalog_repo(request: Request) -> CatalogRepo:
    return request.app.state.catalog_repo


async def get_config_repo(request: Request) -> ConfigSettingsRepo:
    return request.app.state.config_repo


async def get_deal_repo(request: Request) -> DealRepo:
    return request.app.state.deal_repo


async def get_app(request: Request) -> FastAPI:
    return request.app


async def optional_user(
    request: Request,
    user_repo: UserRepo = Depends(get_user_repo),
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    if creds is None or creds.scheme.lower() != "bearer":
        return None
    web: WebConfig = request.app.state.web_config
    try:
        payload = jwt.decode(creds.credentials, web.jwt_secret, algorithms=[web.jwt_alg])
    except jwt.PyJWTError:
        return None
    uid = int(payload.get("sub", "0"))
    return await user_repo.get_by_id(uid)


async def require_user(user=Depends(optional_user)):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    return user


async def require_admin(user=Depends(require_user)):
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user
