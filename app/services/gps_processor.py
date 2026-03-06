"""Parse GPX and produce structured point data for storage and calculation."""
from datetime import datetime
from decimal import Decimal
from typing import Any

import gpxpy
import gpxpy.gpx
from dateutil import tz


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz.UTC)
    return dt.astimezone(tz.UTC)


def process_gpx_string(gpx_content: str) -> dict[str, Any]:
    """
    Parse GPX XML and return structured data for a single activity.
    Assumes one track with one segment (or merges all points in order).
    Returns dict with:
      - started_at: datetime (UTC)
      - ended_at: datetime | None (UTC)
      - points: list of {lat, lon, elevation_m, timestamp}
    """
    gpx = gpxpy.parse(gpx_content)
    points: list[dict[str, Any]] = []
    started_at: datetime | None = None
    ended_at: datetime | None = None

    for track in gpx.tracks:
        for segment in track.segments:
            for pt in segment.points:
                ts = _ensure_utc(pt.time)
                if ts is None:
                    continue
                if started_at is None or ts < started_at:
                    started_at = ts
                if ended_at is None or ts > ended_at:
                    ended_at = ts
                points.append({
                    "lat": Decimal(str(round(pt.latitude, 7))),
                    "lon": Decimal(str(round(pt.longitude, 7))),
                    "elevation_m": float(pt.elevation) if pt.elevation is not None else None,
                    "timestamp": ts,
                })

    if not points:
        return {"started_at": started_at or datetime.now(tz.UTC), "ended_at": ended_at, "points": []}

    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "points": points,
    }
