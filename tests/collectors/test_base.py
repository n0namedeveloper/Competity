import pytest
from app.collectors.base import BaseCollector, CollectorResult, CollectedItem

class MockFailingCollector(BaseCollector):
    source_name = "mock_failing"
    
    def __init__(self, fail_times=2):
        self.fail_times = fail_times
        self.attempts = 0
        
    async def collect(self, competitor) -> CollectorResult:
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise Exception(f"Mock failure on attempt {self.attempts}")
        
        result = CollectorResult()
        result.items.append(CollectedItem(source=self.source_name, source_url="test", content="success"))
        return result


@pytest.mark.asyncio
async def test_base_collector_retry_success():
    """Test that the base collector retries failed collections."""
    from unittest.mock import MagicMock
    competitor = MagicMock()
    competitor.name = "Test"
    
    # Needs to fail 2 times, succeed on 3rd
    collector = MockFailingCollector(fail_times=2)
    
    # We will test the robust_collect wrapper that we plan to add
    # Since we are doing TDD, this method might not exist yet, we write the test assuming it will.
    result = await collector.robust_collect(competitor, max_retries=3, base_delay=0.1)
    
    assert collector.attempts == 3
    assert result.success_count == 1
    assert result.items[0].content == "success"

@pytest.mark.asyncio
async def test_base_collector_retry_failure():
    """Test that it ultimately fails if max_retries is exceeded."""
    from unittest.mock import MagicMock
    competitor = MagicMock()
    competitor.name = "Test"
    
    # Always fails
    collector = MockFailingCollector(fail_times=5)
    
    result = await collector.robust_collect(competitor, max_retries=2, base_delay=0.1)
    
    assert collector.attempts == 3 # 1 initial + 2 retries
    assert result.error_count == 1
    assert "Mock failure" in result.errors[0]
