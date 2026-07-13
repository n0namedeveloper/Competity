"""GitHub collector — fetches repos, releases, and activity via REST API v3."""

import json
from datetime import datetime, timedelta, timezone

import httpx

from app.collectors.base import BaseCollector, CollectedItem, CollectorResult
from app.config import settings


class GitHubCollector(BaseCollector):
    """Collects GitHub activity for a competitor's organization.

    Fetches:
    - Recent repositories (new or updated)
    - Latest releases across repos
    - Star counts and activity metrics
    """

    source_name = "github"
    API_BASE = "https://api.github.com"

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def setup(self) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        self._client = httpx.AsyncClient(
            base_url=self.API_BASE,
            headers=headers,
            timeout=30.0,
        )
        self._log("HTTP client ready")

    async def teardown(self) -> None:
        if self._client:
            await self._client.aclose()

    async def collect(self, competitor) -> CollectorResult:
        result = CollectorResult()

        if not competitor.github_org:
            self._log("Skipping — no github_org configured", competitor=competitor.name)
            return result

        if not self._client:
            await self.setup()

        org = competitor.github_org
        since = datetime.now(timezone.utc) - timedelta(days=7)

        # ── Fetch public repos ──
        try:
            repos = await self._fetch_repos(org)
            if repos:
                # Find recently updated repos
                recent_repos = [
                    r for r in repos
                    if datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00")) > since
                ]

                if recent_repos:
                    content = json.dumps(
                        [
                            {
                                "name": r["name"],
                                "description": r.get("description", ""),
                                "stars": r["stargazers_count"],
                                "forks": r["forks_count"],
                                "language": r.get("language", ""),
                                "updated_at": r["updated_at"],
                                "created_at": r["created_at"],
                                "is_new": datetime.fromisoformat(
                                    r["created_at"].replace("Z", "+00:00")
                                ) > since,
                            }
                            for r in recent_repos[:20]  # Limit to 20
                        ],
                        indent=2,
                    )

                    result.items.append(
                        CollectedItem(
                            source=self.source_name,
                            source_url=f"https://github.com/{org}",
                            title=f"{competitor.name} — GitHub repos ({len(recent_repos)} recently updated)",
                            content=content,
                        )
                    )
                    self._log(
                        "Repos fetched",
                        competitor=competitor.name,
                        total=len(repos),
                        recent=len(recent_repos),
                    )
        except Exception as e:
            result.errors.append(f"Failed to fetch repos for {org}: {e}")
            self._log_error(f"Repos fetch failed: {e}", competitor=competitor.name)

        # ── Fetch recent releases ──
        try:
            releases = await self._fetch_releases(org, repos[:10] if repos else [])
            recent_releases = [
                r for r in releases
                if datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")) > since
            ]

            if recent_releases:
                content = json.dumps(
                    [
                        {
                            "repo": r["_repo_name"],
                            "tag": r["tag_name"],
                            "name": r.get("name", ""),
                            "body": (r.get("body", "") or "")[:2000],
                            "published_at": r["published_at"],
                            "prerelease": r.get("prerelease", False),
                        }
                        for r in recent_releases
                    ],
                    indent=2,
                )

                result.items.append(
                    CollectedItem(
                        source=self.source_name,
                        source_url=f"https://github.com/{org}",
                        title=f"{competitor.name} — GitHub releases ({len(recent_releases)} new)",
                        content=content,
                    )
                )
                self._log(
                    "Releases fetched",
                    competitor=competitor.name,
                    count=len(recent_releases),
                )
        except Exception as e:
            result.errors.append(f"Failed to fetch releases for {org}: {e}")
            self._log_error(f"Releases fetch failed: {e}", competitor=competitor.name)

        return result

    async def _fetch_repos(self, org: str) -> list[dict]:
        """Fetch public repos for an organization, sorted by updated date."""
        repos = []
        page = 1
        while page <= 3:  # Max 3 pages = 90 repos
            resp = await self._client.get(
                f"/orgs/{org}/repos",
                params={"sort": "updated", "per_page": 30, "page": page, "type": "public"},
            )
            if resp.status_code != 200:
                self._log_error(f"GitHub API error: {resp.status_code}", org=org)
                break
            data = resp.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        return repos

    async def _fetch_releases(self, org: str, repos: list[dict]) -> list[dict]:
        """Fetch latest releases across top repos."""
        all_releases = []
        for repo in repos:
            repo_name = repo["name"]
            try:
                resp = await self._client.get(
                    f"/repos/{org}/{repo_name}/releases",
                    params={"per_page": 5},
                )
                if resp.status_code == 200:
                    releases = resp.json()
                    for r in releases:
                        r["_repo_name"] = repo_name
                    all_releases.extend(releases)
            except Exception:
                continue
        return all_releases
