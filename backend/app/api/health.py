"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app import __version__
from app.core.config import Settings
from app.core.dependencies import get_app_settings
from app.database.mongodb import mongodb
from app.schemas.health import DependencyStatus, HealthData, HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness and dependency health check",
)
async def health_check(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    mongo_ok = await mongodb.ping()
    dependencies = [
        DependencyStatus(
            name="mongodb",
            status="ok" if mongo_ok else "unavailable",
            detail=(
                "Ping succeeded"
                if mongo_ok
                else "Unable to reach MongoDB. Check Atlas Network Access IP whitelist or local MONGODB_URI."
            ),
        )
    ]
    overall = "ok" if mongo_ok else "degraded"

    return HealthResponse(
        data=HealthData(
            status=overall,
            app=settings.app_name,
            version=__version__,
            environment=settings.app_env,
            dependencies=dependencies,
        )
    )
