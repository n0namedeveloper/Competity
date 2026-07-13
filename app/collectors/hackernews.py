"""HackerNews collector — uses the Algolia HN Search API (no auth required)."""

import json
import time

import httpx

from app.collectors.base import BaseCollector, CollectedItem, CollectorResult


class HackerNewsCollector(BaseCollector):
    """Collects HackerNews mentions of competitors via Algolia Search API.

    Searches stories and comments by competitor keywords.
    No authentication required.
    """

    source_name = "hackernews"
    API_BASE = "https://hn.algolia.com/api/v1"

    def __init__(self, days_back: int = 7) -> None:
        self._client: httpx.AsyncClient | None = None
        self._days_back = days_back

    async def setup(self) -> None:
        self._client = httpx.AsyncClient(timeout=30.0)
        self._log("HTTP client ready")

    async def teardown(self) -> None:
        if self._client:
            await self._client.aclose()

    async def collect(self, competitor) -> CollectorResult:
        result = CollectorResult()

        if not self._client:
            await self.setup()

        # Build search keywords from competitor config
        keywords = self._build_keywords(competitor)
        if not keywords:
            self._log("Skipping — no keywords configured", competitor=competitor.name)
            return result

        since_timestamp = int(time.time() - self._days_back * 86400)

        for keyword in keywords:
            try:
                items = await self._search(keyword, since_timestamp)
                if items:
                    result.items.append(
                        CollectedItem(
                            source=self.source_name,
                            source_url=f"https://hn.algolia.com/?q={keyword}",
                            title=f"{competitor.name} — HN mentions for '{keyword}' ({len(items)} items)",
                            content=json.dumps(items, indent=2),
                        )
                    )
                    self._log(
                        "Mentions found",
                        competitor=competitor.name,
                        keyword=keyword,
                        count=len(items),
                    )
                else:
                    self._log(
                        "No mentions found",
                        competitor=competitor.name,
                        keyword=keyword,
                    )
            except Exception as e:
                error_msg = f"HN search failed for '{keyword}': {e}"
                result.errors.append(error_msg)
                self._log_error(error_msg, competitor=competitor.name)

        return result

    async def _search(self, query: str, since_timestamp: int) -> list[dict]:
        """Search HN Algolia API for stories and comments."""
        resp = await self._client.get(
            f"{self.API_BASE}/search_by_date",
            params={
                "query": query,
                "tags": "(story,comment)",
                "numericFilters": f"created_at_i>{since_timestamp}",
                "hitsPerPage": 20,
            },
        )

        if resp.status_code != 200:
            self._log_error(f"Algolia API error: {resp.status_code}")
            return []

        hits = resp.json().get("hits", [])
        return [
            {
                "type": "story" if hit.get("title") else "comment",
                "title": hit.get("title", ""),
                "text": (hit.get("comment_text") or hit.get("story_text") or "")[:1000],
                "url": hit.get("url", ""),
                "hn_url": f"https://news.ycombinator.com/item?id={hit['objectID']}",
                "points": hit.get("points"),
                "num_comments": hit.get("num_comments"),
                "author": hit.get("author", ""),
                "created_at": hit.get("created_at", ""),
            }
            for hit in hits
        ]

    @staticmethod
    def _build_keywords(competitor) -> list[str]:
        """Build list of search keywords from competitor config."""
        keywords = list(competitor.keywords or [])
        # Also search by name if not already in keywords
        if competitor.name.lower() not in [k.lower() for k in keywords]:
            keywords.insert(0, competitor.name)
        return keywords[:5]  # Cap at 5 keywords to avoid rate limits
