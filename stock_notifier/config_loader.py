from __future__ import annotations

import os
from pathlib import Path

from stock_notifier.models import AppConfig, JobSpec, ProductConfig, WebsiteConfig
from stock_notifier.retailers import PARSER_SUPPORTED_WEBSITE_KEYS
from stock_notifier.schemas.yaml_models import (
    parse_app_yaml,
    parse_jobs_yaml,
    parse_product_file,
    parse_website_file,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def config_dir() -> Path:
    override = os.environ.get("STOCK_NOTIFIER_CONFIG_DIR")
    if override:
        return Path(override)
    return _repo_root() / "config"


def load_app() -> AppConfig:
    return parse_app_yaml(
        config_dir() / "app.yaml",
        amazon_affiliate_tag_override=os.environ.get("AMAZON_AFFILIATE_TAG"),
    )


def load_products() -> dict[str, ProductConfig]:
    base = config_dir() / "products"
    if not base.is_dir():
        raise FileNotFoundError(
            f"Missing products directory {base}. "
            "Add one YAML file per product (e.g. products/PS5.yaml).",
        )
    paths = sorted(base.glob("*.yaml"))
    if not paths:
        raise FileNotFoundError(f"No product YAML files under {base}")
    out: dict[str, ProductConfig] = {}
    for path in paths:
        p = parse_product_file(path)
        if p.key in out:
            raise ValueError(f"Duplicate product key after load: {p.key!r}")
        out[p.key] = p
    return out


def load_website_configs() -> dict[str, WebsiteConfig]:
    base = config_dir() / "websites"
    out: dict[str, WebsiteConfig] = {}
    for key in sorted(PARSER_SUPPORTED_WEBSITE_KEYS):
        path = base / f"{key}.yaml"
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing website config for supported retailer {key!r}: {path}",
            )
        loaded = parse_website_file(path)
        if loaded.key != key:
            raise ValueError(
                f"Website file {path} has key {loaded.key!r}, expected {key!r}",
            )
        out[key] = loaded
    return out


def _validate_jobs(jobs: list[JobSpec], *, label: str) -> None:
    bad = [j for j in jobs if j.website_key not in PARSER_SUPPORTED_WEBSITE_KEYS]
    if bad:
        details = ", ".join(f"{j.product_key}@{j.website_key}" for j in bad)
        raise ValueError(
            f"{label}: jobs reference retailers without parsers "
            f"(supported: {sorted(PARSER_SUPPORTED_WEBSITE_KEYS)}): {details}",
        )


def load_jobs() -> tuple[list[JobSpec], list[JobSpec]]:
    doc = parse_jobs_yaml(config_dir() / "jobs.yaml")
    requests_jobs = [
        JobSpec("requests", r.product_key, r.website_key, r.delay_seconds) for r in doc.requests
    ]
    playwright_jobs = [
        JobSpec("playwright", r.product_key, r.website_key, r.delay_seconds) for r in doc.playwright
    ]
    _validate_jobs(requests_jobs, label="jobs.yaml requests")
    _validate_jobs(playwright_jobs, label="jobs.yaml playwright")
    return requests_jobs, playwright_jobs
