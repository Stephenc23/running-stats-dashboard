"""Database URL normalization for local, Docker, and Render deployments."""
from __future__ import annotations

import os
import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def build_database_url_from_components() -> str:
    """Build URL from discrete vars (bypasses Render-linked DATABASE_URL)."""
    from urllib.parse import quote_plus

    host = (os.getenv("POSTGRES_HOST") or os.getenv("PGHOST") or "").strip()
    user = (os.getenv("POSTGRES_USER") or os.getenv("PGUSER") or "").strip()
    password = (os.getenv("POSTGRES_PASSWORD") or os.getenv("PGPASSWORD") or "").strip()
    database = (os.getenv("POSTGRES_DB") or os.getenv("PGDATABASE") or "").strip()
    port = (os.getenv("POSTGRES_PORT") or os.getenv("PGPORT") or "5432").strip()

    if not all([host, user, password, database]):
        return ""

    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


def raw_database_url_from_env() -> str:
    """Prefer component vars, then external URL, then DATABASE_URL."""
    built = build_database_url_from_components()
    if built:
        return built

    external = (os.getenv("DATABASE_EXTERNAL_URL") or "").strip()
    primary = (os.getenv("DATABASE_URL") or "").strip()

    # On Render, ignore linked short internal host if external URL is provided elsewhere
    if os.getenv("RENDER") and primary and is_incomplete_render_host(database_hostname(primary)):
        if external:
            return external
        return primary

    return external or primary


def strip_asyncpg_unsupported_query_params(url: str) -> str:
    """Remove query params asyncpg.connect() does not accept (e.g. sslmode)."""
    parsed = urlparse(url)
    if not parsed.query:
        return url

    params = parse_qs(parsed.query, keep_blank_values=True)
    for key in ("sslmode", "sslrootcert", "sslcert", "sslkey"):
        params.pop(key, None)

    new_query = urlencode(params, doseq=True) if params else ""
    return urlunparse(parsed._replace(query=new_query))


def normalize_database_url(url: str) -> str:
    """Normalize Postgres URL for SQLAlchemy asyncpg."""
    cleaned = url.strip().strip('"').strip("'")
    if not cleaned:
        return cleaned

    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://") :]

    if "+asyncpg" in cleaned:
        normalized = cleaned
    elif "psycopg2" in cleaned:
        normalized = cleaned.replace("postgresql+psycopg2", "postgresql+asyncpg", 1)
    elif cleaned.startswith("postgresql://"):
        normalized = cleaned.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        normalized = cleaned

    return strip_asyncpg_unsupported_query_params(normalized)


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
    """Render external Postgres requires SSL (via connect_args, not sslmode URL param)."""
    host = database_hostname(database_url) or ""
    if "render.com" in host or "render.com" in database_url:
        return {"ssl": True}
    return {}
