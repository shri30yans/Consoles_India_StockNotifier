"""Composition root.

Builds and wires every adapter. Designed so each piece is a constructor argument
you can swap (e.g. inject InMemoryDedupe in tests, Redis in prod, etc.).
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from dataclasses import dataclass

from deals_platform.bus import InMemoryBus
from deals_platform.bus.bus import Topics
from deals_platform.config import PlatformConfig, load_platform_config
from deals_platform.domain.events import (
    DealCandidate,
    EnrichedDeal,
    PublishablePost,
    ScoredDeal,
)
from deals_platform.domain.ports import Source
from deals_platform.llm import OpenAICompatLLM, StubLLM
from deals_platform.notify import (
    ChannelRouter,
    DiscordNotifier,
    EmailNotifier,
    TelegramNotifier,
    TwitterNotifier,
    WhatsAppNotifier,
)
from deals_platform.pipeline import (
    CompositeScorer,
    CuratorAgent,
    HashCanonicalResolver,
    Normalizer,
)
from deals_platform.pipeline.scorer import ScoringWeights
from deals_platform.sources import (
    AmazonSignalsSource,
    DesiDimeSource,
    RedditSource,
    RetailerWatchSource,
    WatchSpec,
)
from deals_platform.storage import (
    PostgresDedupeStore,
    PostgresPostLog,
    PostgresPriceHistoryRepo,
    create_engine,
    session_factory,
)
from deals_platform.storage.bootstrap import create_all
from stock_notifier.config_loader import load_app
from stock_notifier.fetch import create_requests_fetcher

logger = logging.getLogger(__name__)


@dataclass
class App:
    sources: list[Source]
    normalizer: Normalizer
    scorer: CompositeScorer
    curator: CuratorAgent
    router: ChannelRouter
    bus: InMemoryBus
    cleanup: list = None  # type: ignore[assignment]


async def build_app(cfg: PlatformConfig | None = None) -> App:
    cfg = cfg or load_platform_config()

    # ---- storage ----
    engine = create_engine()
    await create_all(engine)
    sm = session_factory(engine)
    history = PostgresPriceHistoryRepo(sm)
    dedupe = PostgresDedupeStore(sm)
    post_log = PostgresPostLog(sm)

    # ---- llm ----
    llm = _build_llm()

    # ---- pipeline parts ----
    resolver = HashCanonicalResolver()
    normalizer = Normalizer(history=history, resolver=resolver, dedupe=dedupe)

    weights = ScoringWeights(
        lowest_in_90d=cfg.scoring.weights.get("lowest_in_90d", 0.35),
        below_30d_median=cfg.scoring.weights.get("below_30d_median", 0.25),
        discount_vs_mrp=cfg.scoring.weights.get("discount_vs_mrp", 0.10),
        cross_retailer_best=cfg.scoring.weights.get("cross_retailer_best", 0.15),
        has_offers=cfg.scoring.weights.get("has_offers", 0.05),
        aggregator_corroborated=cfg.scoring.weights.get("aggregator_corroborated", 0.10),
    )
    scorer = CompositeScorer(weights=weights, threshold=cfg.scoring.threshold)
    curator = CuratorAgent(
        llm=llm,
        post_log=post_log,
        category_to_channels=cfg.channel_to_channel_keys(),
        repost_cooldown_hours=cfg.scoring.repost_cooldown_hours,
        score_threshold=cfg.scoring.threshold,
    )

    # ---- notifiers + router ----
    notifiers = {
        "telegram": TelegramNotifier(),
        "whatsapp": WhatsAppNotifier(),
        "discord": DiscordNotifier(),
        "twitter": TwitterNotifier(),
        "email": EmailNotifier(),
    }
    router = ChannelRouter(notifiers, cfg.channel_bindings())

    # ---- sources ----
    cleanup: list = []
    sources: list[Source] = []
    if cfg.sources.watches or cfg.sources.amazon_signals.enabled:
        app_cfg = load_app()  # reuse stock_notifier's HTTP fetcher config
        fetcher = create_requests_fetcher(app_cfg)
        await fetcher.start()
        cleanup.append(fetcher.close)
        if cfg.sources.watches:
            watches = [
                WatchSpec(
                    retailer=w.retailer,
                    url=w.url,
                    poll_seconds=w.poll_seconds,
                    title_hint=w.title_hint,
                )
                for w in cfg.sources.watches
            ]
            sources.append(RetailerWatchSource("retailers", watches, fetcher))

        if cfg.sources.amazon_signals.enabled and cfg.sources.amazon_signals.seed_urls:
            sources.append(
                AmazonSignalsSource(
                    fetcher,
                    seed_urls=cfg.sources.amazon_signals.seed_urls,
                    poll_seconds=cfg.sources.amazon_signals.poll_seconds,
                    max_links_per_seed=cfg.sources.amazon_signals.max_links_per_seed,
                )
            )

        for agg in cfg.sources.aggregators:
            if not agg.enabled:
                continue
            if agg.type == "desidime":
                sources.append(DesiDimeSource(fetcher, poll_seconds=agg.poll_seconds))
            elif agg.type == "reddit":
                sources.append(RedditSource(agg.subreddits, poll_seconds=agg.poll_seconds))

    app = App(
        sources=sources,
        normalizer=normalizer,
        scorer=scorer,
        curator=curator,
        router=router,
        bus=InMemoryBus(),
        cleanup=cleanup,
    )
    return app


def _build_llm():
    if os.environ.get("LLM_API_KEY"):
        return OpenAICompatLLM()
    logger.warning("LLM_API_KEY not set — using StubLLM (development only).")
    return StubLLM()


# ----------------------- Pipeline coroutines -----------------------


async def _candidate_loop(app: App) -> None:
    """Read every Source in parallel and publish to the bus."""
    async def consume(src: Source) -> None:
        async for cand in src.stream():
            await app.bus.publish(Topics.CANDIDATE, cand)

    tasks = [asyncio.create_task(consume(s), name=f"src:{s.name}") for s in app.sources]
    await asyncio.gather(*tasks, return_exceptions=True)


async def _normalize_loop(app: App) -> None:
    sub = app.bus.subscribe(Topics.CANDIDATE)
    async for evt in sub:
        cand: DealCandidate = evt  # type: ignore[assignment]
        try:
            enriched = await app.normalizer.normalize(cand)
        except Exception:
            logger.exception("normalize failed")
            continue
        if enriched is not None:
            await app.bus.publish(Topics.ENRICHED, enriched)


async def _score_loop(app: App) -> None:
    sub = app.bus.subscribe(Topics.ENRICHED)
    async for evt in sub:
        deal: EnrichedDeal = evt  # type: ignore[assignment]
        try:
            scored = app.scorer.score(deal)
        except Exception:
            logger.exception("score failed")
            continue
        if scored.breakdown.score >= app.scorer.threshold:
            await app.bus.publish(Topics.SCORED, scored)


async def _curate_loop(app: App) -> None:
    sub = app.bus.subscribe(Topics.SCORED)
    async for evt in sub:
        scored: ScoredDeal = evt  # type: ignore[assignment]
        try:
            post = await app.curator.curate(scored)
        except Exception:
            logger.exception("curate failed")
            continue
        if post is not None:
            await app.bus.publish(Topics.PUBLISHABLE, post)


async def _publish_loop(app: App) -> None:
    sub = app.bus.subscribe(Topics.PUBLISHABLE)
    async for evt in sub:
        post: PublishablePost = evt  # type: ignore[assignment]
        try:
            await app.router.fan_out(post)
        except Exception:
            logger.exception("router fan-out failed")


# ----------------------- Entrypoint -----------------------


async def run() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = await build_app()
    logger.info(
        "DealsPlatform online — sources=%d threshold=%.2f", len(app.sources), app.scorer.threshold
    )

    tasks = [
        asyncio.create_task(_candidate_loop(app), name="candidates"),
        asyncio.create_task(_normalize_loop(app), name="normalize"),
        asyncio.create_task(_score_loop(app), name="score"),
        asyncio.create_task(_curate_loop(app), name="curate"),
        asyncio.create_task(_publish_loop(app), name="publish"),
    ]

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except (NotImplementedError, RuntimeError, ValueError):
            pass

    try:
        await stop.wait()
    finally:
        logger.info("shutting down")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for fn in app.cleanup or ():
            try:
                await fn()
            except Exception:
                logger.exception("cleanup failed")
