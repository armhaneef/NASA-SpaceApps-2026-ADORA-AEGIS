"""Phase 2 storage models; clinical rules and API contracts live elsewhere."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Float, ForeignKey
from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.database.connection import Base


class UTCDateTime(TypeDecorator):
    """Reject naive timestamps and restore UTC awareness after SQLite reads."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp must include a timezone")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect):
        return value.replace(tzinfo=timezone.utc) if value is not None else None


class Astronaut(Base):
    __tablename__ = "astronauts"

    astronaut_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    mission_id: Mapped[str] = mapped_column(String(64), index=True)
    mission_role: Mapped[str] = mapped_column(String(100))
    profile_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=lambda: datetime.now(timezone.utc)
    )

    sensor_readings: Mapped[list["SensorReading"]] = relationship(
        back_populates="astronaut", passive_deletes="all"
    )
    health_analyses: Mapped[list["HealthAnalysis"]] = relationship(
        back_populates="astronaut", passive_deletes="all"
    )


class SensorReading(Base):
    """One numeric measurement or summary; waveforms need a future model."""

    __tablename__ = "sensor_readings"
    __table_args__ = (
        Index("ix_readings_astronaut_type_time", "astronaut_id", "measurement_type", "timestamp"),
        Index(
            "uq_sensor_readings_identity",
            "astronaut_id", "timestamp", "measurement_type", "source", "sensor_type",
            unique=True,
        ),
        CheckConstraint("length(trim(unit)) > 0", name="reading_unit_required"),
        CheckConstraint("length(trim(source)) > 0", name="reading_source_required"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    astronaut_id: Mapped[str] = mapped_column(
        ForeignKey("astronauts.astronaut_id", ondelete="RESTRICT")
    )
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime())
    sensor_type: Mapped[str] = mapped_column(String(100))
    measurement_type: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(40))
    source: Mapped[str] = mapped_column(String(200))
    is_simulated: Mapped[bool] = mapped_column(Boolean(create_constraint=True))
    quality: Mapped[str | None] = mapped_column(String(100))

    astronaut: Mapped[Astronaut] = relationship(back_populates="sensor_readings")


class HealthAnalysis(Base):
    """Immutable analysis snapshot, including the full ML output and inputs."""

    __tablename__ = "health_analyses"
    __table_args__ = (
        Index("ix_analysis_astronaut_time", "astronaut_id", "analysis_timestamp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    astronaut_id: Mapped[str] = mapped_column(
        ForeignKey("astronauts.astronaut_id", ondelete="RESTRICT")
    )
    analysis_timestamp: Mapped[datetime] = mapped_column(UTCDateTime())
    result: Mapped[dict[str, Any]] = mapped_column(JSON)

    astronaut: Mapped[Astronaut] = relationship(back_populates="health_analyses")
