"""Run, RunPoint, and Split models for GPS and pace data."""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Run(Base):
    """A single run/activity with metadata and computed stats."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Computed metrics
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_pace_min_per_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_gain_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_loss_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Raw file reference (optional)
    source_file: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_data_stored: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="runs")
    points: Mapped[list["RunPoint"]] = relationship(
        "RunPoint", back_populates="run", order_by="RunPoint.sequence", cascade="all, delete-orphan"
    )
    splits: Mapped[list["Split"]] = relationship(
        "Split", back_populates="run", order_by="Split.split_index", cascade="all, delete-orphan"
    )


class RunPoint(Base):
    """Single GPS point in a run (track point)."""

    __tablename__ = "run_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    elevation_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Optional: store as PostGIS point for spatial queries (can be added via migration)
    # geometry = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    run: Mapped["Run"] = relationship("Run", back_populates="points")


class Split(Base):
    """Per-kilometer (or per-mile) split for a run."""

    __tablename__ = "splits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    split_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-based km number

    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    pace_min_per_km: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_gain_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    run: Mapped["Run"] = relationship("Run", back_populates="splits")
