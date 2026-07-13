"""APScheduler setup — cron jobs for data collection and report generation."""

from datetime import datetime, timezone

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

logger = structlog.get_logger()

scheduler = AsyncIOScheduler()


async def scheduled_collect():
    """Scheduled job: collect data from all sources for all competitors."""
    from app.database import AsyncSessionLocal
    from app.services.collector_service import CollectorService

    logger.info("Scheduled collection started")
    async with AsyncSessionLocal() as session:
        try:
            service = CollectorService(session)
            summary = await service.collect_all()
            logger.info("Scheduled collection completed", summary=summary)
        except Exception as e:
            logger.error(f"Scheduled collection failed: {e}")


async def scheduled_report():
    """Scheduled job: generate weekly report and send via Telegram."""
    from app.bot.telegram import telegram_bot
    from app.database import AsyncSessionLocal
    from app.services.report_generator import ReportGenerator

    logger.info("Scheduled report generation started")
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
                    logger.info(f"Scheduled report #{report.id} sent successfully")
                else:
                    logger.warning(f"Scheduled report #{report.id} generated but delivery failed")
        except Exception as e:
            logger.error(f"Scheduled report generation failed: {e}")


def setup_scheduler():
    """Configure and start the scheduler with cron jobs.

    Jobs:
    - Data collection: daily at configured hour (default 03:00 UTC)
    - Report generation: weekly on configured day (default Monday 09:00 UTC)
    """
    # Daily data collection
    scheduler.add_job(
        scheduled_collect,
        "cron",
        hour=settings.collect_cron_hour,
        minute=settings.collect_cron_minute,
        id="daily_collect",
        replace_existing=True,
        name="Daily data collection",
    )

    # Weekly report generation
    scheduler.add_job(
        scheduled_report,
        "cron",
        day_of_week=settings.report_cron_day_of_week,
        hour=settings.report_cron_hour,
        minute=settings.report_cron_minute,
        id="weekly_report",
        replace_existing=True,
        name="Weekly report generation",
    )

    scheduler.start()
    logger.info(
        "Scheduler started",
        collect_schedule=f"Daily at {settings.collect_cron_hour:02d}:{settings.collect_cron_minute:02d} UTC",
        report_schedule=(
            f"Every {settings.report_cron_day_of_week} at "
            f"{settings.report_cron_hour:02d}:{settings.report_cron_minute:02d} UTC"
        ),
    )


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
