"""Shared aiohttp helpers for notification channels that call HTTP APIs."""

from __future__ import annotations

import json
from typing import Any

import aiohttp


class ChannelError(Exception):
    """HTTP or transport failure for a notification channel."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        body_preview: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.body_preview = body_preview


class BaseHttpChannel:
    """Shared aiohttp scaffolding for channels that POST JSON to a webhook/API.

    Subclasses provide payload + URL; this base owns session lifetime, timeout,
    and error reporting. Callers wrap calls with ``with_retries`` where appropriate.

    A new ``ClientSession`` is used per call (matches existing channel behavior).
    """

    DEFAULT_TIMEOUT_SECONDS: float = 30.0

    async def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        timeout_seconds: float | None = None,
        auth: aiohttp.BasicAuth | None = None,
        headers: dict[str, str] | None = None,
        return_json: bool = False,
    ) -> dict[str, Any] | list[Any] | Any | None:
        """POST JSON; on non-2xx raises :class:`ChannelError`.

        With ``return_json=True``, parses and returns the response body (any JSON value).
        Otherwise returns ``None`` after a successful status check (body is not read).
        """
        total = self.DEFAULT_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        timeout = aiohttp.ClientTimeout(total=total)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                url,
                json=payload,
                auth=auth,
                headers=headers,
                timeout=timeout,
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    preview = body[:500] if body else ""
                    raise ChannelError(
                        f"HTTP {resp.status}: {preview}",
                        status=resp.status,
                        body_preview=preview,
                    )
                if return_json:
                    return await resp.json(content_type=None)
                return None

    async def _post_form_urlencoded(
        self,
        url: str,
        form: dict[str, str],
        *,
        timeout_seconds: float | None = None,
        auth: aiohttp.BasicAuth | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """POST ``application/x-www-form-urlencoded``; return parsed JSON. Raises on non-2xx."""
        total = self.DEFAULT_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        timeout = aiohttp.ClientTimeout(total=total)
        hdrs = {"Content-Type": "application/x-www-form-urlencoded"}
        if headers:
            hdrs.update(headers)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                url,
                data=form,
                auth=auth,
                headers=hdrs,
                timeout=timeout,
            ) as resp:
                raw = await resp.text()
                if resp.status >= 400:
                    preview = raw[:500] if raw else ""
                    raise ChannelError(
                        f"HTTP {resp.status}: {preview}",
                        status=resp.status,
                        body_preview=preview,
                    )
                return json.loads(raw)
