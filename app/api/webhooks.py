"""Webhooks API — triggers for n8n and external integrations."""

from fastapi import APIRouter, BackgroundTasks, Request
from telegram import Update

from app.bot.telegram import telegram_bot
from app.database import AsyncSessionLocal

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/collect")
async def webhook_collect(background_tasks: BackgroundTasks):
    """Trigger data collection via webhook (for n8n integration).

    Returns immediately with 202 Accepted.
    """
    background_tasks.add_task(_collect_task)
    return {"status": "accepted", "message": "Data collection started"}


@router.post("/report")
async def webhook_report(background_tasks: BackgroundTasks):
    """Trigger report generation via webhook (for n8n integration).

    Returns immediately with 202 Accepted.
    """
    background_tasks.add_task(_report_task)
    return {"status": "accepted", "message": "Report generation started"}


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Receive Telegram bot updates via webhook.

    Configure Telegram webhook URL to point here:
    POST https://your-domain.com/api/v1/webhooks/telegram
    """
    data = await request.json()
    await telegram_bot.process_update(data)
    return {"status": "ok"}


async def _collect_task():
    """Background task: run all collectors."""
    from app.services.collector_service import CollectorService
    import structlog

    logger = structlog.get_logger()

    async with AsyncSessionLocal() as session:
        try:
            service = CollectorService(session)
            summary = await service.collect_all()
            logger.info("Webhook-triggered collection completed", summary=summary)
        except Exception as e:
            logger.error(f"Webhook collection failed: {e}")


async def _report_task():
    """Background task: generate report and send via Telegram."""
    from app.services.report_generator import ReportGenerator
    from datetime import datetime, timezone
    import structlog

    logger = structlog.get_logger()

    async with AsyncSessionLocal() as session:
        try:
            generator = ReportGenerator(session)
            report = await generator.generate_weekly_report()

            if report.content_markdown:
                sent = await telegram_bot.send_report(report.content_markdown)
                if sent:
                    report.status = "sent"
                    report.sent_at = datetime.now(timezone.utc)
                    await session.commit()

            logger.info(f"Webhook-triggered report #{report.id} generated")
        except Exception as e:
            logger.error(f"Webhook report generation failed: {e}")
