#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module configures and provides access to Google Gemini models.
"""

import logging
from typing import Literal

import google.generativeai as genai

from config import config

logger = logging.getLogger(__name__)


class GeminiConfig:
    """Centralized Gemini model configuration and access."""

    # Model aliases - Updated for SPEED (December 2025)
    FLASH_2 = "models/gemini-2.0-flash-exp"  # Fast
    GEMINI_2_5_FLASH = "gemini-2.5-flash"  # Fastest production model
    GEMINI_3_PRO = "gemini-3-pro-preview"  # Slow but most intelligent
    
    # Model assignments - Using 2.5 Flash for SPEED
    CONTENT_MODEL = GEMINI_2_5_FLASH  # 10x faster than 3.0 Pro
    SCORING_MODEL = FLASH_2  # Fast scoring
    ANALYSIS_MODEL = FLASH_2  # Fast analysis

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
        logger.info("✅ Gemini 2.5 Flash configured for speed.")

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
