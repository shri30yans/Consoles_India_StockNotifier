"""FastAPI user-facing API and static SPA."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from commerce_platform.platform.store.db import Database
from commerce_platform.platform.store.repos import (
    CatalogRepo,
    PriceRepo,
    StockRepo,
    TrackingRepo,
    UserRepo,
)
from commerce_platform.web.bootstrap import maybe_bootstrap_admin
from commerce_platform.web.config import WebConfig
from commerce_platform.web.rate_limit import RateLimiter
from commerce_platform.web.routes import admin as admin_routes
from commerce_platform.web.routes import auth as auth_routes
from commerce_platform.web.routes import health as health_routes
from commerce_platform.web.routes import products as products_routes
from commerce_platform.web.routes import tracking as tracking_routes

logger = logging.getLogger(__name__)


def create_app(
    config_yaml: str | Path,
    web: WebConfig,
    *,
    db: Database | None = None,
) -> FastAPI:
    """Build the FastAPI app.

    ``db``: if provided, must already be opened; the caller closes it after the server stops.
    If omitted, lifespan opens and closes Postgres using ``platform.store`` (``dsn`` or ``DATABASE_URL``).
    """
    config_path = Path(config_yaml).resolve()

    async def _attach_db(app: FastAPI, connection: Database) -> None:
        app.state.db = connection
        app.state.price_repo = PriceRepo(connection.pool)
        app.state.stock_repo = StockRepo(connection.pool)
        app.state.user_repo = UserRepo(connection.pool)
        app.state.tracking_repo = TrackingRepo(connection.pool)
        app.state.catalog_repo = CatalogRepo(connection.pool)
        await maybe_bootstrap_admin(connection, web)
        logger.info("Web API using DB %s", connection.describe_for_logs())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if db is not None:
            await _attach_db(app, db)
            yield
        else:
            from commerce_platform.platform.config.loader import load

            owned = Database(load(config_path).platform.store)
            await owned.open()
            try:
                await _attach_db(app, owned)
                yield
            finally:
                await owned.close()

    app = FastAPI(title="Commerce monitor", lifespan=lifespan)
    app.state.web_config = web
    app.state.rate_limiter = RateLimiter(web.web_requests_per_hour_per_ip)
    app.state.config_path = config_path

    if web.trusted_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(web.trusted_hosts))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(web.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = "/api"
    app.include_router(health_routes.router, prefix=api)
    app.include_router(products_routes.router, prefix=api)
    app.include_router(auth_routes.router, prefix=api)
    app.include_router(auth_routes.me_router, prefix=api)
    app.include_router(tracking_routes.router, prefix=api)
    app.include_router(admin_routes.router, prefix=api)

    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def spa(full_path: str):
            if full_path.startswith("api"):
                raise HTTPException(404)
            index = static_dir / "index.html"
            if index.is_file():
                return FileResponse(index)
            return JSONResponse({"detail": "Frontend not built"}, status_code=404)

    return app
