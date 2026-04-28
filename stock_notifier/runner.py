from __future__ import annotations

import asyncio
import contextlib
import logging
import platform
import signal
from pathlib import Path

from stock_notifier.config_loader import (
    config_dir,
    load_app,
    load_jobs,
    load_products,
    load_website_configs,
)
from stock_notifier.config_validation import validate_monitoring_jobs
from stock_notifier.fetch import HtmlFetcher, PlaywrightFetcher, create_requests_fetcher
from stock_notifier.log_context import reset_job_log_id, set_job_log_id
from stock_notifier.logging_config import setup_logging
from stock_notifier.models import AppConfig, JobSpec, ParseContext
from stock_notifier.notify import NotificationService
from stock_notifier.parsers import parse_html
from stock_notifier.run_support import sleep_poll_interval
from stock_notifier.stock_state import ContinuousStockState

logger = logging.getLogger(__name__)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _job_log_label(job: JobSpec) -> str:
    return f"{job.transport}:{job.product_key}@{job.website_key}"


async def _requests_job_loop(
    job: JobSpec,
    *,
    app: AppConfig,
    products,
    websites,
    fetcher: HtmlFetcher,
    notifier: NotificationService,
    semaphore: asyncio.Semaphore | None,
) -> None:
    product = products[job.product_key]
    website = websites[job.website_key]
    link = product.links[job.website_key]

    ctx = ParseContext(
        job_product_key=job.product_key,
        website_key=job.website_key,
        page_url=link,
        website=website,
    )

    while True:
        log_tok = set_job_log_id(_job_log_label(job))
        try:
            if semaphore is not None:
                async with semaphore:
                    html = await fetcher.get_html(
                        link,
                        website.headers,
                        product_key=job.product_key,
                        website_key=job.website_key,
                    )
            else:
                html = await fetcher.get_html(
                    link,
                    website.headers,
                    product_key=job.product_key,
                    website_key=job.website_key,
                )
            if html:
                result = parse_html(html, ctx)
                for sig in result.signals:
                    await notifier.apply(sig, page=None)
        finally:
            reset_job_log_id(log_tok)
        await sleep_poll_interval(app, job.delay_seconds)


async def _playwright_job_loop(
    job: JobSpec,
    *,
    app: AppConfig,
    products,
    websites,
    fetcher: PlaywrightFetcher,
    notifier: NotificationService,
    semaphore: asyncio.Semaphore | None,
) -> None:
    product = products[job.product_key]
    website = websites[job.website_key]
    link = product.links[job.website_key]

    ctx = ParseContext(
        job_product_key=job.product_key,
        website_key=job.website_key,
        page_url=link,
        website=website,
    )

    page = await fetcher.new_page()
    try:
        while True:
            log_tok = set_job_log_id(_job_log_label(job))
            try:
                if semaphore is not None:
                    async with semaphore:
                        html = await fetcher.fetch_in_page(
                            page,
                            link,
                            website.headers,
                            product_key=job.product_key,
                            website_key=job.website_key,
                        )
                else:
                    html = await fetcher.fetch_in_page(
                        page,
                        link,
                        website.headers,
                        product_key=job.product_key,
                        website_key=job.website_key,
                    )
                if html:
                    result = parse_html(html, ctx)
                    for sig in result.signals:
                        await notifier.apply(sig, page=page)
            finally:
                reset_job_log_id(log_tok)
            await sleep_poll_interval(app, job.delay_seconds)
    finally:
        await page.close()


def _select_jobs(
    mode: str, requests_jobs: list[JobSpec], playwright_jobs: list[JobSpec]
) -> list[JobSpec]:
    m = mode.lower()
    if m == "requests":
        return list(requests_jobs)
    if m == "playwright":
        return list(playwright_jobs)
    if m == "all":
        return list(requests_jobs) + list(playwright_jobs)
    if m == "pause":
        return []
    logger.error("Unknown mode %s — valid: requests, playwright, all, pause", mode)
    return []


async def run() -> None:
    from dotenv import load_dotenv

    root = _root()
    load_dotenv(root / ".env")
    app = load_app()
    setup_logging(app, root)

    products = load_products()
    websites = load_website_configs()
    requests_jobs, playwright_jobs = load_jobs()
    jobs = _select_jobs(app.mode, requests_jobs, playwright_jobs)
    validate_monitoring_jobs(products, jobs)

    print("Bot started (stock_notifier)")
    print(f"Python version: {platform.python_version()}")
    print(f"Config directory: {config_dir()}")
    print(f"Notifications enabled: {app.notify}")
    print(f"Mode: {app.mode} ({len(jobs)} job(s))")
    imp = f" (impersonate={app.curl_impersonate})" if app.http_client == "curl_cffi" else ""
    print(f"HTTP client: {app.http_client}{imp}")
    print(
        f"fake-useragent: {app.use_fake_useragent} | "
        f"playwright stealth: {app.playwright_apply_stealth}",
    )
    print("-------------------")

    if not jobs:
        logger.info("No monitoring jobs selected; exiting.")
        return

    notifier = NotificationService(app, products, websites, ContinuousStockState())

    req_sem: asyncio.Semaphore | None = None
    pw_sem: asyncio.Semaphore | None = None
    n = app.max_concurrent_per_transport
    if n > 0:
        req_sem = asyncio.Semaphore(n)
        pw_sem = asyncio.Semaphore(n)

    req_fetcher: HtmlFetcher | None = None
    pw: PlaywrightFetcher | None = None
    worker_tasks: list[asyncio.Task] = []

    for job in jobs:
        if job.transport == "requests":
            if req_fetcher is None:
                req_fetcher = create_requests_fetcher(app)
                await req_fetcher.start()
            worker_tasks.append(
                asyncio.create_task(
                    _requests_job_loop(
                        job,
                        app=app,
                        products=products,
                        websites=websites,
                        fetcher=req_fetcher,
                        notifier=notifier,
                        semaphore=req_sem,
                    ),
                    name=f"req:{job.product_key}:{job.website_key}",
                ),
            )
        elif job.transport == "playwright":
            if pw is None:
                pw = PlaywrightFetcher(app)
                await pw.start()
            worker_tasks.append(
                asyncio.create_task(
                    _playwright_job_loop(
                        job,
                        app=app,
                        products=products,
                        websites=websites,
                        fetcher=pw,
                        notifier=notifier,
                        semaphore=pw_sem,
                    ),
                    name=f"pw:{job.product_key}:{job.website_key}",
                ),
            )

    stop = asyncio.Event()

    def _request_stop() -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop)
        except (NotImplementedError, RuntimeError, ValueError):
            pass

    async def _gather_workers() -> None:
        await asyncio.gather(*worker_tasks)

    gather_workers = asyncio.create_task(_gather_workers())
    wait_stop = asyncio.create_task(stop.wait())
    try:
        done, _pending = await asyncio.wait(
            {gather_workers, wait_stop},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if wait_stop in done and not gather_workers.done():
            logger.info("Shutdown signal received; cancelling worker tasks")
            for t in worker_tasks:
                t.cancel()
            gather_workers.cancel()
            await asyncio.gather(*worker_tasks, return_exceptions=True)
            with contextlib.suppress(asyncio.CancelledError):
                await gather_workers
        else:
            wait_stop.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await wait_stop
    finally:
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.remove_signal_handler(sig)
            except (NotImplementedError, RuntimeError, ValueError):
                pass
        if req_fetcher is not None:
            await req_fetcher.close()
        if pw is not None:
            await pw.close()


def main() -> None:
    asyncio.run(run())
