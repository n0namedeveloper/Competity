"""Competitors API — CRUD endpoints for managing monitored competitors."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.competitor import Competitor
from app.schemas.competitor import CompetitorCreate, CompetitorOut, CompetitorUpdate

router = APIRouter(prefix="/api/v1/competitors", tags=["competitors"])


@router.get("/", response_model=list[CompetitorOut])
async def list_competitors(db: AsyncSession = Depends(get_db)):
    """List all monitored competitors."""
    result = await db.execute(select(Competitor).order_by(Competitor.name))
    return result.scalars().all()


@router.post("/", response_model=CompetitorOut, status_code=201)
async def create_competitor(data: CompetitorCreate, db: AsyncSession = Depends(get_db)):
    """Add a new competitor to monitor."""
    competitor = Competitor(**data.model_dump())
    db.add(competitor)
    await db.flush()
    await db.refresh(competitor)
    return competitor


@router.get("/{competitor_id}", response_model=CompetitorOut)
async def get_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single competitor by ID."""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@router.put("/{competitor_id}", response_model=CompetitorOut)
async def update_competitor(
    competitor_id: int, data: CompetitorUpdate, db: AsyncSession = Depends(get_db)
):
    """Update an existing competitor."""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(competitor, field, value)

    await db.flush()
    await db.refresh(competitor)
    return competitor


@router.delete("/{competitor_id}", status_code=204)
async def delete_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a competitor and all their collected data."""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    await db.delete(competitor)
