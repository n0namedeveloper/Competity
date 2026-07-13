"""Pydantic schemas for Competitor."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompetitorCreate(BaseModel):
    """Schema for creating a new competitor."""

    name: str
    domain: str | None = None
    github_org: str | None = None
    producthunt_slug: str | None = None
    keywords: list[str] | None = None


class CompetitorUpdate(BaseModel):
    """Schema for updating an existing competitor."""

    name: str | None = None
    domain: str | None = None
    github_org: str | None = None
    producthunt_slug: str | None = None
    keywords: list[str] | None = None
    is_active: bool | None = None


class CompetitorOut(BaseModel):
    """Schema for competitor response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    domain: str | None
    github_org: str | None
    producthunt_slug: str | None
    keywords: list[str] | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
