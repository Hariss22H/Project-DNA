"""Health check schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class DependencyStatus(BaseModel):
    name: str
    status: Literal["ok", "degraded", "unavailable"]
    detail: str | None = None


class HealthData(BaseModel):
    status: Literal["ok", "degraded"]
    app: str
    version: str
    environment: str
    dependencies: list[DependencyStatus] = Field(default_factory=list)


class HealthResponse(BaseModel):
    success: bool = True
    data: HealthData
