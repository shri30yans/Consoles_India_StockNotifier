from __future__ import annotations

from pathlib import Path

import pytest
import stock_notifier.config_loader as cl


def test_load_jobs_rejects_unknown_website(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "jobs.yaml").write_text(
        "requests:\n"
        "  - {product_key: PS5, website_key: walmart, delay_seconds: 5}\n"
        "playwright: []\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cl, "config_dir", lambda: tmp_path)
    with pytest.raises(ValueError, match="retailers without parsers"):
        cl.load_jobs()


def test_load_products_requires_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cl, "config_dir", lambda: tmp_path)
    with pytest.raises(FileNotFoundError):
        cl.load_products()
