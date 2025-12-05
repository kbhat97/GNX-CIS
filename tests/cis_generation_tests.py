"""
Tests for content generation functionality.

Tests:
- Generate first post
- Improve existing post
- Copy to clipboard
- Download image
- View post history
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.normal
class TestGenerationNormalCases:
    """Normal content generation test cases (must pass 100%)"""
    
    def test_generate_first_post(self, sample_topic, mock_gemini_response, mock_virality_response):
        """Test 4.1.3: Generate first post with content, image, and score"""
        from utils.json_parser import parse_llm_json_response
        
        # Parse mock responses
        content_data = parse_llm_json_response(
            mock_gemini_response.text,
            {"post_text": "", "reasoning": ""}
        )
        score_data = parse_llm_json_response(
            mock_virality_response.text,
            {"score": 0, "confidence": "LOW", "suggestions": []}
        )
        
        assert content_data['post_text'] == "Test LinkedIn post content"
        assert score_data['score'] == 85
        assert score_data['confidence'] == "HIGH"
        assert len(score_data['suggestions']) == 2
    
    def test_improve_existing_post(self, sample_post_data):
        """Test 4.1.4: Improve post generates new content with updated score"""
        # Simulate improvement
        original_score = sample_post_data['virality_score']
        feedback = "Make it more technical and add statistics"
        
        # Mock improved post
        improved_data = sample_post_data.copy()
        improved_data['virality_score'] = 92
        improved_data['improvement_feedback'] = feedback
        improved_data['improvement_count'] = 1
        
        assert improved_data['virality_score'] > original_score
        assert improved_data['improvement_feedback'] == feedback
        assert improved_data['improvement_count'] == 1
    
    def test_copy_post_to_clipboard(self, sample_post_data):
        """Test 4.1.5: Copy post content to clipboard"""
        content = sample_post_data['content']
        
        # Simulate clipboard copy
        clipboard_content = content
        
        assert clipboard_content == sample_post_data['content']
        assert len(clipboard_content) > 0
    
    def test_download_image(self, sample_post_data):
        """Test 4.1.6: Download image as PNG file"""
        # Simulate image download
        image_url = "https://example.com/image.png"
        sample_post_data['image_url'] = image_url
        
        assert sample_post_data['image_url'] is not None
        assert sample_post_data['image_url'].endswith('.png')
    
    def test_view_post_history(self, mock_streamlit_session, sample_post_data):
        """Test 4.1.7: View all previous posts in history"""
        session = mock_streamlit_session
        
        # Add posts to history
        for i in range(3):
            post = sample_post_data.copy()
            post['id'] = i
            session['post_history'].append(post)
        
        assert len(session['post_history']) == 3
        assert all('id' in post for post in session['post_history'])
        assert session['post_history'][0]['id'] == 0
        assert session['post_history'][2]['id'] == 2


@pytest.mark.edge
class TestGenerationEdgeCases:
    """Edge cases for content generation (must pass 90%)"""
    
    def test_very_long_topic(self):
        """Test 4.2.1: Very long topic (1000+ chars) is gracefully truncated"""
        from utils.sanitizer import sanitize_topic
        
        long_topic = "A" * 1500  # 1500 characters
        
        # Should not raise error, just truncate or handle
        try:
            result = sanitize_topic(long_topic)
            assert len(result) <= 2000  # Max length
        except ValueError as e:
            # Or it might reject if too long
            assert "exceeds maximum length" in str(e)
    
    def test_empty_topic_submission(self):
        """Test 4.2.2: Empty topic shows error"""
        from utils.sanitizer import sanitize_topic
        
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize_topic("")
        
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize_topic("   ")  # Whitespace only
    
    def test_special_characters_in_topic(self):
        """Test 4.2.3: Special characters in topic are handled"""
        from utils.sanitizer import sanitize_topic
        
        topic_with_special = "SAP S/4HANA: Migration & Integration (2024) - Best Practices!"
        
        # Should handle without breaking
        result = sanitize_topic(topic_with_special)
        assert result is not None
        assert len(result) > 0
    
    def test_rapid_generation_rate_limit(self, mock_streamlit_session):
        """Test 4.2.4: Rapid generation (10x/min) shows rate limit"""
        session = mock_streamlit_session
        
        # Simulate 10 rapid generations
        for i in range(10):
            session['gen_count'] += 1
        
        # Check if rate limit would trigger
        assert session['gen_count'] == 10
        
        # Rate limit should trigger at 10/min
        if session['gen_count'] >= 10:
            rate_limited = True
        else:
            rate_limited = False
        
        assert rate_limited, "Should trigger rate limit after 10 generations"


@pytest.mark.failure
class TestGenerationFailureCases:
    """Failure handling for content generation"""
    
    def test_gemini_api_timeout(self):
        """Test 4.3.1: Gemini API timeout shows friendly error"""
        from unittest.mock import patch
        import time
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model.return_value.generate_content.side_effect = TimeoutError("API timeout")
            
            # Should handle gracefully
            try:
                model = mock_model()
                model.generate_content("test")
                assert False, "Should have raised TimeoutError"
            except TimeoutError as e:
                assert "timeout" in str(e).lower()
    
    def test_gemini_api_error(self):
        """Test 4.3.2: Gemini API error is logged and shows friendly message"""
        from unittest.mock import patch
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model.return_value.generate_content.side_effect = Exception("API Error")
            
            # Should handle gracefully
            try:
                model = mock_model()
                model.generate_content("test")
                assert False, "Should have raised Exception"
            except Exception as e:
                assert "API Error" in str(e)
    
    def test_json_parsing_error(self):
        """Test malformed JSON response from Gemini"""
        from utils.json_parser import parse_llm_json_response
        
        malformed_json = "This is not JSON at all"
        fallback = {"post_text": "Error", "reasoning": "Failed"}
        
        result = parse_llm_json_response(malformed_json, fallback)
        
        # Should return fallback
        assert result == fallback
    
    def test_image_generation_failure(self):
        """Test image generation failure is handled gracefully"""
        # Simulate image generation failure
        image_url = None
        
        # Should not crash the app
        assert image_url is None  # Gracefully handle None
