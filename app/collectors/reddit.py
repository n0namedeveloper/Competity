"""Reddit collector — uses AsyncPRAW to search for competitor mentions."""

import json

from app.collectors.base import BaseCollector, CollectedItem, CollectorResult
from app.config import settings

# Subreddits to search for competitor mentions
TARGET_SUBREDDITS = [
    "SaaS",
    "startups",
    "programming",
    "technology",
    "webdev",
    "software",
    "Entrepreneur",
]


class RedditCollector(BaseCollector):
    """Collects Reddit posts mentioning competitors via AsyncPRAW.

    Searches target subreddits for recent posts matching keywords.
    Requires Reddit API credentials (client_id, client_secret).
    """

    source_name = "reddit"

    def __init__(self) -> None:
        self._reddit = None

    async def setup(self) -> None:
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            self._log("No Reddit credentials configured — collector disabled")
            return

        try:
            import asyncpraw

            self._reddit = asyncpraw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent,
            )
            self._log("Reddit client ready")
        except ImportError:
            self._log_error("asyncpraw not installed — Reddit collector disabled")

    async def teardown(self) -> None:
        if self._reddit:
            await self._reddit.close()

    async def collect(self, competitor) -> CollectorResult:
        result = CollectorResult()

        if not self._reddit:
            self._log("Skipping — no Reddit client", competitor=competitor.name)
            return result

        keywords = self._build_keywords(competitor)
        if not keywords:
            self._log("Skipping — no keywords configured", competitor=competitor.name)
            return result

        all_posts = []

        for keyword in keywords:
            for sub_name in TARGET_SUBREDDITS:
                try:
                    subreddit = await self._reddit.subreddit(sub_name)
                    async for submission in subreddit.search(
                        keyword, sort="new", time_filter="week", limit=5
                    ):
                        all_posts.append({
                            "subreddit": sub_name,
                            "title": submission.title,
                            "selftext": (submission.selftext or "")[:1000],
                            "url": f"https://reddit.com{submission.permalink}",
                            "score": submission.score,
                            "num_comments": submission.num_comments,
                            "author": str(submission.author) if submission.author else "[deleted]",
                            "created_utc": submission.created_utc,
                            "keyword": keyword,
                        })
                except Exception as e:
                    error_msg = f"Reddit search failed for r/{sub_name} '{keyword}': {e}"
                    result.errors.append(error_msg)
                    self._log_error(error_msg, competitor=competitor.name)

        # Deduplicate by URL
        seen_urls = set()
        unique_posts = []
        for post in all_posts:
            if post["url"] not in seen_urls:
                seen_urls.add(post["url"])
                unique_posts.append(post)

        if unique_posts:
            result.items.append(
                CollectedItem(
                    source=self.source_name,
                    source_url=f"https://www.reddit.com/search/?q={keywords[0]}",
                    title=f"{competitor.name} — Reddit ({len(unique_posts)} posts)",
                    content=json.dumps(unique_posts, indent=2),
                )
            )
            self._log(
                "Posts collected",
                competitor=competitor.name,
                count=len(unique_posts),
            )
        else:
            self._log("No Reddit posts found", competitor=competitor.name)

        return result

    @staticmethod
    def _build_keywords(competitor) -> list[str]:
        """Build list of search keywords from competitor config."""
        keywords = list(competitor.keywords or [])
        if competitor.name.lower() not in [k.lower() for k in keywords]:
            keywords.insert(0, competitor.name)
        return keywords[:3]  # Cap at 3 to avoid rate limits (many subreddits × keywords)
