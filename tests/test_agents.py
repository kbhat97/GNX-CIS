import pytest
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent
from agents.history_agent import HistoryAgent

@pytest.mark.asyncio
async def test_content_generation():
    """Test content agent generates valid posts"""
    agent = ContentAgent()
    result = await agent.generate_post("AI agents", use_history=False)
    
    assert "post_text" in result
    assert "reasoning" in result
    assert len(result["post_text"]) > 50
    assert result["post_text"].count("#") >= 3  # Has hashtags
    print(f"✅ Content generation test passed")

@pytest.mark.asyncio
async def test_virality_scoring():
    """Test virality agent scores posts"""
    agent = ViralityAgent()
    test_post = """
    Just deployed our latest AI system to production. 
    Key lesson: Always test with real data.
    What's your biggest production challenge?
    #AI #Production
    """
    
    result = await agent.score_post(test_post)
    
    assert "score" in result
    assert 0 <= result["score"] <= 100
    assert "breakdown" in result
    assert "suggestions" in result
    print(f"✅ Virality scoring test passed - Score: {result['score']}/100")

@pytest.mark.asyncio
async def test_history_analysis():
    """Test history agent analyzes posts"""
    agent = HistoryAgent()
    result = await agent.analyze_past_posts(limit=5)
    
    assert "writing_style" in result
    assert "common_topics" in result
    assert isinstance(result["common_topics"], list)
    print(f"✅ History analysis test passed")

@pytest.mark.asyncio
async def test_mock_posts_fallback():
    """Test that mock posts work when API is unavailable"""
    agent = HistoryAgent()
    result = await agent.analyze_past_posts(limit=3)
    
    # Should not crash and should return valid structure
    assert result is not None
    assert "writing_style" in result
    print(f"✅ Mock posts fallback test passed")

def test_configuration():
    """Test configuration is loaded"""
    from config import config
    
    assert config.GOOGLE_API_KEY is not None
    assert config.SUPABASE_URL is not None
    print(f"✅ Configuration test passed")