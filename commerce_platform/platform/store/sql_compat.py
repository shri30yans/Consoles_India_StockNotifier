"""PostgreSQL DSN normalization and SSL handling."""

from __future__ import annotations

import os
import ssl
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse, urlunparse

import certifi

_SSL_QUERY_KEYS = frozenset({"sslmode", "ssl", "gssencmode"})


def postgres_ssl_from_env() -> bool | ssl.SSLContext:
    """``DATABASE_SSL``: ``true`` (default) or ``false``. For ``true``, use certifi CA bundle (asyncpg ``ssl=`` arg)."""
    raw = os.environ.get("DATABASE_SSL", "true").strip().lower()
    if raw == "false":
        return False
    if raw == "true":
        return ssl.create_default_context(cafile=certifi.where())
    raise RuntimeError("DATABASE_SSL must be exactly 'true' or 'false'")


def strip_ssl_related_query_params(dsn: str) -> str:
    """Remove TLS-related query params so ``ssl=False`` is not overridden by the URI."""
    p = urlparse(dsn)
    if not p.query:
        return dsn
    pairs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in _SSL_QUERY_KEYS]
    return urlunparse(p._replace(query=urlencode(pairs)))


def _fix_leading_dot_supabase_pooler_user(dsn: str) -> str:
    """Supabase pooler user must be ``postgres.<project-ref>``. A leading ``.`` alone is rejected."""
    p = urlparse(dsn)
    host = (p.hostname or "").lower()
    if "pooler.supabase.com" not in host or not p.username:
        return dsn
    user = unquote(p.username)
    if not user.startswith("."):
        return dsn
    user = "postgres." + user[1:]
    user_enc = quote(user, safe="")
    if p.password is not None:
        pw_enc = quote(unquote(p.password), safe="")
        netloc = f"{user_enc}:{pw_enc}@{p.hostname}"
    else:
        netloc = f"{user_enc}@{p.hostname}"
    if p.port:
        netloc = f"{netloc}:{p.port}"
    return urlunparse((p.scheme, netloc, p.path, p.params, p.query, p.fragment))


def normalize_dsn_for_asyncpg(dsn: str) -> str:
    """Strip ``+asyncpg`` scheme; fix common Supabase pooler username typo (``.ref`` → ``postgres.ref``)."""
    d = dsn.strip()
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if d.startswith(prefix):
            d = "postgresql://" + d[len(prefix) :]
            break
    return _fix_leading_dot_supabase_pooler_user(d)


def redact_dsn_for_logs(dsn: str) -> str:
    """Hide password in ``postgresql://user:pass@host/db`` for log lines."""
    if "@" not in dsn or "://" not in dsn:
        return dsn
    head, _, rest = dsn.partition("://")
    if "@" not in rest:
        return dsn
    creds, _, hostpart = rest.rpartition("@")
    if ":" not in creds:
        return f"{head}://***@{hostpart}"
    user, _, _pwd = creds.partition(":")
    return f"{head}://{user}:***@{hostpart}"
