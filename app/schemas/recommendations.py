"""Training recommendation schemas."""
from pydantic import BaseModel


class TrainingRecommendation(BaseModel):
    """A single training recommendation."""

    type: str  # e.g. "recovery", "tempo", "long_run", "interval"
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    suggested_pace_min_per_km: float | None = None
    suggested_distance_km: float | None = None
    suggested_duration_minutes: int | None = None
    reason: str


class RecommendationsResponse(BaseModel):
    """Response containing personalized recommendations."""

    user_id: int
    recommendations: list[TrainingRecommendation]
    summary: str  # Short text summary
