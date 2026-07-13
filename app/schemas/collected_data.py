"""Pydantic schemas for CollectedData."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CollectedDataOut(BaseModel):
    """Schema for collected data response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_id: int
    source: str
    source_url: str
    title: str | None
    content: str
    content_hash: str
    collected_at: datetime
