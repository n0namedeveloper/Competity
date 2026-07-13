"""Base collector — abstract interface for all data source collectors."""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger()


@dataclass
class CollectedItem:
    """A single item collected from a source."""

    source: str
    source_url: str
    title: str | None = None
    content: str = ""

    @property
    def content_hash(self) -> str:
        """SHA256 hash of the content for dedup / change detection."""
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


@dataclass
class CollectorResult:
    """Result from a collector run."""

    items: list[CollectedItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len(self.items)

    @property
    def error_count(self) -> int:
        return len(self.errors)


class BaseCollector(ABC):
    """Abstract base class for all data source collectors.

    Each collector implements the `collect` method that takes a competitor
    and returns a list of collected items.
    """

    source_name: str = "unknown"

    @abstractmethod
    async def collect(self, competitor) -> CollectorResult:
        """Collect data for a given competitor.

        Args:
            competitor: A Competitor model instance.

        Returns:
            CollectorResult with items and any errors.
        """
        ...

    async def setup(self) -> None:
        """Optional setup (e.g., browser launch). Called once before collecting."""
        pass

    async def teardown(self) -> None:
        """Optional teardown (e.g., browser close). Called after collecting."""
        pass

    def _log(self, msg: str, **kwargs) -> None:
        """Structured logging helper."""
        logger.info(msg, collector=self.source_name, **kwargs)

    def _log_error(self, msg: str, **kwargs) -> None:
        """Structured error logging helper."""
        logger.error(msg, collector=self.source_name, **kwargs)

    async def robust_collect(self, competitor, max_retries: int = 2, base_delay: float = 2.0) -> CollectorResult:
        """Execute collect() with exponential backoff retries on failure."""
        import asyncio
        
        attempts = 0
        while attempts <= max_retries:
            attempts += 1
            try:
                return await self.collect(competitor)
            except Exception as e:
                if attempts > max_retries:
                    self._log_error(f"Collection completely failed after {attempts} attempts: {e}", competitor=competitor.name)
                    result = CollectorResult()
                    result.errors.append(f"Failed after {attempts} attempts: {str(e)}")
                    return result
                
                delay = base_delay * (2 ** (attempts - 1))
                self._log_error(f"Collection failed (attempt {attempts}/{max_retries + 1}), retrying in {delay}s: {e}", competitor=competitor.name)
                await asyncio.sleep(delay)
