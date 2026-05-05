from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from commerce_platform.platform.config.merge import load_merged_platform_config
from commerce_platform.platform.config.schema import Money
from commerce_platform.platform.store.repos import CatalogRepo, PriceRepo, StockRepo
from commerce_platform.web.deps import get_catalog_repo, get_config_path, get_price_repo, get_stock_repo

router = APIRouter(tags=["products"])


@router.get("/products")
async def list_products(
    sort: str = "updated",
    price_repo: PriceRepo = Depends(get_price_repo),
    stock_repo: StockRepo = Depends(get_stock_repo),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
    config_path: Path = Depends(get_config_path),
):
    """Lightweight index: id, name, aggregate stock, last signal time. Two DB round-trips total."""
    cfg = await load_merged_platform_config(config_path, catalog_repo)
    pairs: list[tuple[str, str]] = []
    for p in cfg.products:
        for w in p.watches:
            pairs.append((p.id, w.source))
    snaps = await price_repo.get_latest_snapshots_batch(pairs)
    states = await stock_repo.get_batch(pairs)

    out: list[dict[str, Any]] = []
    for p in cfg.products:
        any_in_stock = False
        last: str | None = None
        for w in p.watches:
            key = (p.id, w.source)
            snap = snaps.get(key)
            st = states.get(key)
            if snap is not None and snap.in_stock:
                any_in_stock = True
            elif st is not None and st.in_stock:
                any_in_stock = True
            for ts in (snap.captured_at if snap else None, st.last_checked_at if st else None):
                if ts is not None and (last is None or ts > last):
                    last = ts
        out.append(
            {
                "id": p.id,
                "name": p.name,
                "any_in_stock": any_in_stock,
                "last_updated": last,
            }
        )
    sk = sort.lower().strip()
    if sk == "name":
        out.sort(key=lambda r: r["name"].lower())
    else:
        out.sort(key=lambda r: r["last_updated"] or "", reverse=True)
    return out


@router.get("/products/{product_id}")
async def product_detail(
    product_id: str,
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
    config_path: Path = Depends(get_config_path),
):
    cfg = await load_merged_platform_config(config_path, catalog_repo)
    p = next((x for x in cfg.products if x.id == product_id), None)
    if not p:
        raise HTTPException(404, "Unknown product")
    watches = [
        {
            "source": w.source,
            "poll_seconds": cfg.resolve_poll_seconds(w),
            "url": w.url,
        }
        for w in p.watches
    ]
    return {
        "id": p.id,
        "name": p.name,
        "brand": p.brand,
        "category": p.category,
        "colour": p.colour,
        "image_url": p.image_url,
        "watches": watches,
    }


@router.get("/products/{product_id}/status")
async def product_status(
    product_id: str,
    price_repo: PriceRepo = Depends(get_price_repo),
    stock_repo: StockRepo = Depends(get_stock_repo),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
    config_path: Path = Depends(get_config_path),
):
    cfg = await load_merged_platform_config(config_path, catalog_repo)
    if not any(x.id == product_id for x in cfg.products):
        raise HTTPException(404, "Unknown product")
    product = next(x for x in cfg.products if x.id == product_id)
    watch_pairs = [(product_id, w.source) for w in product.watches]
    snaps = await price_repo.get_latest_snapshots_batch(watch_pairs)
    states = await stock_repo.get_batch(watch_pairs)
    rows = []
    for w in product.watches:
        key = (product_id, w.source)
        snap = snaps.get(key)
        st = states.get(key)
        rows.append(
            {
                "retailer": w.source,
                "in_stock": snap.in_stock if snap else (st.in_stock if st else None),
                "price_inr": Money(snap.price_paise).to_rupees() if snap else None,
                "last_scrape_at": snap.captured_at if snap else (st.last_checked_at if st else None),
            }
        )
    return {"product_id": product_id, "retailers": rows}


@router.get("/products/{product_id}/price-series")
async def product_price_series(
    product_id: str,
    retailer: str | None = None,
    days: int = 30,
    price_repo: PriceRepo = Depends(get_price_repo),
    catalog_repo: CatalogRepo = Depends(get_catalog_repo),
    config_path: Path = Depends(get_config_path),
):
    cfg = await load_merged_platform_config(config_path, catalog_repo)
    product = next((x for x in cfg.products if x.id == product_id), None)
    if product is None:
        raise HTTPException(404, "Unknown product")
    sources = {w.source for w in product.watches}
    if retailer is not None and retailer not in sources:
        raise HTTPException(400, "retailer is not watched for this product")
    d = max(1, min(int(days), 90))
    points = await price_repo.list_price_series(
        product_id,
        retailer,
        days=d,
        limit=900,
    )
    return {
        "product_id": product_id,
        "retailer": retailer,
        "days": d,
        "points": [{"price_paise": p.price_paise, "in_stock": p.in_stock, "captured_at": p.captured_at} for p in points],
    }
