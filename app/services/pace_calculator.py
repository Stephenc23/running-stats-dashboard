"""Compute distance, pace, and per-km splits from GPS points."""
from decimal import Decimal
from typing import Any

from geopy.distance import geodesic


def _point_to_tuple(p: dict[str, Any]) -> tuple[float, float]:
    lat = float(p["lat"]) if isinstance(p["lat"], Decimal) else p["lat"]
    lon = float(p["lon"]) if isinstance(p["lon"], Decimal) else p["lon"]
    return (lat, lon)


def _haversine_km(p1: dict[str, Any], p2: dict[str, Any]) -> float:
    return geodesic(_point_to_tuple(p1), _point_to_tuple(p2)).kilometers


def compute_elevation(points: list[dict[str, Any]]) -> tuple[float, float]:
    """
    Compute total elevation gain and loss in meters from points with elevation_m.
    Returns (elevation_gain_m, elevation_loss_m).
    """
    gain = 0.0
    loss = 0.0
    prev_ele: float | None = None
    for p in points:
        ele = p.get("elevation_m")
        if ele is None:
            continue
        if prev_ele is not None:
            diff = ele - prev_ele
            if diff > 0:
                gain += diff
            else:
                loss += -diff
        prev_ele = ele
    return (gain, loss)


def compute_pace_and_splits(
    points: list[dict[str, Any]],
    started_at: Any,
    ended_at: Any,
) -> dict[str, Any]:
    """
    From ordered GPS points and start/end times, compute:
    - total distance_km, duration_seconds, avg_pace_min_per_km
    - splits: per full kilometer (distance_km, duration_seconds, pace_min_per_km)
    """
    if not points or len(points) < 2:
        duration_seconds = 0.0
        if started_at and ended_at:
            duration_seconds = (ended_at - started_at).total_seconds()
        return {
            "distance_km": 0.0,
            "duration_seconds": max(0.0, duration_seconds),
            "avg_pace_min_per_km": None,
            "splits": [],
        }

    segment_km: list[float] = []
    for i in range(1, len(points)):
        segment_km.append(_haversine_km(points[i - 1], points[i]))

    total_km = sum(segment_km)
    start_ts = points[0]["timestamp"]
    end_ts = points[-1]["timestamp"]
    duration_seconds = (end_ts - start_ts).total_seconds()
    if duration_seconds <= 0:
        duration_seconds = 0.0
        avg_pace = None
    else:
        avg_pace = (duration_seconds / 60.0) / total_km if total_km > 0 else None

    # Segment times in seconds
    segment_sec: list[float] = []
    for i in range(1, len(points)):
        dt = (points[i]["timestamp"] - points[i - 1]["timestamp"]).total_seconds()
        segment_sec.append(max(0.0, dt))

    # Build 1km splits: accumulate distance and time, emit a split every 1 km
    splits: list[dict[str, Any]] = []
    dist_accum = 0.0
    time_accum = 0.0
    split_index = 1

    for seg_idx, (d_km, t_sec) in enumerate(zip(segment_km, segment_sec)):
        while d_km > 1e-9 and dist_accum + d_km >= 1.0:
            need = 1.0 - dist_accum
            ratio = need / d_km
            time_for_1km = time_accum + ratio * t_sec
            pace = (time_for_1km / 60.0) / 1.0 if time_for_1km > 0 else 0.0
            splits.append({
                "split_index": split_index,
                "distance_km": 1.0,
                "duration_seconds": round(time_for_1km, 2),
                "pace_min_per_km": round(pace, 2),
                "elevation_gain_m": None,
            })
            split_index += 1
            d_km -= need
            t_sec = (1.0 - ratio) * t_sec
            dist_accum = 0.0
            time_accum = 0.0
        dist_accum += d_km
        time_accum += t_sec

    if dist_accum > 0.01 and duration_seconds > 0:
        total_split_time = sum(s["duration_seconds"] for s in splits)
        remainder_time = duration_seconds - total_split_time
        pace = (remainder_time / 60.0) / dist_accum if dist_accum > 0 else 0.0
        splits.append({
            "split_index": split_index,
            "distance_km": round(dist_accum, 4),
            "duration_seconds": round(remainder_time, 2),
            "pace_min_per_km": round(pace, 2),
            "elevation_gain_m": None,
        })

    return {
        "distance_km": round(total_km, 4),
        "duration_seconds": round(duration_seconds, 2),
        "avg_pace_min_per_km": round(avg_pace, 2) if avg_pace is not None else None,
        "splits": splits,
    }
