"""Pydantic schemas for Report."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ReportOut(BaseModel):
    """Schema for report response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    period_start: date
    period_end: date
    content_markdown: str
    content_json: dict
    status: str
    sent_at: datetime | None
    created_at: datetime


class CompetitorAnalysis(BaseModel):
    """Structured analysis for a single competitor from DeepSeek."""

    competitor_name: str
    new_launches: list[str] = []
    pricing_changes: list[str] = []
    new_features: list[str] = []
    community_sentiment: str = ""
    github_activity: str = ""
    key_insights: list[str] = []


class WeeklyReport(BaseModel):
    """Full weekly report structure."""

    period_start: date
    period_end: date
    competitors: list[CompetitorAnalysis] = []
    executive_summary: str = ""
