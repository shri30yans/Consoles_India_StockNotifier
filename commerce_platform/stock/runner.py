"""Stock runner — builds polling jobs from config and schedules them."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, cast

from commerce_platform.platform.config.schema import PlatformConfig, ProductConfig, WatchConfig
from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.fetch.factory import create_http_fetcher, create_playwright_fetcher
from commerce_platform.platform.fetch.protocol import HtmlFetcher
from commerce_platform.platform.store.repos import CatalogRepo
from commerce_platform.stock.poller import Poller
from commerce_platform.stock.wishlist_watcher import WishlistWatcher

logger = logging.getLogger(__name__)


class StockRunner:
    def __init__(
        self,
        get_config: Callable[[], Awaitable[PlatformConfig]],
        bus: EventBus,
        catalog_repo: CatalogRepo,
    ) -> None:
        self._get_config = get_config
        self._bus = bus
        self._catalog_repo = catalog_repo
        self._http_sem: asyncio.Semaphore | None = None
        self._pw_sem: asyncio.Semaphore | None = None

    async def run(self) -> None:
        http_fetcher = None
        pw_fetcher = None

        while True:
            config = await self._get_config()
            reload_s = max(15, config.platform.config_reload_seconds)

            if http_fetcher is None:
                http_fetcher = create_http_fetcher(config.stock.fetch)
                await http_fetcher.start()
                pw_fetcher = create_playwright_fetcher(config.stock.fetch)

            self._http_sem = asyncio.Semaphore(config.stock.fetch.max_concurrent_requests)
            self._pw_sem = asyncio.Semaphore(config.stock.fetch.max_concurrent_playwright)
            assert (
                self._http_sem is not None
                and self._pw_sem is not None
                and pw_fetcher is not None
            )

            tasks = []
            for product in config.products:
                for watch in product.watches:
                    poll_seconds = config.resolve_poll_seconds(watch)
                    use_playwright = watch.source.endswith("_playwright")
                    fetcher = pw_fetcher if use_playwright else http_fetcher
                    sem = self._pw_sem if use_playwright else self._http_sem
                    tasks.append(self._job_loop(product, watch, fetcher, poll_seconds, sem))

            for source in config.platform_sources:
                if source.type == "amazon_wishlist":
                    logger.info(
                        "Registering amazon_wishlist job: poll_every=%ds url=%s",
                        source.poll_seconds,
                        source.url or "(missing)",
                    )
                    tasks.append(
                        WishlistWatcher(
                            source,
                            http_fetcher,
                            self._catalog_repo,
                            self._bus,
                        ).run()
                    )

            if not tasks:
                logger.warning("No stock jobs configured — sleeping %ss", reload_s)
                await asyncio.sleep(reload_s)
                continue

            logger.info(
                "StockRunner starting %d jobs — full reload every %ss",
                len(tasks),
                reload_s,
            )
            reload_timer = asyncio.create_task(asyncio.sleep(reload_s))

            async def _gather_jobs(jobs: Sequence[Awaitable[Any]]) -> list[Any]:
                return cast(list[Any], await asyncio.gather(*jobs, return_exceptions=True))

            job_gather: asyncio.Task[list[Any]] = asyncio.create_task(_gather_jobs(tasks))
            done, pending = await asyncio.wait(
                {reload_timer, job_gather},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for p in pending:
                p.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            if job_gather in done:
                excs = job_gather.result()
                if isinstance(excs, BaseException):
                    logger.exception("Stock gather failed: %s", excs)
                elif isinstance(excs, list) and any(isinstance(x, BaseException) for x in excs):
                    logger.error("Stock jobs exited with errors: %s", excs)

    async def _job_loop(
        self,
        product: ProductConfig,
        watch: WatchConfig,
        fetcher: HtmlFetcher,
        poll_seconds: int,
        sem: asyncio.Semaphore,
    ) -> None:
        poller = Poller(fetcher, self._bus)
        label = f"{product.id}@{watch.source}"
        await asyncio.sleep(random.uniform(0, min(poll_seconds * 0.1, 10)))
        logger.info("Stock job started: %s every %ds", label, poll_seconds)
        backoff = 1.0
        while True:
            try:
                async with sem:
                    await poller.poll(product, watch)
                backoff = 1.0
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Stock poll error for %s", label)
                await asyncio.sleep(min(backoff * 2, 300))
                backoff = min(backoff * 2, 300)
                continue
            await asyncio.sleep(poll_seconds)
