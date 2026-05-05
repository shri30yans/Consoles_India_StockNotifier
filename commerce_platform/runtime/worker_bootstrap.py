"""Unified event-driven notification pipeline."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from commerce_platform.agents.curator_agent import CuratorAgent
from commerce_platform.agents.discovery_agent import DealDiscoveryAgent
from commerce_platform.agents.parser_fixer_agent import ParserFixerAgent
from commerce_platform.deals.scorer import DealScorer
from commerce_platform.notify.handler import NotificationHandler
from commerce_platform.platform.notify.affiliate import AffiliateRewriter
from commerce_platform.platform.notify.router import ChannelRouter
from commerce_platform.platform.config.merge import load_merged_platform_config
from commerce_platform.platform.config.schema import PlatformConfig
from commerce_platform.platform.events.bus import EventBus
from commerce_platform.platform.events.observation import PriceObservation, RuleMatch
from commerce_platform.platform.fetch.factory import create_http_fetcher, create_playwright_fetcher
from commerce_platform.platform.store.db import Database
from commerce_platform.platform.store.repos import CatalogRepo, ConfigSettingsRepo, DealRepo, PriceRepo, StockRepo
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
    config_repo = ConfigSettingsRepo(db.pool)
    deal_repo = DealRepo(db.pool)
    price_repo = PriceRepo(db.pool)
    stock_repo = StockRepo(db.pool)
    bus = EventBus()
    router = ChannelRouter(config.channels)

    # Core services
    rule_engine = RuleEngine(catalog_repo, price_repo, stock_repo)
    affiliate_rewriter = AffiliateRewriter(config_repo)
    notification_handler = NotificationHandler(router, affiliate_rewriter=affiliate_rewriter)

    async def load_platform_config() -> PlatformConfig:
        """Load current platform configuration from disk."""
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

    async def discovery_loop() -> None:
        """Autonomous discovery agents poll retailer deal pages."""
        http_fetcher = create_http_fetcher(config.stock.fetch)
        await http_fetcher.start()
        pw_fetcher = create_playwright_fetcher(config.stock.fetch)

        deal_scorer = DealScorer(
            config_repo,
            price_repo,
            config.deals.scoring.weights,
        )

        try:
            while True:
                platform_config = await load_platform_config()
                for source in platform_config.platform_sources:
                    # Only process deal sources (type ends with _deals)
                    if not source.type.endswith("_deals"):
                        continue

                    if not source.seed_urls:
                        logger.warning("Deal source %s has no seed URLs", source.type)
                        continue

                    # Sources that require Playwright for JS rendering
                    playwright_sources = {"ajio_deals", "myntra_deals"}
                    use_playwright = source.type in playwright_sources
                    fetcher = pw_fetcher if use_playwright else http_fetcher

                    agent = DealDiscoveryAgent(
                        source_type=source.type,
                        seed_urls=source.seed_urls,
                        minimum_discount_pct=source.minimum_discount_pct or 0.0,
                        fetcher=fetcher,
                        catalog_repo=catalog_repo,
                        deal_repo=deal_repo,
                        deal_scorer=deal_scorer,
                        bus=bus,
                        config_repo=config_repo,
                    )

                    try:
                        result = await agent.discover()
                        logger.info(
                            "Discovery: %s — found=%d qualified=%d created=%d updated=%d errors=%d",
                            source.type,
                            result.items_found,
                            result.items_qualified,
                            result.deals_created,
                            result.deals_updated,
                            len(result.errors),
                        )
                        if result.parser_suggestion:
                            logger.warning("Parser suggestion for %s: %s", source.type, result.parser_suggestion)
                    except Exception:
                        logger.exception("Discovery failed for source %s", source.type)

                # Sleep until next poll
                poll_interval = max(60, config.platform.config_reload_seconds)
                await asyncio.sleep(poll_interval)

        except asyncio.CancelledError:
            logger.info("Discovery loop stopped")
        finally:
            await http_fetcher.close()
            await pw_fetcher.close()

    async def curation_loop() -> None:
        """Autonomous curation agent evaluates deals and routes to admin."""
        curator = CuratorAgent(deal_repo, config_repo, router)

        try:
            while True:
                try:
                    result = await curator.curate()
                    logger.info(
                        "Curation: pending=%d sent_to_admin=%d errors=%d",
                        result.get("total_pending", 0),
                        result.get("sent_to_admin", 0),
                        len(result.get("errors", [])),
                    )
                    if result.get("errors"):
                        for err in result.get("errors", []):
                            logger.warning("Curation error: %s", err)
                except Exception:
                    logger.exception("Curation pass failed")

                # Run curation every 5 minutes
                await asyncio.sleep(300)

        except asyncio.CancelledError:
            logger.info("Curation loop stopped")

    async def parser_fixer_loop() -> None:
        """ParserFixerAgent listens for parser failures and auto-fixes."""
        fixer = ParserFixerAgent(config_repo, bus)
        try:
            await fixer.run_continuous()
        except asyncio.CancelledError:
            logger.info("ParserFixerAgent stopped")

    # Create tasks
    tasks = [
        asyncio.create_task(
            StockRunner(
                get_merged,
                bus,
                catalog_repo,
                config_repo=config_repo,
                deal_repo=deal_repo,
                price_repo=price_repo,
            ).run(),
            name="stock-runner",
        ),
        asyncio.create_task(observation_processor(), name="observation-processor"),
        asyncio.create_task(discovery_loop(), name="discovery-loop"),
        asyncio.create_task(curation_loop(), name="curation-loop"),
        asyncio.create_task(parser_fixer_loop(), name="parser-fixer"),
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
