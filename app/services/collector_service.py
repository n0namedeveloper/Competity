"""Collector service — orchestrates all data source collectors."""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import BaseCollector, CollectorResult
from app.collectors.github import GitHubCollector
from app.collectors.hackernews import HackerNewsCollector
from app.collectors.producthunt import ProductHuntCollector
from app.collectors.reddit import RedditCollector
from app.collectors.website import WebsiteCollector
from app.models.collected_data import CollectedData
from app.models.competitor import Competitor

logger = structlog.get_logger()


class CollectorService:
    """Orchestrates data collection from all sources for all active competitors.

    Manages collector lifecycle (setup/teardown) and persists collected data.
    Deduplicates by content_hash — if identical content was already collected,
    it is skipped.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._collectors: list[BaseCollector] = [
            WebsiteCollector(),
            GitHubCollector(),
            ProductHuntCollector(),
            HackerNewsCollector(),
            RedditCollector(),
        ]

    async def collect_all(self) -> dict:
        """Run all collectors for all active competitors.

        Returns:
            Summary dict with counts per source.
        """
        # Fetch active competitors
        result = await self.session.execute(
            select(Competitor).where(Competitor.is_active.is_(True))
        )
        competitors = result.scalars().all()

        if not competitors:
            logger.warning("No active competitors found — skipping collection")
            return {"status": "no_competitors", "total": 0}

        logger.info(f"Starting collection for {len(competitors)} competitors")

        # Setup all collectors
        for collector in self._collectors:
            try:
                await collector.setup()
            except Exception as e:
                logger.error(f"Failed to setup {collector.source_name}: {e}")

        summary = {"status": "completed", "competitors": {}, "total_items": 0, "total_errors": 0}

        # Collect for each competitor
        for competitor in competitors:
            comp_summary = {"items": 0, "errors": 0, "sources": {}}

            for collector in self._collectors:
                try:
                    collector_result: CollectorResult = await collector.robust_collect(competitor)

                    # Persist items (deduplicated)
                    saved = await self._save_items(competitor, collector_result)
                    comp_summary["sources"][collector.source_name] = {
                        "collected": collector_result.success_count,
                        "saved": saved,
                        "errors": collector_result.error_count,
                    }
                    comp_summary["items"] += saved
                    comp_summary["errors"] += collector_result.error_count

                except Exception as e:
                    logger.error(
                        f"Collector {collector.source_name} failed for {competitor.name}: {e}"
                    )
                    comp_summary["errors"] += 1
                    comp_summary["sources"][collector.source_name] = {"error": str(e)}

            summary["competitors"][competitor.name] = comp_summary
            summary["total_items"] += comp_summary["items"]
            summary["total_errors"] += comp_summary["errors"]

        # Teardown all collectors
        for collector in self._collectors:
            try:
                await collector.teardown()
            except Exception as e:
                logger.error(f"Failed to teardown {collector.source_name}: {e}")

        await self.session.commit()

        logger.info(
            "Collection completed",
            total_items=summary["total_items"],
            total_errors=summary["total_errors"],
        )
        return summary

    async def _save_items(self, competitor: Competitor, result: CollectorResult) -> int:
        """Save collected items to DB, skipping duplicates by content_hash."""
        saved = 0
        for item in result.items:
            # Check if this exact content already exists
            existing = await self.session.execute(
                select(CollectedData).where(
                    CollectedData.competitor_id == competitor.id,
                    CollectedData.source == item.source,
                    CollectedData.content_hash == item.content_hash,
                )
            )
            if existing.scalar_one_or_none():
                continue

            data = CollectedData(
                competitor_id=competitor.id,
                source=item.source,
                source_url=item.source_url,
                title=item.title,
                content=item.content,
                content_hash=item.content_hash,
            )
            self.session.add(data)
            saved += 1

        return saved
