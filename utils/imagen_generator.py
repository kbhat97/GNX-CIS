#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gemini 3 Pro Image (Nano Banana Pro) Generator for LinkedIn Posts
Uses Google Vertex AI to generate professional business infographics
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from google.cloud import aiplatform
    from vertexai.preview.vision_models import ImageGenerationModel
    from google.cloud import storage
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning("Vertex AI libraries not installed. Image generation will use fallback.")

from config import config
from utils.logger import log_error, log_agent_action

logger = logging.getLogger(__name__)


class ImagenGenerator:
    """Generate professional LinkedIn images using Gemini 3 Pro Image (Nano Banana Pro)"""
    
    def __init__(self):
        """Initialize Imagen generator with Vertex AI"""
        self.enabled = VERTEX_AI_AVAILABLE
        self.model = None
        self.storage_client = None
        self.bucket = None
        
        if self.enabled:
            try:
                # Initialize Vertex AI
                aiplatform.init(
                    project=config.project_id,
                    location=config.GCP_REGION
                )
                
                # Load Gemini 3 Pro Image model (Nano Banana Pro)
                # Best for business infographics with text rendering
                self.model = ImageGenerationModel.from_pretrained("gemini-3.0-pro-image")
                
                logger.info("✅ Gemini 3 Pro Image (Nano Banana Pro) loaded successfully")
                
                # Initialize Cloud Storage
                self.storage_client = storage.Client(project=config.project_id)
                
                # Get or create bucket
                try:
                    self.bucket = self.storage_client.get_bucket(config.GCS_BUCKET_NAME)
                    logger.info(f"✅ Using existing GCS bucket: {config.GCS_BUCKET_NAME}")
                except Exception:
                    # Bucket doesn't exist, create it
                    self.bucket = self.storage_client.create_bucket(
                        config.GCS_BUCKET_NAME,
                        location=config.GCP_REGION
                    )
                    logger.info(f"✅ Created GCS bucket: {config.GCS_BUCKET_NAME}")
                
                logger.info("✅ Gemini 3 Pro Image (Nano Banana Pro) initialized successfully")
                
            except Exception as e:
                log_error(e, "Imagen initialization")
                self.enabled = False
                logger.warning("⚠️ Falling back to PIL-based image generation")
    
    def generate_linkedin_image(
        self, 
        topic: str, 
        headline: str = None,
        style: str = "professional",
        include_stats: bool = False,
        brand_colors: Dict[str, str] = None
    ) -> Optional[str]:
        """
        Generate a professional LinkedIn business infographic
        
        Args:
            topic: The post topic
            headline: Main headline text to display (optional)
            style: Image style (professional, modern, minimalist, bold)
            include_stats: Whether to include statistical visualization
            brand_colors: Dict with 'primary', 'secondary', 'accent' colors
            
        Returns:
            Public URL of the generated image, or None if failed
        """
        if not self.enabled:
            logger.warning("Imagen not available, skipping image generation")
            return None
        
        try:
            # Build the prompt for business infographic
            prompt = self._build_business_infographic_prompt(topic, headline, style, include_stats, brand_colors)
            
            log_agent_action("ImagenGenerator", "Generating LinkedIn business infographic", f"Topic: {topic}")
            
            # Generate image with Gemini 3 Pro Image
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="16:9",  # LinkedIn optimal ratio (1200x675)
                safety_filter_level="block_some"
            )
            
            # Get the generated image
            if not response.images:
                logger.error("No images generated")
                return None
            
            image = response.images[0]
            
            # Upload to GCS
            public_url = self._upload_to_gcs(image, topic)
            
            log_agent_action("ImagenGenerator", "✅ Business infographic generated successfully", f"URL: {public_url}")
            
            return public_url
            
        except Exception as e:
            log_error(e, "Imagen image generation")
            return None
    
    def _build_business_infographic_prompt(
        self,
        topic: str,
        headline: str,
        style: str,
        include_stats: bool,
        brand_colors: Dict[str, str]
    ) -> str:
        """Build prompt for BUSINESS INFOGRAPHIC (not photo)"""
        
        # Default brand colors
        if not brand_colors:
            brand_colors = {
                "primary": "#1a1d43",  # Navy blue
                "secondary": "#ffffff",  # White
                "accent": "#64b5f6"  # Light blue
            }
        
        # Use headline or topic
        text_content = headline if headline else topic
        
        # Build prompt for BUSINESS INFOGRAPHIC
        prompt = f"""Create a professional LinkedIn business infographic image. This MUST be a BUSINESS GRAPHIC, NOT a photograph.

CRITICAL: This is a BUSINESS INFOGRAPHIC for LinkedIn, NOT a photorealistic scene, landscape, or photo.

CONTENT:
- Main headline text: "{text_content}"
- Topic: {topic}
- Display the headline prominently and clearly

VISUAL STYLE:
- Professional business presentation style (like PowerPoint or Keynote slides)
- Clean, modern corporate design
- Suitable for LinkedIn professional audience
- Similar to business dashboards or infographics
- NOT a photograph, NOT a scenic image, NOT realistic imagery

LAYOUT TYPE - Choose ONE:
1. Text-focused: Large headline on solid colored background with minimal graphics
2. Diagram: Flow chart or process diagram with boxes and arrows  
3. Data visualization: Chart or graph showing statistics
4. Split layout: Text on one side, simple icon/graphic on other

DESIGN SPECIFICATIONS:
- Aspect ratio: 16:9 (landscape, 1200x675 pixels)
- Background: Solid color gradient (navy blue to dark blue) OR light gray
- Typography: Large, bold, professional sans-serif font
- Text color: High contrast (white on dark, or dark on light)
- Graphics: Simple icons, shapes, or diagrams (NOT photos)
- Professional business aesthetic

COLOR SCHEME:
- Primary: {brand_colors['primary']} (navy/dark blue)
- Secondary: {brand_colors['secondary']} (white)
- Accent: {brand_colors['accent']} (light blue for highlights)
- Use corporate/professional color palette

TEXT RENDERING:
- Make headline text LARGE and READABLE
- Use professional typography
- High contrast for readability
- Center or left-align based on layout

STYLE KEYWORDS:
- Corporate presentation
- Business infographic
- Professional slide design
- LinkedIn post graphic
- Clean and minimal
- Data visualization style

AVOID:
- Photorealistic images
- Landscapes or scenic photos
- People or faces
- Stock photography look
- Cluttered designs
- Too much text (keep it concise)

EXAMPLES OF CORRECT STYLE:
- PowerPoint title slide with large text
- Business dashboard screenshot
- Flow diagram with boxes and arrows
- Data chart or graph
- Professional quote card
- Corporate announcement graphic

Generate a clean, professional business infographic suitable for a LinkedIn post."""

        if include_stats:
            prompt += "\n\n- Include a data visualization element (chart, graph, or prominent statistic)"
        
        return prompt
    
    def _upload_to_gcs(self, image, topic: str) -> str:
        """Upload generated image to Google Cloud Storage"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c if c.isalnum() else "_" for c in topic[:30])
            filename = f"linkedin_posts/{timestamp}_{safe_topic}.png"
            
            # Create blob
            blob = self.bucket.blob(filename)
            
            # Get image bytes
            image_bytes = image._image_bytes
            
            # Upload with public access
            blob.upload_from_string(
                image_bytes,
                content_type="image/png"
            )
            
            # Make public
            blob.make_public()
            
            public_url = blob.public_url
            logger.info(f"✅ Image uploaded to GCS: {filename}")
            
            return public_url
            
        except Exception as e:
            log_error(e, "GCS upload")
            return None


# Global instance
imagen_generator = ImagenGenerator()


def create_linkedin_image(
    topic: str,
    headline: str = None,
    style: str = "professional"
) -> Optional[str]:
    """
    Convenience function to generate LinkedIn business infographic
    
    Args:
        topic: Post topic
        headline: Main headline text
        style: Visual style
        
    Returns:
        Public URL of generated image
    """
    return imagen_generator.generate_linkedin_image(topic, headline, style)
