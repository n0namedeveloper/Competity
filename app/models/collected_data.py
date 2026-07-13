"""CollectedData model — raw data collected from various sources."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CollectedData(Base):
    """A single piece of data collected from a source about a competitor."""

    __tablename__ = "collected_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    competitor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # website | github | producthunt | hackernews | reddit
    source_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # SHA256 for dedup + change detection
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    competitor = relationship("Competitor", back_populates="collected_data")

    def __repr__(self) -> str:
        return (
            f"<CollectedData(id={self.id}, source='{self.source}', "
            f"competitor_id={self.competitor_id})>"
        )
