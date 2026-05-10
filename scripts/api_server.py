#!/usr/bin/env python3
"""Start the FastAPI server."""

from pathlib import Path

from commerce_platform.platform.config.loader import load
from commerce_platform.web.config import load_web_config
from commerce_platform.web.main import create_app
from dotenv import load_dotenv

load_dotenv(Path(".env"), override=True)
config = load(Path("config.yaml"))
web_cfg = load_web_config(admin_emails=config.admin_emails)
app = create_app("config.yaml", web_cfg)

if __name__ == "__main__":
    import uvicorn

    print("")
    print("=" * 60)
    print("  Deal Discovery — API Server")
    print("=" * 60)
    print("")
    print("Starting on http://0.0.0.0:8000")
    print("")
    print("Next steps:")
    print("  1. Open http://localhost:8000/deals in browser")
    print("  2. Wait 60 seconds for first deal discovery")
    print("")
    print("To stop: Ctrl+C")
    print("")

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
