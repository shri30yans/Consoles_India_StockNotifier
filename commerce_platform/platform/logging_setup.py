"""Shared logging configuration for CLI workers and tools."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from commerce_platform.platform.config.schema import PlatformMetaConfig


def configure_platform_logging(platform: PlatformMetaConfig, log_dir: str = "logs") -> None:
    """Attach rotating file + stdout handlers; tame noisy libraries when log level is DEBUG."""
    lvl = getattr(logging, platform.log_level.upper(), logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

    root = logging.getLogger()
    root.setLevel(lvl)

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(lvl)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    os.makedirs(log_dir, exist_ok=True)
    fh = RotatingFileHandler(
        os.path.join(log_dir, "platform.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(lvl)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    if lvl <= logging.DEBUG:
        for noisy in (
            "asyncpg",
            "asyncio",
            "httpcore",
            "httpx",
            "aiohttp",
            "aiohttp.client",
            "urllib3",
            "curl_cffi",
        ):
            logging.getLogger(noisy).setLevel(logging.INFO)

    logging.getLogger(__name__).info(
        "Logging enabled at %s — console and %s/platform.log",
        logging.getLevelName(lvl),
        os.path.abspath(log_dir),
    )
