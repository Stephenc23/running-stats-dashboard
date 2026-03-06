"""Generate personalized training recommendations from run history."""
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run


async def get_recommendations(db: AsyncSession, user_id: int) -> dict[str, Any]:
    """
    Analyze user's recent runs and return personalized recommendations.
    Uses simple rule-based logic: recovery when high volume, tempo when consistent, etc.
    """
    # Recent 30 days
    since = datetime.now(UTC) - timedelta(days=30)
    result = await db.execute(
        select(Run)
        .where(Run.user_id == user_id, Run.started_at >= since, Run.distance_km.isnot(None))
        .order_by(Run.started_at.desc())
        .limit(50)
    )
    runs = list(result.scalars().all())

    # Aggregates
    total_km = sum(r.distance_km or 0 for r in runs)
    total_seconds = sum(r.duration_seconds or 0 for r in runs)
    paces = [r.avg_pace_min_per_km for r in runs if r.avg_pace_min_per_km is not None]
    avg_pace = sum(paces) / len(paces) if paces else None
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    runs_this_week = sum(1 for r in runs if r.started_at >= week_ago)
    runs_last_week = sum(1 for r in runs if two_weeks_ago <= r.started_at < week_ago)

    recommendations: list[dict[str, Any]] = []
    summary_parts: list[str] = []

    if not runs:
        recommendations.append({
            "type": "easy_run",
            "title": "Start with an easy run",
            "description": "You have no recent runs. Begin with 3–5 km at a comfortable pace.",
            "priority": "high",
            "suggested_pace_min_per_km": None,
            "suggested_distance_km": 4.0,
            "suggested_duration_minutes": 30,
            "reason": "No recent activity; building base.",
        })
        return {"recommendations": recommendations, "summary": "Start with an easy 3–5 km run to build a base."}

    # Rule-based recommendations
    if runs_this_week >= 4 and total_km > 40:
        recommendations.append({
            "type": "recovery",
            "title": "Recovery run or rest day",
            "description": "You've had a solid week. Take an easy 20–30 min run or a rest day.",
            "priority": "high",
            "suggested_pace_min_per_km": (avg_pace * 1.15) if avg_pace else None,
            "suggested_distance_km": 3.0,
            "suggested_duration_minutes": 25,
            "reason": "High weekly volume; recovery helps adaptation.",
        })
        summary_parts.append("Prioritize recovery.")

    if avg_pace and runs_this_week <= 2 and runs_last_week >= 2:
        recommendations.append({
            "type": "consistency",
            "title": "Get back to consistency",
            "description": "Two runs this week will help maintain fitness. Aim for 2–3 easy runs.",
            "priority": "medium",
            "suggested_pace_min_per_km": avg_pace * 1.1,
            "suggested_distance_km": 5.0,
            "suggested_duration_minutes": 30,
            "reason": "Fewer runs than last week; consistency is key.",
        })
        summary_parts.append("Focus on consistency.")

    if avg_pace and (not paces or len(runs) >= 5):
        tempo_pace = avg_pace * 0.92 if avg_pace else None
        recommendations.append({
            "type": "tempo",
            "title": "Tempo run",
            "description": "Include one tempo run: 20–25 min at comfortably hard pace.",
            "priority": "medium",
            "suggested_pace_min_per_km": tempo_pace,
            "suggested_distance_km": 5.0,
            "suggested_duration_minutes": 25,
            "reason": "Tempo efforts improve lactate threshold.",
        })
        if "Tempo" not in " ".join(summary_parts):
            summary_parts.append("Add a tempo run.")

    if total_km < 25 and runs_this_week <= 3:
        long_run_km = max(6.0, (total_km / max(len(runs), 1)) * 1.3)
        recommendations.append({
            "type": "long_run",
            "title": "Long run",
            "description": f"One long run of {long_run_km:.1f}–{long_run_km + 2:.1f} km at easy pace.",
            "priority": "high",
            "suggested_pace_min_per_km": avg_pace * 1.1 if avg_pace else None,
            "suggested_distance_km": round(long_run_km, 1),
            "suggested_duration_minutes": int(long_run_km * 6.5),
            "reason": "Building endurance with one longer run per week.",
        })
        summary_parts.append("Include a long run.")

    if not recommendations:
        recommendations.append({
            "type": "easy_run",
            "title": "Easy run",
            "description": "Keep it easy: 4–6 km at a conversational pace.",
            "priority": "medium",
            "suggested_pace_min_per_km": avg_pace,
            "suggested_distance_km": 5.0,
            "suggested_duration_minutes": 35,
            "reason": "Maintain base fitness.",
        })
        summary_parts.append("Easy run recommended.")

    summary = " ".join(summary_parts) if summary_parts else "Stay consistent with your training."
    return {"recommendations": recommendations, "summary": summary}
