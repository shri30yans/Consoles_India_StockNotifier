from __future__ import annotations

from collections.abc import Iterable

from stock_notifier.models import JobSpec, ProductConfig


def validate_monitoring_jobs(products: dict[str, ProductConfig], jobs: Iterable[JobSpec]) -> None:
    """
    Fail fast before any network I/O: every job must resolve to a product
    with a non-empty URL for that retailer.
    """
    for job in jobs:
        product = products.get(job.product_key)
        if product is None:
            raise ValueError(f"Unknown product_key in jobs.yaml: {job.product_key!r}")
        url = product.links.get(job.website_key)
        if not url or not str(url).strip():
            raise ValueError(
                f"Product {job.product_key!r} has no non-empty URL for website_key "
                f"{job.website_key!r} in config/products.yaml",
            )
