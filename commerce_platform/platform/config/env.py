"""Resolve env:VAR_NAME placeholders in config string values."""

from __future__ import annotations

import os
import re


_ENV_PATTERN = re.compile(r"^env:([A-Z_][A-Z0-9_]*)$")


def resolve(value: str) -> str:
    """If value matches 'env:VAR_NAME', return the env var value. Otherwise return as-is."""
    m = _ENV_PATTERN.match(value.strip())
    if m:
        var = m.group(1)
        resolved = os.environ.get(var)
        if resolved is None:
            raise RuntimeError(f"Required env var {var!r} is not set")
        return resolved
    return value


def resolve_optional(value: str | None) -> str | None:
    if value is None:
        return None
    m = _ENV_PATTERN.match(value.strip())
    if m:
        var = m.group(1)
        return os.environ.get(var)
    return value
