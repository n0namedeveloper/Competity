import pytest
from app.services.analyzer import Analyzer
from app.schemas.report import CompetitorAnalysis

# Create a mock for the AsyncOpenAI client
class MockChatCompletion:
    def __init__(self, content):
        self.content = content
        
    @property
    def choices(self):
        class Message:
            def __init__(self, content):
                self.content = content
                
        class Choice:
            def __init__(self, content):
                self.message = Message(content)
                
        return [Choice(self.content)]

class MockCompletions:
    def __init__(self, content):
        self.content = content
        
    async def create(self, **kwargs):
        return MockChatCompletion(self.content)

class MockChat:
    def __init__(self, content):
        self.completions = MockCompletions(content)

class MockAsyncOpenAI:
    def __init__(self, content):
        self.chat = MockChat(content)


@pytest.mark.asyncio
async def test_analyze_competitor_success(monkeypatch):
    # Setup mock to return a valid JSON string
    mock_json = '''
    {
        "competitor_name": "TestCorp",
        "new_launches": ["Product X"],
        "pricing_changes": [],
        "new_features": ["Feature Y"],
        "community_sentiment": "Positive",
        "github_activity": "Active",
        "key_insights": ["Good stuff"]
    }
    '''
    analyzer = Analyzer()
    analyzer._client = MockAsyncOpenAI(mock_json)
    
    result = await analyzer.analyze_competitor("TestCorp", [{"source": "website", "content": "launched Product X"}])
    
    assert isinstance(result, CompetitorAnalysis)
    assert result.competitor_name == "TestCorp"
    assert "Product X" in result.new_launches
    assert "Feature Y" in result.new_features

@pytest.mark.asyncio
async def test_analyze_competitor_json_error(monkeypatch):
    # Setup mock to return invalid JSON
    analyzer = Analyzer()
    analyzer._client = MockAsyncOpenAI("Not JSON")
    
    result = await analyzer.analyze_competitor("TestCorp", [{"source": "website", "content": "launched Product X"}])
    
    # Should handle gracefully and return fallback analysis
    assert isinstance(result, CompetitorAnalysis)
    assert result.competitor_name == "TestCorp"
    assert "Analysis failed:" in result.key_insights[0]

@pytest.mark.asyncio
async def test_analyze_competitor_empty_data():
    analyzer = Analyzer()
    
    result = await analyzer.analyze_competitor("TestCorp", [])
    
    # Should return early with no data msg
    assert isinstance(result, CompetitorAnalysis)
    assert "No data collected this period" in result.key_insights[0]
