"""Reports API — endpoints for viewing and generating reports."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.models.report import Report
from app.schemas.report import ReportOut

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/", response_model=list[ReportOut])
async def list_reports(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """List recent reports, newest first."""
    result = await db.execute(
        select(Report).order_by(Report.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single report by ID."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/generate", status_code=202)
async def generate_report(background_tasks: BackgroundTasks):
    """Trigger report generation in the background.

    Returns immediately with 202 Accepted.
    """
    background_tasks.add_task(_generate_report_task)
    return {"status": "accepted", "message": "Report generation started"}


from pydantic import BaseModel
class BulkDeleteRequest(BaseModel):
    report_ids: list[int]

@router.delete("/")
async def bulk_delete_reports(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """Delete multiple reports by their IDs."""
    from sqlalchemy import delete
    await db.execute(delete(Report).where(Report.id.in_(request.report_ids)))
    await db.commit()
    return {"status": "success", "deleted_count": len(request.report_ids)}


async def _generate_report_task():
    """Background task that generates a report and optionally sends it via Telegram."""
    from app.bot.telegram import telegram_bot
    from app.services.report_generator import ReportGenerator

    async with AsyncSessionLocal() as session:
        try:
            generator = ReportGenerator(session)
            report = await generator.generate_weekly_report()

            # Send via Telegram
            if report.content_markdown:
                sent = await telegram_bot.send_report(report.content_markdown)
                if sent:
                    report.status = "sent"
                    from datetime import datetime, timezone
                    report.sent_at = datetime.now(timezone.utc)
                    await session.commit()
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.error(f"Background report generation failed: {e}")
