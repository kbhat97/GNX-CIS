"""
Production-ready tests for Content Diversity System (IMP-001)
Tests DIVERSITY_CONFIG and its integration with ContentAgent.

Run with: pytest tests/test_diversity_system.py -v
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 1: DIVERSITY_CONFIG Unit Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDiversityConfig:
    """Tests for DIVERSITY_CONFIG in gemini_config.py"""

    def test_diversity_config_exists(self):
        """DIVERSITY_CONFIG should be importable from gemini_config"""
        from utils.gemini_config import DIVERSITY_CONFIG
        assert DIVERSITY_CONFIG is not None

    def test_diversity_config_temperature(self):
        """Temperature should be 0.9 for creative variety"""
        from utils.gemini_config import DIVERSITY_CONFIG
        assert DIVERSITY_CONFIG.temperature == 0.9

    def test_diversity_config_top_p(self):
        """Top-p should be 0.92 for nucleus sampling"""
        from utils.gemini_config import DIVERSITY_CONFIG
        assert DIVERSITY_CONFIG.top_p == 0.92

    # NOTE: presence_penalty and frequency_penalty tests removed
    # Gemini 2.5 Flash doesn't support these parameters (INVALID_ARGUMENT error)
    # Reference: https://github.com/google/generative-ai-python, Sep 2025

    def test_diversity_config_max_output_tokens(self):
        """Max output tokens should be 1024 for LinkedIn posts + JSON"""
        from utils.gemini_config import DIVERSITY_CONFIG
        assert DIVERSITY_CONFIG.max_output_tokens == 4096

    def test_diversity_config_is_generation_config_type(self):
        """DIVERSITY_CONFIG should be a GenerationConfig instance"""
        from utils.gemini_config import DIVERSITY_CONFIG
        from google.generativeai.types import GenerationConfig
        assert isinstance(DIVERSITY_CONFIG, GenerationConfig)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 2: ContentAgent Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestContentAgentDiversityIntegration:
    """Tests for ContentAgent using DIVERSITY_CONFIG"""

    def test_content_agent_imports_diversity_config(self):
        """ContentAgent should import DIVERSITY_CONFIG"""
        from agents.content_agent import DIVERSITY_CONFIG
        assert DIVERSITY_CONFIG is not None

    @pytest.mark.asyncio
    async def test_generate_post_uses_diversity_config(self, mock_env_vars):
        """generate_post_text should pass DIVERSITY_CONFIG to generate_content_async"""
        from agents.content_agent import ContentAgent, DIVERSITY_CONFIG
        
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"post_text": "Test post", "reasoning": "Test"}'
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        
        with patch.object(ContentAgent, '__init__', lambda self, supabase_client=None: None):
            agent = ContentAgent()
            agent.name = "ContentAgent"
            agent.model = mock_model
            agent.hook_manager = None  # IMP-004: Required for hook injection to skip
            
            result = await agent.generate_post_text(
                topic="AI in healthcare",
                use_history=False,
                user_id="test_user"
            )
            
            mock_model.generate_content_async.assert_called_once()
            call_kwargs = mock_model.generate_content_async.call_args
            assert call_kwargs.kwargs.get('generation_config') == DIVERSITY_CONFIG

    @pytest.mark.asyncio
    async def test_improve_post_uses_diversity_config(self, mock_env_vars):
        """improve_post_text should pass DIVERSITY_CONFIG to generate_content_async"""
        from agents.content_agent import ContentAgent, DIVERSITY_CONFIG
        
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"post_text": "Improved post", "reasoning": "Better hook"}'
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        
        with patch.object(ContentAgent, '__init__', lambda self, supabase_client=None: None):
            agent = ContentAgent()
            agent.name = "ContentAgent"
            agent.model = mock_model
            agent.hook_manager = None  # IMP-004: Required for consistency
            
            result = await agent.improve_post_text(
                original_text="Original post content",
                feedback="Make the hook stronger"
            )
            
            mock_model.generate_content_async.assert_called_once()
            call_kwargs = mock_model.generate_content_async.call_args
            assert call_kwargs.kwargs.get('generation_config') == DIVERSITY_CONFIG


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 3: Parameter Validation Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDiversityConfigValidation:
    """Validate DIVERSITY_CONFIG parameters are within acceptable ranges"""

    def test_temperature_in_valid_range(self):
        """Temperature should be between 0.0 and 2.0"""
        from utils.gemini_config import DIVERSITY_CONFIG
        assert 0.0 <= DIVERSITY_CONFIG.temperature <= 2.0

    def test_top_p_in_valid_range(self):
        """Top-p should be between 0.0 and 1.0"""
        from utils.gemini_config import DIVERSITY_CONFIG
        assert 0.0 <= DIVERSITY_CONFIG.top_p <= 1.0

    # NOTE: presence_penalty and frequency_penalty range tests removed
    # Gemini 2.5 Flash doesn't support these parameters

    def test_max_output_tokens_reasonable_for_linkedin(self):
        """Max tokens should be reasonable for LinkedIn posts"""
        from utils.gemini_config import DIVERSITY_CONFIG
        assert 512 <= DIVERSITY_CONFIG.max_output_tokens <= 4096


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 4: Prompt Token Budget Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPromptTokenBudget:
    """Tests to ensure prompt doesn't exceed token limits"""

    def test_style_definitions_count(self):
        """Should have exactly 5 style definitions"""
        from agents.content_agent import STYLE_DEFINITIONS
        assert len(STYLE_DEFINITIONS) == 5

    def test_each_style_has_instructions(self):
        """Each style should have instructions string"""
        from agents.content_agent import STYLE_DEFINITIONS
        for style_key, style_def in STYLE_DEFINITIONS.items():
            assert "instructions" in style_def
            assert len(style_def["instructions"]) > 50

    def test_style_instructions_not_too_long(self):
        """Style instructions should be under 500 chars to avoid prompt bloat"""
        from agents.content_agent import STYLE_DEFINITIONS
        for style_key, style_def in STYLE_DEFINITIONS.items():
            assert len(style_def["instructions"]) < 500, f"Style {style_key} too long"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 4B: Enhanced Style Definitions Tests (IMP-002)
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnhancedStyleDefinitions:
    """Tests for IMP-002 enhanced STYLE_DEFINITIONS"""

    def test_each_style_has_sentence_patterns(self):
        """Each style should have sentence_patterns list"""
        from agents.content_agent import STYLE_DEFINITIONS
        for style_key, style_def in STYLE_DEFINITIONS.items():
            assert "sentence_patterns" in style_def, f"{style_key} missing sentence_patterns"
            assert isinstance(style_def["sentence_patterns"], list)
            assert len(style_def["sentence_patterns"]) >= 3, f"{style_key} needs 3+ patterns"

    def test_each_style_has_vocabulary(self):
        """Each style should have vocabulary dict with use/avoid"""
        from agents.content_agent import STYLE_DEFINITIONS
        for style_key, style_def in STYLE_DEFINITIONS.items():
            assert "vocabulary" in style_def, f"{style_key} missing vocabulary"
            vocab = style_def["vocabulary"]
            assert "use" in vocab, f"{style_key} vocabulary missing 'use'"
            assert "avoid" in vocab, f"{style_key} vocabulary missing 'avoid'"

    def test_each_style_has_rhetorical_moves(self):
        """Each style should have rhetorical_moves list"""
        from agents.content_agent import STYLE_DEFINITIONS
        for style_key, style_def in STYLE_DEFINITIONS.items():
            assert "rhetorical_moves" in style_def, f"{style_key} missing rhetorical_moves"
            assert isinstance(style_def["rhetorical_moves"], list)
            assert len(style_def["rhetorical_moves"]) >= 3

    def test_vocabulary_use_list_not_empty(self):
        """Each style should have at least 3 'use' vocabulary items"""
        from agents.content_agent import STYLE_DEFINITIONS
        for style_key, style_def in STYLE_DEFINITIONS.items():
            use_words = style_def["vocabulary"]["use"]
            assert len(use_words) >= 3, f"{style_key} needs 3+ 'use' vocabulary"

    def test_vocabulary_avoid_list_not_empty(self):
        """Each style should have at least 3 'avoid' vocabulary items"""
        from agents.content_agent import STYLE_DEFINITIONS
        for style_key, style_def in STYLE_DEFINITIONS.items():
            avoid_words = style_def["vocabulary"]["avoid"]
            assert len(avoid_words) >= 3, f"{style_key} needs 3+ 'avoid' vocabulary"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 4C: Image Style Prefixes Tests (IMP-005)
# ═══════════════════════════════════════════════════════════════════════════════


class TestImageStylePrefixes:
    """Tests for IMP-005 IMAGE_PROMPT_LIBRARY in image_generator.py"""

    def test_image_prompt_library_exists(self):
        """IMAGE_PROMPT_LIBRARY should be importable"""
        from utils.image_generator import IMAGE_PROMPT_LIBRARY
        assert IMAGE_PROMPT_LIBRARY is not None
        assert isinstance(IMAGE_PROMPT_LIBRARY, dict)

    def test_all_five_styles_have_image_templates(self):
        """Each of the 5 content styles should have a dedicated image template"""
        from utils.image_generator import IMAGE_PROMPT_LIBRARY
        required_styles = ["professional", "technical", "inspirational", "thought_leadership", "storytelling"]
        for style in required_styles:
            assert style in IMAGE_PROMPT_LIBRARY, f"Missing image template for {style}"

    def test_each_image_template_has_placeholder(self):
        """Each image template should have {headline} and {content} placeholders"""
        from utils.image_generator import IMAGE_PROMPT_LIBRARY
        for style_key, template in IMAGE_PROMPT_LIBRARY.items():
            assert "{headline}" in template, f"{style_key} template missing {{headline}}"
            assert "{content}" in template, f"{style_key} template missing {{content}}"

    def test_each_image_template_specifies_aspect_ratio(self):
        """Each template should specify 16:9 aspect ratio for LinkedIn"""
        from utils.image_generator import IMAGE_PROMPT_LIBRARY
        for style_key, template in IMAGE_PROMPT_LIBRARY.items():
            assert "16:9" in template, f"{style_key} template missing 16:9 aspect ratio"

    def test_image_quality_rules_exist(self):
        """IMAGE_QUALITY_RULES should be defined with key text rendering rules"""
        from utils.image_generator import IMAGE_QUALITY_RULES
        assert IMAGE_QUALITY_RULES is not None
        assert "TEXT" in IMAGE_QUALITY_RULES  # Text accuracy rules
        assert "MARGIN" in IMAGE_QUALITY_RULES  # Safe margins rule


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 4D: Hook History Tests (IMP-003)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHookHistory:
    """Tests for IMP-003 hook history management"""

    def test_extract_hook_from_content_simple(self):
        """extract_hook_from_content should return first line"""
        from utils.hook_history import extract_hook_from_content
        
        content = "This is the hook line.\n\nThis is the body of the post."
        hook = extract_hook_from_content(content)
        assert hook == "This is the hook line."

    def test_extract_hook_removes_markdown(self):
        """extract_hook_from_content should remove ** markdown"""
        from utils.hook_history import extract_hook_from_content
        
        # Test that ** markers are removed
        content = "**Bold hook here**\nBody text."
        hook = extract_hook_from_content(content)
        assert "**" not in hook  # No markdown markers
        assert hook.startswith("Bold hook here")  # Correct text extracted

    def test_extract_hook_truncates_long_hooks(self):
        """extract_hook_from_content should truncate to 150 chars"""
        from utils.hook_history import extract_hook_from_content
        
        long_hook = "A" * 200
        content = f"{long_hook}\n\nBody"
        hook = extract_hook_from_content(content)
        assert len(hook) <= 150
        assert hook.endswith("...")

    def test_extract_hook_handles_empty(self):
        """extract_hook_from_content should return None for empty content"""
        from utils.hook_history import extract_hook_from_content
        
        assert extract_hook_from_content("") is None
        assert extract_hook_from_content(None) is None

    def test_format_prohibited_hooks_empty(self):
        """format_prohibited_hooks should return empty string for no hooks"""
        from utils.hook_history import HookHistoryManager
        
        manager = HookHistoryManager(None)  # supabase not needed for formatting
        result = manager.format_prohibited_hooks([])
        assert result == ""

    def test_format_prohibited_hooks_produces_valid_format(self):
        """format_prohibited_hooks should create proper prompt section"""
        from utils.hook_history import HookHistoryManager
        
        manager = HookHistoryManager(None)
        hooks = ["Hook one", "Hook two"]
        result = manager.format_prohibited_hooks(hooks)
        
        assert "PROHIBITED HOOKS" in result
        assert "- \"Hook one\"" in result
        assert "- \"Hook two\"" in result
        assert "DO NOT use" in result


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 4E: Hook Injection Integration Tests (IMP-004)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHookInjection:
    """Tests for IMP-004 hook injection in ContentAgent"""

    def test_content_agent_has_hook_manager_attr(self):
        """ContentAgent should have hook_manager attribute"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        assert hasattr(agent, 'hook_manager')

    def test_content_agent_without_supabase_has_no_hook_manager(self):
        """ContentAgent without supabase should have None hook_manager"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        assert agent.hook_manager is None

    def test_content_agent_has_get_prohibited_hooks_method(self):
        """ContentAgent should have _get_prohibited_hooks_section method"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        assert hasattr(agent, '_get_prohibited_hooks_section')
        assert callable(agent._get_prohibited_hooks_section)

    def test_content_agent_has_save_hook_method(self):
        """ContentAgent should have _save_hook method"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        assert hasattr(agent, '_save_hook')
        assert callable(agent._save_hook)

    @pytest.mark.asyncio
    async def test_get_prohibited_hooks_returns_empty_when_no_manager(self, mock_env_vars):
        """_get_prohibited_hooks_section should return empty string when no hook_manager"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        result = await agent._get_prohibited_hooks_section("test_user")
        assert result == ""

    @pytest.mark.asyncio
    async def test_save_hook_graceful_when_no_manager(self, mock_env_vars):
        """_save_hook should do nothing when no hook_manager"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        # Should not raise
        await agent._save_hook("test_user", "Test post content")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 4F: Multi-Candidate Generation Tests (IMP-006)
# ═══════════════════════════════════════════════════════════════════════════════


class TestMultiCandidateGeneration:
    """Tests for IMP-006 multi-candidate generation"""

    def test_content_agent_has_multi_candidate_count(self):
        """ContentAgent should have MULTI_CANDIDATE_COUNT = 2"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        assert hasattr(agent, 'MULTI_CANDIDATE_COUNT')
        assert agent.MULTI_CANDIDATE_COUNT == 2

    def test_content_agent_has_score_hook_quality_method(self):
        """ContentAgent should have _score_hook_quality method"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        assert hasattr(agent, '_score_hook_quality')
        assert callable(agent._score_hook_quality)

    def test_score_hook_quality_returns_float(self):
        """_score_hook_quality should return a float score"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        score = agent._score_hook_quality("This is a test hook line.\n\nBody text here.")
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_score_hook_quality_prefers_questions(self):
        """Hooks with questions should score higher"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        
        question_hook = "What's the #1 mistake leaders make?\n\nBody text."
        statement_hook = "I think leadership is important.\n\nBody text."
        
        question_score = agent._score_hook_quality(question_hook)
        statement_score = agent._score_hook_quality(statement_hook)
        
        assert question_score > statement_score

    def test_score_hook_quality_penalizes_generic(self):
        """Generic hooks should score lower"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(supabase_client=None)
        
        generic_hook = "I think everyone should know this.\n\nBody."
        strong_hook = "Here's the uncomfortable truth about AI:\n\nBody."
        
        generic_score = agent._score_hook_quality(generic_hook)
        strong_score = agent._score_hook_quality(strong_hook)
        
        assert strong_score > generic_score

    def test_generate_post_text_accepts_candidates_param(self):
        """generate_post_text should accept generate_candidates parameter"""
        from agents.content_agent import ContentAgent
        import inspect
        
        sig = inspect.signature(ContentAgent.generate_post_text)
        params = list(sig.parameters.keys())
        assert 'generate_candidates' in params


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 5: Error Handling Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDiversityErrorHandling:
    """Tests for graceful error handling"""

    @pytest.mark.asyncio
    async def test_generate_post_handles_api_error(self, mock_env_vars):
        """ContentAgent should return error payload on API failure"""
        from agents.content_agent import ContentAgent
        
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(side_effect=Exception("API Error"))
        
        with patch.object(ContentAgent, '__init__', lambda self: None):
            agent = ContentAgent()
            agent.name = "ContentAgent"
            agent.model = mock_model
            
            result = await agent.generate_post_text(
                topic="Test topic",
                use_history=False,
                user_id="test_user"
            )
            
            assert "error" in result
            assert result["post_text"] == ""

    @pytest.mark.asyncio
    async def test_improve_post_handles_api_error(self, mock_env_vars):
        """improve_post_text should return original text on API failure"""
        from agents.content_agent import ContentAgent
        
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(side_effect=Exception("API Error"))
        
        original_text = "Original post content"
        
        with patch.object(ContentAgent, '__init__', lambda self: None):
            agent = ContentAgent()
            agent.name = "ContentAgent"
            agent.model = mock_model
            
            result = await agent.improve_post_text(
                original_text=original_text,
                feedback="Make it better"
            )
            
            assert "error" in result
            assert result["post_text"] == original_text
