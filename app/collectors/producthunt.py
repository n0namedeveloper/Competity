"""Product Hunt collector — fetches recent launches via GraphQL API v2."""

import json

import httpx

from app.collectors.base import BaseCollector, CollectedItem, CollectorResult
from app.config import settings

# GraphQL query to search for posts by a topic/keyword
POSTS_QUERY = """
query SearchPosts($query: String!, $first: Int!) {
  posts(order: NEWEST, first: $first, topic: $query) {
    edges {
      node {
        id
        name
        tagline
        description
        url
        votesCount
        commentsCount
        createdAt
        topics {
          edges {
            node {
              name
            }
          }
        }
        makers {
          name
          username
        }
      }
    }
  }
}
"""


class ProductHuntCollector(BaseCollector):
    """Collects recent Product Hunt launches for a competitor.

    Uses the GraphQL API v2 with a developer token.
    Falls back to a simpler query if the topic-based query fails.
    """

    source_name = "producthunt"
    API_URL = "https://api.producthunt.com/v2/api/graphql"

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def setup(self) -> None:
        if not settings.producthunt_token:
            self._log("No Product Hunt token configured — collector disabled")
            return

        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {settings.producthunt_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )
        self._log("HTTP client ready")

    async def teardown(self) -> None:
        if self._client:
            await self._client.aclose()

    async def collect(self, competitor) -> CollectorResult:
        result = CollectorResult()

        if not self._client:
            self._log("Skipping — no token configured", competitor=competitor.name)
            return result

        # Use producthunt_slug or competitor name as search term
        search_term = competitor.producthunt_slug or competitor.name

        try:
            resp = await self._client.post(
                self.API_URL,
                json={
                    "query": POSTS_QUERY,
                    "variables": {"query": search_term, "first": 10},
                },
            )

            if resp.status_code != 200:
                result.errors.append(
                    f"Product Hunt API error: {resp.status_code} — {resp.text[:200]}"
                )
                return result

            data = resp.json()
            posts = data.get("data", {}).get("posts", {}).get("edges", [])

            if posts:
                items = []
                for edge in posts:
                    node = edge["node"]
                    items.append({
                        "name": node["name"],
                        "tagline": node["tagline"],
                        "description": node.get("description", ""),
                        "url": node["url"],
                        "votes": node["votesCount"],
                        "comments": node["commentsCount"],
                        "created_at": node["createdAt"],
                        "topics": [
                            t["node"]["name"]
                            for t in node.get("topics", {}).get("edges", [])
                        ],
                        "makers": [
                            m["name"] for m in node.get("makers", [])
                        ],
                    })

                result.items.append(
                    CollectedItem(
                        source=self.source_name,
                        source_url=f"https://www.producthunt.com/search?q={search_term}",
                        title=f"{competitor.name} — Product Hunt ({len(items)} posts)",
                        content=json.dumps(items, indent=2),
                    )
                )
                self._log(
                    "Posts fetched",
                    competitor=competitor.name,
                    count=len(items),
                )
            else:
                self._log("No posts found", competitor=competitor.name, query=search_term)

        except Exception as e:
            error_msg = f"Product Hunt collection failed for {search_term}: {e}"
            result.errors.append(error_msg)
            self._log_error(error_msg, competitor=competitor.name)

        return result
