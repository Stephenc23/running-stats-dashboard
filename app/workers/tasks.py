"""Celery tasks for async GPX processing."""
from app.config import get_settings
from app.models.run import Run, RunPoint, Split
from app.services.gps_processor import process_gpx_string
from app.services.pace_calculator import compute_elevation, compute_pace_and_splits

# Sync engine/session for Celery (workers typically run sync)
# Use async only from FastAPI; for Celery we run sync SQLAlchemy
settings = get_settings()
sync_database_url = settings.database_url.replace("+asyncpg", "+psycopg2")

# For Celery we need sync driver - add psycopg2 to requirements if using task
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SyncSession
    from sqlalchemy.orm import sessionmaker as sync_sessionmaker

    _engine = create_engine(sync_database_url, pool_pre_ping=True)
    SyncSessionLocal = sync_sessionmaker(autocommit=False, autoflush=False, bind=_engine)
except Exception:
    SyncSessionLocal = None
    _engine = None


def process_gpx_task_sync(user_id: int, gpx_content: str, title: str | None, source_filename: str | None) -> int | None:
    """Synchronous task: parse GPX, compute stats, save Run + points + splits. Returns run_id."""
    if _engine is None or SyncSessionLocal is None:
        return None
    data = process_gpx_string(gpx_content)
    started_at = data["started_at"]
    ended_at = data["ended_at"]
    points_data = data["points"]
    if not points_data:
        return None
    pace_result = compute_pace_and_splits(points_data, started_at, ended_at)
    gain, loss = compute_elevation(points_data)
    with SyncSessionLocal() as session:
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
        session.add(run)
        session.flush()
        for seq, p in enumerate(points_data):
            pt = RunPoint(
                run_id=run.id,
                sequence=seq,
                latitude=p["lat"],
                longitude=p["lon"],
                elevation_m=p.get("elevation_m"),
                timestamp=p["timestamp"],
            )
            session.add(pt)
        for s in pace_result["splits"]:
            split = Split(
                run_id=run.id,
                split_index=s["split_index"],
                distance_km=s["distance_km"],
                duration_seconds=s["duration_seconds"],
                pace_min_per_km=s["pace_min_per_km"],
                elevation_gain_m=s.get("elevation_gain_m"),
            )
            session.add(split)
        session.commit()
        return run.id


# Celery task (optional - app can use sync upload instead)
from app.workers.celery_app import celery_app


@celery_app.task(bind=True)
def process_gpx_async(self, user_id: int, gpx_content: str, title: str | None = None, source_filename: str | None = None):
    """Celery task: process GPX in background. Returns run_id."""
    return process_gpx_task_sync(user_id, gpx_content, title, source_filename or "upload.gpx")
