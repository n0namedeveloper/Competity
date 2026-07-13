"""Website collector — uses Playwright to scrape competitor websites."""

from playwright.async_api import async_playwright

from app.collectors.base import BaseCollector, CollectedItem, CollectorResult


class WebsiteCollector(BaseCollector):
    """Scrapes competitor websites for pricing, changelog, and blog content.

    Uses Playwright (async) for JavaScript-rendered pages.
    Target pages: /, /pricing, /changelog, /blog
    """

    source_name = "website"

    # Pages to scrape relative to the competitor's domain
    TARGET_PATHS = [
        ("/", "Homepage"),
        ("/pricing", "Pricing"),
        ("/changelog", "Changelog"),
        ("/blog", "Blog"),
    ]

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None

    async def setup(self) -> None:
        """Launch headless Chromium browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._log("Browser launched")

    async def teardown(self) -> None:
        """Close browser and Playwright."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._log("Browser closed")

    async def collect(self, competitor) -> CollectorResult:
        """Scrape target pages from the competitor's website."""
        result = CollectorResult()

        if not competitor.domain:
            self._log("Skipping — no domain configured", competitor=competitor.name)
            return result

        if not self._browser:
            await self.setup()

        context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
        )

        for path, page_name in self.TARGET_PATHS:
            url = f"https://{competitor.domain}{path}"
            try:
                page = await context.new_page()
                response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)

                if response and response.ok:
                    # Extract page title
                    title = await page.title()

                    # Extract main content text
                    content = await page.evaluate("""() => {
                        // Remove scripts, styles, nav, footer
                        const remove = document.querySelectorAll(
                            'script, style, nav, footer, header, .cookie-banner, .popup'
                        );
                        remove.forEach(el => el.remove());

                        // Get text from body
                        return document.body ? document.body.innerText.trim() : '';
                    }""")

                    # Truncate very large pages to ~10K chars
                    if len(content) > 10000:
                        content = content[:10000] + "\n\n[... truncated ...]"

                    if content:
                        result.items.append(
                            CollectedItem(
                                source=self.source_name,
                                source_url=url,
                                title=f"{competitor.name} — {page_name}: {title}",
                                content=content,
                            )
                        )
                        self._log(
                            "Page scraped",
                            competitor=competitor.name,
                            page=page_name,
                            chars=len(content),
                        )
                    else:
                        self._log(
                            "Empty content",
                            competitor=competitor.name,
                            page=page_name,
                        )
                else:
                    status = response.status if response else "no response"
                    self._log(
                        "Page not accessible",
                        competitor=competitor.name,
                        page=page_name,
                        status=status,
                    )

                await page.close()

            except Exception as e:
                error_msg = f"Failed to scrape {url}: {e}"
                result.errors.append(error_msg)
                self._log_error(error_msg, competitor=competitor.name)

        await context.close()
        return result
