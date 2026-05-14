from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProductionRecord(Base):
    __tablename__ = "production_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), index=True, nullable=False)
    pattern_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    production_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    stitches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    finished_pieces: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    work_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

    machine = relationship("Machine", back_populates="production_records")
