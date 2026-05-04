"""Unified event-driven notification pipeline."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from commerce_platform.notify.handler import NotificationHandler
from commerce_platform.platform.notify.router import ChannelRouter
from commerce_platform.platform.config.merge import load_merged_platform_config
from commerce_platform.platform.config.schema import PlatformConfig
from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.events.observation import PriceObservation, RuleMatch
from commerce_platform.platform.store.db import Database
from commerce_platform.platform.store.repos import CatalogRepo, PriceRepo, StockRepo
from commerce_platform.platform.store.repos.price_repo import PriceSnapshot
from commerce_platform.rules.engine import RuleEngine
from commerce_platform.stock.runner import StockRunner

logger = logging.getLogger(__name__)


async def run_stock_and_deals_workers(
    config: PlatformConfig,
    yaml_path: str | Path,
    *,
    db: Database,
) -> None:
    """Run unified notification pipeline. ``db`` must already be open."""
    path = Path(yaml_path)
    catalog_repo = CatalogRepo(db.pool)
    price_repo = PriceRepo(db.pool)
    stock_repo = StockRepo(db.pool)
    bus = EventBus()
    router = ChannelRouter(config.channels)

    # Core services
    rule_engine = RuleEngine(catalog_repo, price_repo, stock_repo)
    notification_handler = NotificationHandler(router)

    async def get_merged():
        return await load_merged_platform_config(path, catalog_repo)

    async def observation_processor() -> None:
        """Subscribe to observations, evaluate rules, send notifications."""
        await rule_engine.reload_rules()
        config_reload_seconds = max(15, config.platform.config_reload_seconds)

        async def persist_observation(observation: PriceObservation) -> None:
            """Write scrape outcome so APIs/status ``last_scrape_at`` reflect every poll."""
            await stock_repo.upsert(observation.product_id, observation.retailer, observation.in_stock)
            if observation.price_paise > 0 or (
                observation.mrp_paise is not None and observation.mrp_paise > 0
            ):
                await price_repo.record(
                    PriceSnapshot(
                        id=None,
                        product_id=observation.product_id,
                        retailer=observation.retailer,
                        price_paise=observation.price_paise,
                        mrp_paise=observation.mrp_paise,
                        in_stock=observation.in_stock,
                        captured_at=observation.observed_at,
                    )
                )

        # Periodic rule reload
        async def reload_rules_loop() -> None:
            while True:
                await asyncio.sleep(config_reload_seconds)
                try:
                    await rule_engine.reload_rules()
                except Exception:
                    logger.exception("Failed to reload rules")

        reload_task = asyncio.create_task(reload_rules_loop(), name="rule-reloader")

        # Process observations
        obs_queue = bus.subscribe(PriceObservation)
        try:
            async for observation in bus.iter_events(obs_queue):
                try:
                    await persist_observation(observation)
                    # Evaluate rules
                    matches = await rule_engine.evaluate(observation)

                    # Handle matches
                    for match in matches:
                        logger.info(
                            "Rule matched: product=%s rule=%s retailer=%s",
                            match.observation.product_id,
                            match.rule_id,
                            match.observation.retailer,
                        )
                        await notification_handler.handle_rule_match(match)

                except Exception:
                    logger.exception("Error processing observation: %s", observation)

        finally:
            reload_task.cancel()
            await asyncio.gather(reload_task, return_exceptions=True)

    # Create tasks
    tasks = [
        asyncio.create_task(StockRunner(get_merged, bus, catalog_repo).run(), name="stock-runner"),
        asyncio.create_task(observation_processor(), name="observation-processor"),
    ]

    try:
        done, _pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        for t in done:
            exc = t.exception()
            if exc is not None:
                raise exc
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Workers stopped.")
