"""Run, splits, and dashboard schemas."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RunPointResponse(BaseModel):
    """Single GPS point in a run."""

    id: int
    run_id: int
    sequence: int
    latitude: Decimal
    longitude: Decimal
    elevation_m: float | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class SplitResponse(BaseModel):
    """Per-kilometer split."""

    id: int
    run_id: int
    split_index: int
    distance_km: float
    duration_seconds: float
    pace_min_per_km: float
    elevation_gain_m: float | None

    model_config = ConfigDict(from_attributes=True)


class RunCreate(BaseModel):
    """Input for creating a run (e.g. from upload)."""

    title: str | None = None


class RunResponse(BaseModel):
    """Full run with optional points and splits."""

    id: int
    user_id: int
    title: str | None
    started_at: datetime
    ended_at: datetime | None
    distance_km: float | None
    duration_seconds: float | None
    avg_pace_min_per_km: float | None
    elevation_gain_m: float | None
    elevation_loss_m: float | None
    source_file: str | None
    created_at: datetime
    points: list[RunPointResponse] = []
    splits: list[SplitResponse] = []

    model_config = ConfigDict(from_attributes=True)


class RunSummary(BaseModel):
    """Summary of a run for list views."""

    id: int
    user_id: int
    title: str | None
    started_at: datetime
    distance_km: float | None
    duration_seconds: float | None
    avg_pace_min_per_km: float | None
    elevation_gain_m: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    """Aggregate stats for dashboard."""

    total_runs: int
    total_distance_km: float
    total_duration_seconds: float
    avg_pace_min_per_km: float | None
    total_elevation_gain_m: float
    runs_this_week: int
    runs_this_month: int
