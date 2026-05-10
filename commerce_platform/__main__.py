"""Commerce Platform — one process: HTTP API + stock/alerts/deals workers."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


async def _run_app_with_workers(config_path: Path, *, host: str, port: int) -> None:
    """Open one ``Database`` for HTTP handlers and workers so schema migration runs once."""
    from uvicorn import Config, Server

    from commerce_platform.platform.config.loader import load
    from commerce_platform.platform.logging_setup import configure_platform_logging
    from commerce_platform.platform.store.db import Database
    from commerce_platform.runtime.worker_bootstrap import run_stock_and_deals_workers
    from commerce_platform.web.config import load_web_config
    from commerce_platform.web.main import create_app

    os.environ["PLATFORM_CONFIG"] = str(config_path)
    config = load(config_path)
    configure_platform_logging(config.platform)
    web_cfg = load_web_config()

    db = Database(config.platform.store)
    await db.open()
    app = create_app(config_path, web_cfg, db=db)
    server = Server(Config(app, host=host, port=port, log_level="info"))

    async def serve_http() -> None:
        await server.serve()

    try:
        await asyncio.gather(
            serve_http(),
            run_stock_and_deals_workers(config, config_path, db=db),
        )
    finally:
        await db.close()


def main() -> None:
    load_dotenv()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser(
        prog="commerce_platform",
        description=(
            "Run the FastAPI app and stock + alerts + deals workers in one process."
        ),
    )
    parser.add_argument(
        "--config",
        "-c",
        default=os.environ.get("PLATFORM_CONFIG", "config.yaml"),
        metavar="PATH",
        help="config.yaml (default: env PLATFORM_CONFIG or ./config.yaml)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP port (default: 8000)",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        metavar="COMMAND",
        help="Optional. Only `all` is valid: same as omitting it (HTTP API + workers).",
    )

    args = parser.parse_args()
    if args.command is not None and args.command != "all":
        parser.error(f"unknown command {args.command!r}; omit it or use `all`")
    config_path = Path(args.config).resolve()
    asyncio.run(_run_app_with_workers(config_path, host=args.host, port=args.port))


if __name__ == "__main__":
    main()
