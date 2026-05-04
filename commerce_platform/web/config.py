"""Web API settings from the environment.

Call ``load_dotenv()`` before ``load_web_config()`` when using a ``.env`` file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WebConfig:
    jwt_alg: str
    jwt_secret: str
    jwt_expire_seconds: int
    open_registration: bool
    bootstrap_admin_email: str
    bootstrap_admin_password: str
    web_requests_per_hour_per_ip: int
    cors_origins: tuple[str, ...]
    trusted_hosts: tuple[str, ...]
    admin_emails: tuple[str, ...]


def load_web_config(admin_emails: list[str] | None = None) -> WebConfig:
    """Read ``WEB_*`` from ``os.environ``.

    Values typically come from ``load_dotenv()`` or the process environment.
    ``admin_emails``: list of email addresses that should have admin role (from config.yaml).
    """
    raw_cors = os.getenv("WEB_CORS_ORIGINS", "*")
    parts = tuple(p.strip() for p in raw_cors.split(",") if p.strip())
    cors = parts if parts else ("*",)
    raw_hosts = os.getenv("WEB_TRUSTED_HOSTS", "").strip()
    trusted = tuple(h.strip() for h in raw_hosts.split(",") if h.strip()) if raw_hosts else ()
    admin_email_tuple = tuple(e.lower().strip() for e in (admin_emails or []) if e.strip())
    return WebConfig(
        jwt_alg="HS256",
        jwt_secret=os.getenv("WEB_JWT_SECRET", "dev-insecure-change-me"),
        jwt_expire_seconds=int(
            os.getenv("WEB_JWT_EXPIRE_SECONDS", str(7 * 24 * 3600)),
        ),
        open_registration=os.getenv("WEB_OPEN_REGISTRATION", "true").lower()
        in ("1", "true", "yes"),
        bootstrap_admin_email=os.getenv("WEB_BOOTSTRAP_ADMIN_EMAIL", "").strip(),
        bootstrap_admin_password=os.getenv("WEB_BOOTSTRAP_ADMIN_PASSWORD", "").strip(),
        web_requests_per_hour_per_ip=int(os.getenv("WEB_REQUESTS_PER_HOUR_PER_IP", "20")),
        cors_origins=cors,
        trusted_hosts=trusted,
        admin_emails=admin_email_tuple,
    )
