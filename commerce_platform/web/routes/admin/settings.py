"""Read-only admin settings endpoints (auth/JWT/registration view)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from commerce_platform.platform.store.repos import UserRepo
from commerce_platform.web.config import WebConfig
from commerce_platform.web.deps import get_user_repo, get_web_config, require_admin

router = APIRouter()


@router.get("/settings/auth")
async def admin_auth_settings(
    _admin=Depends(require_admin),
    user_repo: UserRepo = Depends(get_user_repo),
    web: WebConfig = Depends(get_web_config),
):
    user_count = await user_repo.count()
    return {
        "jwt_algorithm": web.jwt_alg,
        "jwt_expire_seconds": web.jwt_expire_seconds,
        "open_registration": web.open_registration,
        "bootstrap_admin_env_configured": bool(
            web.bootstrap_admin_email and web.bootstrap_admin_password
        ),
        "requests_per_hour_per_ip": web.web_requests_per_hour_per_ip,
        "cors_origins": ",".join(web.cors_origins),
        "using_default_jwt_secret": web.jwt_secret == "dev-insecure-change-me",
        "registered_users": user_count,
        "note": "WEB_JWT_SECRET and password values are never returned. Use the same PLATFORM_CONFIG for every process that touches this database.",
    }
