"""DeepSeek V4 analyzer — generates structured competitive intelligence from raw data."""

import json

import structlog
from openai import AsyncOpenAI

from app.config import settings
from app.schemas.report import CompetitorAnalysis

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are a competitive intelligence analyst. You analyze raw data collected 
from various sources (websites, GitHub, Product Hunt, HackerNews, Reddit) about competitor 
companies and produce structured intelligence reports.

Your analysis should be:
- Factual and evidence-based (cite sources)
- Focused on actionable insights
- Organized into clear categories
- Written in a professional but concise tone

Always respond in valid JSON matching the requested schema."""

ANALYSIS_PROMPT_TEMPLATE = """Analyze the following raw data collected about competitor "{competitor_name}" 
over the past week and produce a structured intelligence report.

== RAW DATA ==
{raw_data}
== END RAW DATA ==

Produce a JSON object with the following structure:
{{
    "competitor_name": "{competitor_name}",
    "new_launches": ["list of new products/features they launched this week"],
    "pricing_changes": ["list of any pricing changes detected, including specifics"],
    "new_features": ["list of new features or capabilities they announced or shipped"],
    "community_sentiment": "Brief summary of how the community (HN/Reddit) perceives them this week",
    "github_activity": "Summary of their GitHub activity (new repos, releases, stars trends)",
    "key_insights": ["list of 3-5 most important strategic takeaways"]
}}

If no data is available for a category, use an empty list [] or empty string "".
Be specific — mention dates, numbers, and concrete details where available.
Respond ONLY with valid JSON, no markdown wrapping."""


class Analyzer:
    """Uses DeepSeek V4 to analyze collected data and generate structured insights.

    Uses the OpenAI-compatible API with base_url pointed at DeepSeek.
    """

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

    def _ensure_client(self) -> AsyncOpenAI:
        if not self._client:
            if not settings.deepseek_api_key:
                raise ValueError("DEEPSEEK_API_KEY is not configured")
            self._client = AsyncOpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
            )
        return self._client

    async def analyze_competitor(
        self, competitor_name: str, raw_data_items: list[dict]
    ) -> CompetitorAnalysis:
        """Analyze collected data for a single competitor.

        Args:
            competitor_name: Name of the competitor.
            raw_data_items: List of dicts with 'source', 'title', 'content' keys.

        Returns:
            CompetitorAnalysis with structured intelligence.
        """
        # Format raw data for the prompt
        raw_data_text = self._format_raw_data(raw_data_items)

        if not raw_data_text.strip():
            logger.info("No data to analyze", competitor=competitor_name)
            return CompetitorAnalysis(
                competitor_name=competitor_name,
                key_insights=["No data collected this period."],
            )

        client = self._ensure_client()

        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            competitor_name=competitor_name,
            raw_data=raw_data_text,
        )

        try:
            response = await client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from DeepSeek")

            # Parse JSON response
            data = json.loads(content)
            analysis = CompetitorAnalysis(**data)

            logger.info(
                "Analysis completed",
                competitor=competitor_name,
                launches=len(analysis.new_launches),
                features=len(analysis.new_features),
                insights=len(analysis.key_insights),
            )
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DeepSeek response: {e}", competitor=competitor_name)
            return CompetitorAnalysis(
                competitor_name=competitor_name,
                key_insights=[f"Analysis failed: could not parse AI response."],
            )
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}", competitor=competitor_name)
            return CompetitorAnalysis(
                competitor_name=competitor_name,
                key_insights=[f"Analysis failed: {str(e)}"],
            )

    @staticmethod
    def _format_raw_data(items: list[dict]) -> str:
        """Format raw data items into a structured text block for the AI prompt."""
        sections = []
        for item in items:
            source = item.get("source", "unknown")
            title = item.get("title", "Untitled")
            content = item.get("content", "")

            # Truncate individual items to keep total prompt manageable
            if len(content) > 5000:
                content = content[:5000] + "\n[... truncated ...]"

            sections.append(
                f"--- Source: {source.upper()} ---\n"
                f"Title: {title}\n"
                f"Content:\n{content}\n"
            )

        return "\n".join(sections)
