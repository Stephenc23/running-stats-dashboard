"""Run CRUD, upload GPX, get run details and dashboard stats."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models.run import Run, RunPoint, Split
from app.models.user import User
from app.schemas.run import DashboardStats, RunResponse, RunSummary
from app.services.gps_processor import process_gpx_string
from app.services.pace_calculator import compute_elevation, compute_pace_and_splits

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[RunSummary])
async def list_runs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 50,
    offset: int = 0,
) -> list[Run]:
    result = await db.execute(
        select(Run)
        .where(Run.user_id == current_user.id)
        .order_by(Run.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    runs = list(result.scalars().all())
    return runs


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardStats:
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Total runs and aggregates
    total_r = await db.execute(
        select(
            func.count(Run.id).label("count"),
            func.coalesce(func.sum(Run.distance_km), 0).label("distance"),
            func.coalesce(func.sum(Run.duration_seconds), 0).label("duration"),
            func.coalesce(func.sum(Run.elevation_gain_m), 0).label("elevation"),
        ).where(Run.user_id == current_user.id)
    )
    row = total_r.one()
    total_runs = row.count or 0
    total_distance_km = float(row.distance or 0)
    total_duration_seconds = float(row.duration or 0)
    total_elevation_gain_m = float(row.elevation or 0)

    # Average pace (weighted by distance)
    if total_distance_km > 0 and total_duration_seconds > 0:
        avg_pace_min_per_km = (total_duration_seconds / 60.0) / total_distance_km
    else:
        avg_pace_min_per_km = None

    # Runs this week / month
    week_r = await db.execute(
        select(func.count(Run.id)).where(Run.user_id == current_user.id, Run.started_at >= week_ago)
    )
    month_r = await db.execute(
        select(func.count(Run.id)).where(Run.user_id == current_user.id, Run.started_at >= month_ago)
    )
    runs_this_week = week_r.scalar() or 0
    runs_this_month = month_r.scalar() or 0

    return DashboardStats(
        total_runs=total_runs,
        total_distance_km=round(total_distance_km, 2),
        total_duration_seconds=round(total_duration_seconds, 2),
        avg_pace_min_per_km=round(avg_pace_min_per_km, 2) if avg_pace_min_per_km is not None else None,
        total_elevation_gain_m=round(total_elevation_gain_m, 2),
        runs_this_week=runs_this_week,
        runs_this_month=runs_this_month,
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Run:
    result = await db.execute(
        select(Run)
        .where(Run.id == run_id, Run.user_id == current_user.id)
        .options(selectinload(Run.points), selectinload(Run.splits))
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_run(
    run_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    result = await db.execute(select(Run).where(Run.id == run_id, Run.user_id == current_user.id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    await db.delete(run)
    await db.flush()


@router.post("/upload-gpx", response_model=RunResponse)
async def upload_gpx(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(..., description="GPX file"),
    title: str | None = None,
) -> Run:
    """Create a run by uploading a GPX file (multipart/form-data, key 'file')."""
    content = await file.read()
    try:
        gpx_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be UTF-8 text (GPX XML)")
    run = await _process_and_save_run(
        db, current_user.id, gpx_content, title, source_filename=file.filename or "upload.gpx"
    )
    result = await db.execute(
        select(Run)
        .where(Run.id == run.id)
        .options(selectinload(Run.points), selectinload(Run.splits))
    )
    return result.scalar_one()


async def _process_and_save_run(
    db: AsyncSession,
    user_id: int,
    gpx_content: str,
    title: str | None,
    source_filename: str | None,
) -> Run:
    """Parse GPX, compute stats/splits, persist Run + points + splits."""
    data = process_gpx_string(gpx_content)
    started_at = data["started_at"]
    ended_at = data["ended_at"]
    points_data = data["points"]

    if not points_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GPX contains no track points")

    pace_result = compute_pace_and_splits(points_data, started_at, ended_at)
    gain, loss = compute_elevation(points_data)

    run = Run(
        user_id=user_id,
        title=title or (started_at.strftime("%Y-%m-%d %H:%M") if started_at else None),
        started_at=started_at,
        ended_at=ended_at,
        distance_km=pace_result["distance_km"],
        duration_seconds=pace_result["duration_seconds"],
        avg_pace_min_per_km=pace_result["avg_pace_min_per_km"],
        elevation_gain_m=gain,
        elevation_loss_m=loss,
        source_file=source_filename,
        raw_data_stored=False,
    )
    db.add(run)
    await db.flush()

    for seq, p in enumerate(points_data):
        pt = RunPoint(
            run_id=run.id,
            sequence=seq,
            latitude=p["lat"],
            longitude=p["lon"],
            elevation_m=p.get("elevation_m"),
            timestamp=p["timestamp"],
        )
        db.add(pt)
    await db.flush()

    for s in pace_result["splits"]:
        split = Split(
            run_id=run.id,
            split_index=s["split_index"],
            distance_km=s["distance_km"],
            duration_seconds=s["duration_seconds"],
            pace_min_per_km=s["pace_min_per_km"],
            elevation_gain_m=s.get("elevation_gain_m"),
        )
        db.add(split)
    await db.flush()
    await db.refresh(run)
    return run
