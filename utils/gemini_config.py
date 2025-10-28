import os
from typing import Literal
import google.generativeai as genai

class GeminiConfig:
    """Centralized Gemini model configuration"""
    
    # Available models from your earlier list
    FLASH = "gemini-2.5-flash"
    PRO = "gemini-2.5-pro"
    LITE = "gemini-2.5-flash-lite"
    
    # Model assignments for different tasks
    CONTENT_MODEL = PRO      # Use PRO for high-quality content
    SCORING_MODEL = FLASH    # Use FLASH for fast scoring
    ANALYSIS_MODEL = PRO     # Use PRO for detailed analysis
    
    @classmethod
    def configure(cls):
        """Configure Gemini with API key"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        genai.configure(api_key=api_key)
    
    @classmethod
    def get_model(cls, model_type: Literal["content", "scoring", "analysis"] = "content"):
        """Get appropriate model for task"""
        cls.configure()
        
        models = {
            "content": cls.CONTENT_MODEL,
            "scoring": cls.SCORING_MODEL,
            "analysis": cls.ANALYSIS_MODEL
        }
        
        model_name = models.get(model_type, cls.FLASH)
        return genai.GenerativeModel(model_name)