#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module configures and provides access to Google Gemini models.
"""

import logging
from typing import Literal

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from config import config

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DIVERSITY_CONFIG: Tuned for content variety in LinkedIn posts
# Research-backed parameters (Google Dev, Sept 2024; Anthropic, 2024)
# NOTE: Gemini 2.5 Flash doesn't support presence_penalty/frequency_penalty
# NOTE: max_output_tokens increased to 4096 to ensure complete responses
# ═══════════════════════════════════════════════════════════════════════════════
DIVERSITY_CONFIG = GenerationConfig(
    temperature=0.9,           # Higher for creative variety (default ~0.7)
    top_p=0.92,                # Nucleus sampling - broader token selection
    max_output_tokens=4096,    # Increased from 1024 - prompt is large, need room for response
)


class GeminiConfig:
    """Centralized Gemini model configuration and access."""

    # Model aliases - Production Ready (December 2024)
    # IMPORTANT: Avoid -exp (experimental) models - they have rate limits even on paid tiers
    FLASH_2 = "gemini-2.0-flash"  # GA stable - fast, reliable
    FLASH_2_5 = "gemini-2.5-flash"  # Fastest + most capable Flash model
    PRO_2_5 = "gemini-2.5-pro"  # Most intelligent for complex tasks
    
    # Model assignments - Production configuration
    CONTENT_MODEL = FLASH_2_5  # Best for content generation (fast + smart)
    SCORING_MODEL = FLASH_2_5  # Same model for scoring consistency
    ANALYSIS_MODEL = FLASH_2  # Fast analysis tasks

    _configured = False

    @classmethod
    def configure(cls):
        """
        Configure the Gemini client with the API key from the central config.

        Raises:
            ValueError: If the Google API key is not found.
        """
        if cls._configured:
            return

        api_key = config.GOOGLE_API_KEY
        if not api_key:
            logger.critical("GOOGLE_API_KEY not found. Gemini features will be disabled.")
            raise ValueError("GOOGLE_API_KEY not found in configuration.")

        genai.configure(api_key=api_key)
        cls._configured = True
        logger.info("[OK] Gemini 2.5 Flash configured for speed.")

    @classmethod
    def get_model(cls, model_type: Literal["content", "scoring", "analysis"] = "content"):
        """
        Get the appropriate generative model for a given task.

        Args:
            model_type: The type of task for which to get the model.

        Returns:
            A configured generative model instance.
        """
        cls.configure()  # Ensure client is configured

        model_map = {
            "content": cls.CONTENT_MODEL,
            "scoring": cls.SCORING_MODEL,
            "analysis": cls.ANALYSIS_MODEL,
        }

        model_name = model_map.get(model_type, cls.FLASH_2)
        logger.info(f"Using model: {model_name} for {model_type}")
        return genai.GenerativeModel(model_name)
