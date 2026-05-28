"""Database URL normalization for local, Docker, and Render deployments."""
from __future__ import annotations

import os
import re
from urllib.parse import urlparse


def raw_database_url_from_env() -> str:
    """Prefer explicit external URL over generic DATABASE_URL (Render may inject a bad one)."""
    external = (os.getenv("DATABASE_EXTERNAL_URL") or "").strip()
    primary = (os.getenv("DATABASE_URL") or "").strip()
    return external or primary


def normalize_database_url(url: str) -> str:
    """Normalize Postgres URL for SQLAlchemy asyncpg."""
    cleaned = url.strip().strip('"').strip("'")
    if not cleaned:
        return cleaned

    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://") :]

    if "+asyncpg" in cleaned:
        return cleaned
    if "psycopg2" in cleaned:
        return cleaned.replace("postgresql+psycopg2", "postgresql+asyncpg", 1)
    if cleaned.startswith("postgresql://"):
        return cleaned.replace("postgresql://", "postgresql+asyncpg://", 1)
    return cleaned


def database_hostname(url: str) -> str | None:
    try:
        return urlparse(url).hostname
    except Exception:
        return None


def is_incomplete_render_host(host: str | None) -> bool:
    """Render internal hostnames look like dpg-xxxx-a without a domain suffix."""
    if not host:
        return True
    if host in {"db", "localhost"}:
        return True
    return bool(re.fullmatch(r"dpg-[a-z0-9]+-a", host))


def asyncpg_connect_args(database_url: str) -> dict:
    """Render external Postgres requires SSL."""
    if "sslmode=require" in database_url or "render.com" in database_url:
        return {"ssl": True}
    return {}
