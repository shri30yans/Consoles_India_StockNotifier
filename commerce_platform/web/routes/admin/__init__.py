"""Admin API routes, grouped by resource.

External callers import ``router`` from this package; it composes the resource
sub-routers (``requests``, ``catalog``, ``ingestion``, ``deals``, ``settings``)
under one ``/admin`` prefix.
"""

from __future__ import annotations

from fastapi import APIRouter

from commerce_platform.web.routes.admin import (
    catalog as catalog_routes,
)
from commerce_platform.web.routes.admin import (
    deals as deals_routes,
)
from commerce_platform.web.routes.admin import (
    ingestion as ingestion_routes,
)
from commerce_platform.web.routes.admin import (
    requests as request_routes,
)
from commerce_platform.web.routes.admin import (
    settings as settings_routes,
)

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(request_routes.router)
router.include_router(catalog_routes.router)
router.include_router(ingestion_routes.router)
router.include_router(deals_routes.router)
router.include_router(settings_routes.router)

__all__ = ["router"]
