#!/usr/bin/env python3
"""Regenerate ua_db.csv — 1000 realistic desktop UA rows.

The CSV is the single source of truth for user agents.  Add new rows by hand
or re-run this script with a higher count.  The header-building logic in
_headers.py derives all other request headers (Sec-CH-UA, Accept, etc.)
from the browser/version/platform columns at runtime.

Usage:
    python scripts/generate_ua_db.py            # 1000 rows, seed 42
    python scripts/generate_ua_db.py --n 2000   # 2000 rows
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

CHROME_VERSIONS  = list(range(109, 136))
FIREFOX_VERSIONS = list(range(109, 136))
MAC_VERSIONS = [
    "10_15_7", "11_0", "12_0", "13_0", "13_1", "13_2", "13_3",
    "13_4", "13_5", "13_6", "14_0", "14_1", "14_2", "14_3", "14_4",
]
OUT_PATH = Path(__file__).parent.parent / "commerce_platform" / "platform" / "fetch" / "ua_db.csv"


def _row(browser: str, version: int, platform: str, ua: str) -> dict[str, str]:
    return {"browser": browser, "version": str(version), "platform": platform, "ua": ua}


def generate(n: int, seed: int = 42) -> list[dict[str, str]]:
    random.seed(seed)
    rows: list[dict[str, str]] = []

    shares = {
        "chrome_win": int(n * 0.40),
        "chrome_mac": int(n * 0.20),
        "edge_win":   int(n * 0.20),
        "firefox_win":int(n * 0.10),
        "chrome_linux":n - int(n * 0.90),  # remainder
    }

    for _ in range(shares["chrome_win"]):
        v = random.choice(CHROME_VERSIONS)
        rows.append(_row("chrome", v, "windows",
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{v}.0.0.0 Safari/537.36"))

    for _ in range(shares["chrome_mac"]):
        v, mac = random.choice(CHROME_VERSIONS), random.choice(MAC_VERSIONS)
        rows.append(_row("chrome", v, "mac",
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X {mac}) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{v}.0.0.0 Safari/537.36"))

    for _ in range(shares["edge_win"]):
        v = random.choice(CHROME_VERSIONS)
        rows.append(_row("edge", v, "windows",
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{v}.0.0.0 Safari/537.36 Edg/{v}.0.0.0"))

    for _ in range(shares["firefox_win"]):
        v = random.choice(FIREFOX_VERSIONS)
        rows.append(_row("firefox", v, "windows",
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{v}.0) "
            f"Gecko/20100101 Firefox/{v}.0"))

    for _ in range(shares["chrome_linux"]):
        v = random.choice(CHROME_VERSIONS)
        rows.append(_row("chrome", v, "linux",
            f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{v}.0.0.0 Safari/537.36"))

    random.shuffle(rows)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rows = generate(args.n, args.seed)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["browser", "version", "platform", "ua"])
        writer.writeheader()
        writer.writerows(rows)

    from collections import Counter
    dist = Counter(r["browser"] for r in rows)
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")
    for browser, count in sorted(dist.items()):
        print(f"  {browser}: {count}")
