"""
Pytest configuration and shared fixtures for CIS tests.
"""

import pytest
import os
import sys
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser"
    }

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response"""
    mock = MagicMock()
    mock.text = '{"post_text": "Test LinkedIn post content", "reasoning": "Test reasoning"}'
    return mock


@pytest.fixture
def mock_virality_response():
    """Mock virality scoring response"""
    mock = MagicMock()
    mock.text = '{"score": 85, "confidence": "HIGH", "suggestions": ["Add more data", "Improve hook"]}'
    return mock


@pytest.fixture
def sample_topic():
    """Sample topic for testing"""
    return "SAP S/4HANA migration best practices for enterprise organizations"


@pytest.fixture
def sample_post_data():
    """Sample post data"""
    return {
        "content": "This is a test LinkedIn post about SAP S/4HANA migration.",
        "reasoning": "Professional tone with technical depth",
        "virality_score": 85,
        "confidence": "HIGH",
        "suggestions": ["Add statistics", "Include call-to-action"],
        "topic": "SAP S/4HANA migration",
        "style": "Professional",
        "image_url": None
    }


@pytest.fixture
def mock_streamlit_session():
    """Mock Streamlit session state"""
    return {
        'post_history': [],
        'gen_count': 0,
        'selected_post_idx': None,
        'compare_mode': False,
        'compare_posts': [],
        'show_improve_form': False,
        'user_preferences': {
            'default_style': 'inspirational',
            'default_tone': 'professional',
            'auto_generate_image': True,
            'show_score_details': True,
            'theme': 'dark'
        }
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables"""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key")
    monkeypatch.setenv("CLERK_SECRET_KEY", "test_clerk_key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_supabase_key")
    monkeypatch.setenv("SENTRY_DSN", "https://test@sentry.io/123")


@pytest.fixture
def mock_content_agent():
    """Mock ContentAgent"""
    agent = MagicMock()
    agent.model = MagicMock()
    agent.model.generate_content = MagicMock()
    return agent


@pytest.fixture
def mock_virality_agent():
    """Mock ViralityAgent"""
    agent = MagicMock()
    agent.model = MagicMock()
    agent.model.generate_content = MagicMock()
    return agent


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "normal: Normal test cases (must pass 100%)"
    )
    config.addinivalue_line(
        "markers", "edge: Edge case tests (must pass 90%)"
    )
    config.addinivalue_line(
        "markers", "failure: Failure handling tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
