"""Load and validate config.yaml."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from commerce_platform.platform.config.schema import PlatformConfig

logger = logging.getLogger(__name__)


def load(path: str | Path = "config.yaml") -> PlatformConfig:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p.resolve()}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    config = PlatformConfig.model_validate(raw)
    logger.info(
        "Loaded config: %d products, %d channels, %d platform_sources",
        len(config.products),
        len(config.channels),
        len(config.platform_sources),
    )
    return config
