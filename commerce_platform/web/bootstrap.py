"""Startup side effects (e.g. first admin user)."""

from __future__ import annotations

import logging

from commerce_platform.platform.store.db import Database
from commerce_platform.platform.store.repos import UserRepo
from commerce_platform.web.auth_tokens import pwd_context
from commerce_platform.web.config import WebConfig

logger = logging.getLogger(__name__)


async def maybe_bootstrap_admin(db: Database, web: WebConfig) -> None:
    if not web.bootstrap_admin_email or not web.bootstrap_admin_password:
        return
    repo = UserRepo(db.pool)
    existing = await repo.get_by_email(web.bootstrap_admin_email)
    if existing:
        return
    user_count = await repo.count()
    if user_count > 0:
        return
    h = pwd_context.hash(web.bootstrap_admin_password)
    await repo.create(web.bootstrap_admin_email, h, role="admin")
    logger.info("Bootstrapped admin user %s", web.bootstrap_admin_email)
