"""FastAPI application entrypoint."""
import os
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, recommendations, runs
from app.config import get_settings

settings = get_settings()

# Project root (where alembic.ini and alembic/ live)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: run DB migrations so tables exist (e.g. on Render)."""
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    if result.returncode != 0:
        raise RuntimeError(f"Migrations failed: {result.stderr or result.stdout}")
    yield


app = FastAPI(
    title=settings.app_name,
    description="Backend for running analytics: GPS processing, pace/splits, training recommendations.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
