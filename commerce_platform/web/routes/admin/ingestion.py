"""Deal ingestion configuration admin endpoints (YAML-backed platform_sources)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException

from commerce_platform.platform.config.merge import load_merged_platform_config
from commerce_platform.platform.store.repos import CatalogRepo
from commerce_platform.web.deps import (
    get_catalog_repo,
    get_config_path,
    require_admin,
)
from commerce_platform.web.schemas import (
    AdminIngestionConfigPatchBody,
    AdminStockFetchPatchBody,
)

router = APIRouter()


def _load_config_dict(config_path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise HTTPException(500, "Invalid config file format")
    return raw


def _write_config_dict(config_path: Path, payload: dict[str, Any]) -> None:
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _merge_stock_fetch_yaml(raw: dict[str, Any], fetch_patch: AdminStockFetchPatchBody) -> None:
    stock_root = raw.get("stock")
    if not isinstance(stock_root, dict):
        stock_root = {}
        raw["stock"] = stock_root
    fetch_obj = stock_root.get("fetch")
    if not isinstance(fetch_obj, dict):
        fetch_obj = {}
        stock_root["fetch"] = fetch_obj
    fetch_obj.update(fetch_patch.model_dump(mode="json"))


@router.get("/ingestion-config")
async def admin_ingestion_config(
    _admin=Depends(require_admin),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
    config_path: Path = Depends(get_config_path),
):
    """YAML-backed deal ingestors (`platform_sources`) and defaults."""
    cfg = await load_merged_platform_config(config_path, catalog_repo)
    return {
        "config_reload_seconds": cfg.platform.config_reload_seconds,
        "defaults_poll_seconds": cfg.defaults.poll_seconds,
        "platform_sources": [s.model_dump(mode="json") for s in cfg.platform_sources],
        "stock_fetch": cfg.stock.fetch.model_dump(mode="json"),
    }


@router.patch("/ingestion-config")
async def admin_patch_ingestion_config(
    body: AdminIngestionConfigPatchBody,
    _admin=Depends(require_admin),
    config_path: Path = Depends(get_config_path),
):
    raw = _load_config_dict(config_path)

    platform_obj = raw.get("platform")
    if not isinstance(platform_obj, dict):
        platform_obj = {}
        raw["platform"] = platform_obj
    defaults_obj = raw.get("defaults")
    if not isinstance(defaults_obj, dict):
        defaults_obj = {}
        raw["defaults"] = defaults_obj

    platform_sources_raw = raw.get("platform_sources")
    if platform_sources_raw is None:
        platform_sources_raw = []
        raw["platform_sources"] = platform_sources_raw
    if not isinstance(platform_sources_raw, list):
        raise HTTPException(400, "platform_sources must be a list in config")

    platform_obj["config_reload_seconds"] = body.config_reload_seconds
    defaults_obj["poll_seconds"] = body.defaults_poll_seconds

    if len(body.platform_sources) != len(platform_sources_raw):
        raise HTTPException(
            400,
            "platform_sources count does not match config file — refresh the admin page and try again",
        )
    for i, patch in enumerate(body.platform_sources):
        row = platform_sources_raw[i]
        if not isinstance(row, dict):
            continue
        row["poll_seconds"] = patch.poll_seconds
        row["enabled"] = patch.enabled

    if body.stock_fetch is not None:
        _merge_stock_fetch_yaml(raw, body.stock_fetch)

    _write_config_dict(config_path, raw)
    return {"ok": True}
