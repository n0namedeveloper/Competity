"""Report model — generated intelligence reports."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Report(Base):
    """A generated competitive intelligence report."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    content_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft | sent
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Report(id={self.id}, period={self.period_start}..{self.period_end}, "
            f"status='{self.status}')>"
        )
