"""Channel router: maps a PublishablePost's logical channel keys
to (notifier, channel_target) pairs and fans out concurrently."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from deals_platform.domain.events import PublishablePost
from deals_platform.domain.ports import Notifier

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChannelBinding:
    """Binds a logical channel key (e.g. 'tech') to one notifier+target.

    Multiple bindings per channel key are supported (e.g. 'tech' goes to
    Telegram AND Discord AND WhatsApp).
    """

    channel_key: str
    notifier_name: str
    target: str  # env var name OR raw value (notifier decides)


class ChannelRouter:
    def __init__(
        self,
        notifiers: dict[str, Notifier],
        bindings: list[ChannelBinding],
    ) -> None:
        self._notifiers = notifiers
        self._bindings = bindings
        self._index: dict[str, list[ChannelBinding]] = {}
        for b in bindings:
            self._index.setdefault(b.channel_key, []).append(b)

    async def fan_out(self, post: PublishablePost) -> None:
        tasks = []
        for key in post.target_channels:
            for b in self._index.get(key, ()):
                notifier = self._notifiers.get(b.notifier_name)
                if notifier is None:
                    logger.warning("notifier %r unknown — skipping binding %s", b.notifier_name, b)
                    continue
                tasks.append(asyncio.create_task(self._safe_send(notifier, post, b)))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    async def _safe_send(notifier: Notifier, post: PublishablePost, b: ChannelBinding) -> None:
        try:
            await notifier.send(post, b.target)
        except Exception:
            logger.exception("notifier %s failed for channel %s", notifier.name, b.channel_key)
