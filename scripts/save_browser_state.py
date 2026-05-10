#!/usr/bin/env python3
"""One-time setup: open a visible browser, browse Amazon + Flipkart, save cookies.

The saved state (cookies, localStorage) is replayed on every subsequent headless
run so the browser looks like a returning user rather than a fresh session.

Run once (or whenever cookies expire):
    python scripts/save_browser_state.py

The file is written to the path configured in config.yaml:
    stock.fetch.playwright_state_file  (default: .playwright_state.json)

Press Ctrl+C in this terminal when you've finished browsing to save and exit.
"""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(".env"), override=True)


async def main() -> None:
    from commerce_platform.platform.config.loader import load
    from commerce_platform.platform.fetch._headers import random_profile

    config = load(Path("config.yaml"))
    cfg = config.stock.fetch
    state_file = Path(cfg.playwright_state_file or ".playwright_state.json")

    from playwright.async_api import async_playwright

    profile = random_profile()
    print(f"Using profile: {profile['browser']} {profile['version']} / {profile['platform']}")
    print(f"State will be saved to: {state_file}")
    print()
    print("The browser will open.  Browse Amazon and Flipkart naturally for 1-2 minutes.")
    print("Press Ctrl+C here (or close this terminal) when done.")
    print()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=profile["ua"],
            locale=cfg.playwright_locale,
            timezone_id=cfg.playwright_timezone_id,
            viewport={"width": 1366, "height": 768},
            extra_http_headers={"Accept-Language": profile["accept_language"]},
        )

        page = await context.new_page()
        await page.goto("https://www.amazon.in", wait_until="domcontentloaded")

        # Open Flipkart in a second tab
        page2 = await context.new_page()
        await page2.goto("https://www.flipkart.com", wait_until="domcontentloaded")

        print("Browser is open.  Browse normally, then press Ctrl+C to save.")

        stop = asyncio.Event()

        def _on_signal(*_):
            stop.set()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _on_signal)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler for all signals
                pass

        # On Windows fall back to polling
        try:
            await asyncio.wait_for(stop.wait(), timeout=300)
        except asyncio.TimeoutError:
            print("5-minute timeout reached — saving state.")
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass

        state_file.parent.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=str(state_file))
        print(f"\nSaved browser state to {state_file}")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
