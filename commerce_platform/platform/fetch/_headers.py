"""Browser profile pool — reads ua_db.csv, builds full request headers at runtime.

ua_db.csv is the single source of truth for user agents.  Add rows to that
file (or run scripts/generate_ua_db.py) to expand the pool.  This module
derives all other headers (Sec-CH-UA, Accept, Sec-Fetch-*) from the
browser/version/platform columns so each profile is internally consistent.

Public API
----------
random_profile()           -> BrowserProfile
build_request_headers()    -> dict[str, str]
"""

from __future__ import annotations

import csv
import random
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

_CSV_PATH = Path(__file__).parent / "ua_db.csv"

_ACCEPT_LANGS = [
    "en-IN,en;q=0.9",
    "en-IN,en-US;q=0.9,en;q=0.8",
    "en-US,en;q=0.9,en-IN;q=0.8",
    "en-GB,en;q=0.9,en-IN;q=0.8",
    "en-IN,en;q=0.8,hi;q=0.7",
]

_ACCEPT_HTML_CHROME = (
    "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,image/apng,*/*;q=0.8,"
    "application/signed-exchange;v=b3;q=0.7"
)
_ACCEPT_HTML_FF = (
    "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,*/*;q=0.8"
)

_PLAT_CH = {"windows": "Windows", "mac": "macOS", "linux": "Linux"}


class BrowserProfile(TypedDict):
    ua: str
    browser: str
    version: int
    platform: str
    accept: str
    accept_language: str
    sec_ch_ua: str | None           # None for Firefox
    sec_ch_ua_mobile: str | None
    sec_ch_ua_platform: str | None


def _build_profile(row: dict[str, str]) -> BrowserProfile:
    browser  = row["browser"]
    version  = int(row["version"])
    platform = row["platform"]
    ua       = row["ua"]

    if browser == "firefox":
        return BrowserProfile(
            ua=ua, browser=browser, version=version, platform=platform,
            accept=_ACCEPT_HTML_FF,
            accept_language=random.choice(_ACCEPT_LANGS),
            sec_ch_ua=None, sec_ch_ua_mobile=None, sec_ch_ua_platform=None,
        )

    if browser == "edge":
        brand = (f'"Microsoft Edge";v="{version}", '
                 f'"Chromium";v="{version}", "Not-A.Brand";v="8"')
    else:  # chrome
        brand = (f'"Chromium";v="{version}", '
                 f'"Google Chrome";v="{version}", "Not-A.Brand";v="8"')

    plat_name = _PLAT_CH.get(platform, "Windows")

    return BrowserProfile(
        ua=ua, browser=browser, version=version, platform=platform,
        accept=_ACCEPT_HTML_CHROME,
        accept_language=random.choice(_ACCEPT_LANGS),
        sec_ch_ua=brand,
        sec_ch_ua_mobile="?0",
        sec_ch_ua_platform=f'"{plat_name}"',
    )


@lru_cache(maxsize=1)
def _load() -> list[BrowserProfile]:
    with _CSV_PATH.open(newline="", encoding="utf-8") as f:
        return [_build_profile(row) for row in csv.DictReader(f)]


def random_profile() -> BrowserProfile:
    """Pick a random desktop browser profile from ua_db.csv."""
    return random.choice(_load())


def build_request_headers(
    profile: BrowserProfile,
    *,
    referer: str | None = None,
) -> dict[str, str]:
    """Build a complete, internally consistent HTTP header dict."""
    fetch_site = "same-origin" if referer else "none"

    h: dict[str, str] = {
        "User-Agent":              profile["ua"],
        "Accept":                  profile["accept"],
        "Accept-Language":         profile["accept_language"],
        "Accept-Encoding":         "gzip, deflate, br",
        "Connection":              "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest":          "document",
        "Sec-Fetch-Mode":          "navigate",
        "Sec-Fetch-Site":          fetch_site,
    }

    if not referer:
        h["Sec-Fetch-User"] = "?1"

    if profile["sec_ch_ua"] is not None:
        h["Sec-CH-UA"]          = profile["sec_ch_ua"]
        h["Sec-CH-UA-Mobile"]   = profile["sec_ch_ua_mobile"] or "?0"
        h["Sec-CH-UA-Platform"] = profile["sec_ch_ua_platform"] or '"Windows"'

    if referer:
        h["Referer"] = referer

    return h
