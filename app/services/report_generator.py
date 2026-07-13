"""Report generator — creates weekly structured reports from AI analysis."""

from datetime import date, datetime, timedelta, timezone

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collected_data import CollectedData
from app.models.competitor import Competitor
from app.models.report import Report
from app.schemas.report import CompetitorAnalysis, WeeklyReport
from app.services.analyzer import Analyzer

logger = structlog.get_logger()


class ReportGenerator:
    """Generates weekly intelligence reports by analyzing collected data with DeepSeek V4.

    Flow:
    1. Fetches all collected data for the reporting period
    2. Groups by competitor
    3. Sends each competitor's data to DeepSeek for analysis
    4. Combines analyses into a unified report
    5. Generates Markdown for Telegram delivery
    6. Saves report to PostgreSQL
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.analyzer = Analyzer()

    async def generate_weekly_report(
        self,
        period_end: date | None = None,
    ) -> Report:
        """Generate a weekly report covering the last 7 days.

        Args:
            period_end: End date of the reporting period (default: today).

        Returns:
            Saved Report model instance.
        """
        if period_end is None:
            period_end = date.today()
        period_start = period_end - timedelta(days=7)

        logger.info(f"Generating report for {period_start} — {period_end}")

        # Fetch active competitors
        result = await self.session.execute(
            select(Competitor).where(Competitor.is_active.is_(True))
        )
        competitors = result.scalars().all()

        if not competitors:
            logger.warning("No active competitors — generating empty report")

        # Analyze each competitor
        analyses: list[CompetitorAnalysis] = []

        for competitor in competitors:
            # Fetch collected data for this competitor in the period
            data_result = await self.session.execute(
                select(CollectedData).where(
                    and_(
                        CollectedData.competitor_id == competitor.id,
                        CollectedData.collected_at >= datetime(
                            period_start.year, period_start.month, period_start.day,
                            tzinfo=timezone.utc,
                        ),
                        CollectedData.collected_at <= datetime(
                            period_end.year, period_end.month, period_end.day,
                            23, 59, 59, tzinfo=timezone.utc,
                        ),
                    )
                )
            )
            collected_items = data_result.scalars().all()

            if not collected_items:
                logger.info(f"No data for {competitor.name} in this period — skipping analysis")
                analyses.append(CompetitorAnalysis(
                    competitor_name=competitor.name,
                    key_insights=["No data collected this period."],
                ))
                continue

            # Format data for analyzer
            raw_data = [
                {
                    "source": item.source,
                    "title": item.title or "",
                    "content": item.content,
                }
                for item in collected_items
            ]

            analysis = await self.analyzer.analyze_competitor(competitor.name, raw_data)
            analyses.append(analysis)

        # Build the full report
        weekly_report = WeeklyReport(
            period_start=period_start,
            period_end=period_end,
            competitors=analyses,
            executive_summary=self._generate_executive_summary(analyses),
        )

        # Generate markdown
        markdown = self._render_markdown(weekly_report)

        # Save to DB
        report = Report(
            period_start=period_start,
            period_end=period_end,
            content_markdown=markdown,
            content_json=weekly_report.model_dump(mode="json"),
            status="draft",
        )
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)

        logger.info(f"Report #{report.id} generated successfully")
        return report

    @staticmethod
    def _generate_executive_summary(analyses: list[CompetitorAnalysis]) -> str:
        """Generate a brief executive summary from all analyses."""
        total_launches = sum(len(a.new_launches) for a in analyses)
        total_features = sum(len(a.new_features) for a in analyses)
        total_pricing = sum(len(a.pricing_changes) for a in analyses)
        active_competitors = [a.competitor_name for a in analyses if a.new_launches or a.new_features]

        parts = []
        if total_launches:
            parts.append(f"{total_launches} new launches detected")
        if total_features:
            parts.append(f"{total_features} new features")
        if total_pricing:
            parts.append(f"{total_pricing} pricing changes")
        if active_competitors:
            parts.append(f"Most active: {', '.join(active_competitors[:3])}")

        return ". ".join(parts) if parts else "Quiet week — no significant activity detected."

    @staticmethod
    def _render_markdown(report: WeeklyReport) -> str:
        """Render the report as Markdown suitable for Telegram."""
        lines = [
            f"📊 *Competitive Intelligence Report*",
            f"📅 Period: {report.period_start} → {report.period_end}",
            "",
            f"*Executive Summary:* {report.executive_summary}",
            "",
        ]

        for analysis in report.competitors:
            lines.append(f"━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"🏢 *{analysis.competitor_name}*")
            lines.append("")

            if analysis.new_launches:
                lines.append("🚀 *New Launches:*")
                for item in analysis.new_launches:
                    lines.append(f"  • {item}")
                lines.append("")

            if analysis.pricing_changes:
                lines.append("💰 *Pricing Changes:*")
                for item in analysis.pricing_changes:
                    lines.append(f"  • {item}")
                lines.append("")

            if analysis.new_features:
                lines.append("✨ *New Features:*")
                for item in analysis.new_features:
                    lines.append(f"  • {item}")
                lines.append("")

            if analysis.github_activity:
                lines.append(f"🐙 *GitHub:* {analysis.github_activity}")
                lines.append("")

            if analysis.community_sentiment:
                lines.append(f"💬 *Community:* {analysis.community_sentiment}")
                lines.append("")

            if analysis.key_insights:
                lines.append("🔑 *Key Insights:*")
                for item in analysis.key_insights:
                    lines.append(f"  • {item}")
                lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("_Generated by Competity Bot_")

        return "\n".join(lines)
