import os
import textwrap
import re
from PIL import Image, ImageDraw, ImageFont
import uuid
from datetime import datetime
import emoji
import base64
import io

# Import Supabase Storage for persistent image URLs
try:
    from utils.supabase_storage import upload_image_to_supabase
    SUPABASE_STORAGE_AVAILABLE = True
except ImportError:
    try:
        from supabase_storage import upload_image_to_supabase
        SUPABASE_STORAGE_AVAILABLE = True
    except ImportError:
        SUPABASE_STORAGE_AVAILABLE = False
        print("[IMAGE] Supabase storage not available - using local storage")

# Try to import google genai for Nano Banana support
try:
    from google import genai
    from google.genai import types
    NANO_BANANA_AVAILABLE = True
except ImportError:
    NANO_BANANA_AVAILABLE = False


def _upload_or_fallback(local_path: str, style: str) -> str:
    """
    Upload image to Supabase if available, otherwise return local path.
    
    Args:
        local_path: Local file system path to the image
        style: Style category for organizing uploads
        
    Returns:
        Public URL if upload succeeds, otherwise local absolute path
    """
    if SUPABASE_STORAGE_AVAILABLE:
        try:
            public_url = upload_image_to_supabase(local_path, style)
            if public_url:
                return public_url
        except Exception as e:
            print(f"[WARN] Supabase upload failed, using local path: {e}")
    
    return os.path.abspath(local_path)

IMAGE_HOOK_LIMIT = 250  # Increased for complete sentences

# ═══════════════════════════════════════════════════════════════════
# STYLE-BASED IMAGE PROMPT LIBRARY (Updated Dec 2024)
# Each style has a DISTINCT visual identity - not all handwritten
# Research: Gemini text rendering, explicit text specs, font control
# ═══════════════════════════════════════════════════════════════════

# Quality rules appended to ALL image prompts (research-backed)
IMAGE_QUALITY_RULES = """

=== CRITICAL TEXT RENDERING RULES (MUST FOLLOW) ===
1. TEXT ACCURACY: Render EXACTLY the text provided. Verify spelling character-by-character.
   - Double-check every word before rendering
   - Common errors to avoid: "tention" → "tension", "imprevvement" → "improvement"
   
2. COMPLETE WORDS ONLY: Every word must be fully visible. NO truncated or cut-off text.
   - If text doesn't fit, reduce font size rather than cutting off
   - All characters of every word must be inside the visible image area

3. TEXT FITTING RULES:
   - Maximum 40 characters per line
   - If headline > 40 chars, wrap to 2-3 lines
   - Each line must be centered
   - Use line breaks at natural phrase boundaries

4. SAFE MARGINS: Keep 80px padding from ALL edges
   - No text or design elements within 80px of any border
   - This prevents edge cropping on LinkedIn

5. FONT SPECIFICATIONS:
   - Headlines: Bold, clean sans-serif font (like Montserrat Bold or Roboto Bold)
   - Body text: Regular weight, highly legible
   - Minimum apparent font size: 24pt equivalent

6. ASPECT RATIO: Exactly 16:9 (1200x675 pixels) - landscape orientation for LinkedIn

7. COLOR CONTRAST: Ensure text has strong contrast against background
   - Light text on dark backgrounds OR dark text on light backgrounds
   - Avoid text on busy/patterned areas
"""

IMAGE_PROMPT_LIBRARY = {
    "professional": """Create a CORPORATE INFOGRAPHIC for LinkedIn:

=== CONTENT ===
{content}

=== DESIGN SPECIFICATIONS ===
STYLE: Clean, modern corporate infographic — like a McKinsey or Deloitte presentation slide
FORMAT: 16:9 aspect ratio (1200x675 pixels) for LinkedIn
BACKGROUND: Gradient from dark navy (#1a1a2e) to deep blue (#16213e)

=== LAYOUT ===
1. HEADLINE at top center: "{headline}"
   - Font: Bold, clean sans-serif (like Montserrat Bold)
   - Color: White (#FFFFFF)
   - Size: Large, prominent
   - If > 40 characters, split into 2 centered lines
   
2. KEY DATA POINTS: Display 2-3 metrics in large circular badges
   - Numbers in bold: {metrics}
   - Cyan accent color (#00bcd4) for highlights
   
3. VISUAL ELEMENTS:
   - Clean geometric shapes (circles, rectangles)
   - Thin accent lines connecting elements
   - Simple business icons (chart, lightbulb, target)
   
4. BOTTOM: Subtle call-to-action question

=== STYLE NOTES ===
- Minimalist, sophisticated, executive-ready
- No clip art or cartoons
- Professional color palette: navy, white, cyan accents
- Clean typography hierarchy

DO NOT use stock photos. Create abstract geometric corporate design.""",

    "technical": """Create a TECHNICAL BLUEPRINT DIAGRAM for LinkedIn:

=== CONTENT ===
{content}

=== DESIGN SPECIFICATIONS ===
STYLE: Engineering blueprint / architecture diagram — like an AWS or Google Cloud diagram
FORMAT: 16:9 aspect ratio (1200x675 pixels) for LinkedIn
BACKGROUND: Dark slate (#1e2939) with subtle grid pattern

=== LAYOUT ===
1. HEADLINE at top: "{headline}"
   - Font: Monospace or technical sans-serif (like Source Code Pro or IBM Plex Mono)
   - Color: Bright green (#00ff88) or cyan (#00bcd4)
   - If > 40 characters, split into 2 lines
   
2. DIAGRAM ELEMENTS:
   - Flowchart boxes with rounded corners
   - Connecting arrows with labels
   - Database cylinders, server icons, API boxes
   - Color-coded components (different colors for different parts)
   
3. METRICS: Display key numbers: {metrics}
   - In highlighted boxes or badges
   - Use bright accent colors
   
4. LEGEND: Small component legend in corner

=== STYLE NOTES ===
- Technical, precise, engineering aesthetic
- Neon accents on dark background
- Grid lines for structure
- Clean, readable at a glance

DO NOT use stock photos. Create technical diagram style.""",

    "thought_leadership": """Create a BOLD TYPOGRAPHY POSTER for LinkedIn:

=== CONTENT ===
{content}

=== DESIGN SPECIFICATIONS ===
STYLE: Bold statement poster — like a TED Talk title card or viral quote graphic
FORMAT: 16:9 aspect ratio (1200x675 pixels) for LinkedIn
BACKGROUND: Solid dark background (#121212) OR bold gradient (purple to blue)

=== LAYOUT ===
1. MAIN STATEMENT prominently centered: "{headline}"
   - Font: Extra bold, impactful sans-serif (like Impact or Bebas Neue style)
   - Color: White or bright accent color
   - Size: LARGE — this should dominate the image
   - If > 40 characters, break into 2-3 powerful lines
   - Consider using different colors for key words
   
2. SUPPORTING ELEMENT:
   - Single powerful statistic: {metrics}
   - OR contrasting "myth vs reality" layout
   - Minimal icons if any
   
3. VISUAL EMPHASIS:
   - Underlines, highlights, or boxes on key words
   - Strong color accents (red, orange, or electric blue)
   - Negative space is important

=== STYLE NOTES ===
- Maximum impact, minimal clutter
- Typography IS the design
- Bold, confident, provocative
- Think: billboard, not infographic

DO NOT use stock photos. Typography and color only.""",

    "inspirational": """Create a CLEAN MOTIVATIONAL VISUAL for LinkedIn:

=== DESIGN SPECIFICATIONS ===
STYLE: Premium motivational poster — like a high-end Nike or Apple campaign
FORMAT: 16:9 aspect ratio (1200x675 pixels) for LinkedIn
BACKGROUND: Gradient sunrise colors (warm oranges, golds) with mountain silhouette

=== LAYOUT (MINIMAL - NO STORY TEXT) ===
1. HEADLINE at TOP CENTER: "{headline}"
   - Font: Bold, clean sans-serif
   - Color: White with subtle shadow
   - Large, prominent, easy to read
   - Split into 2 lines if needed
   
2. VISUAL FOCUS (center/bottom):
   - Silhouette of person at mountain peak with arms raised
   - Warm sunrise glow behind them
   - Subtle upward path/stairs leading to peak
   
3. ONE KEY NUMBER (large, accent color): {metrics}
   - Display prominently near the silhouette
   - Use gold or white color
   
4. BOTTOM: Simple hashtags or call-to-action

=== CRITICAL: KEEP IT CLEAN ===
- DO NOT add paragraphs of story text
- DO NOT add body copy or long descriptions
- ONLY: Headline + Visual + One Metric + Hashtags
- Lots of breathing room and negative space
- Premium, inspirational, NOT cluttered

DO NOT use stock photos. Use silhouettes and gradients only.""",

    "storytelling": """Create a NARRATIVE STORYBOARD for LinkedIn:

=== CONTENT ===
{content}

=== DESIGN SPECIFICATIONS ===
STYLE: Story timeline / journey map — like a documentary infographic or case study visual
FORMAT: 16:9 aspect ratio (1200x675 pixels) for LinkedIn
BACKGROUND: Light cream or warm white (#f5f5f0) with subtle texture

=== LAYOUT ===
1. HEADLINE at top: "{headline}"
   - Font: Friendly but professional sans-serif
   - Color: Dark charcoal (#333333)
   - If > 40 characters, split into 2 lines
   
2. STORY FLOW (left to right):
   - 3-4 story beats shown as connected panels or points
   - "BEFORE" → "TURNING POINT" → "AFTER" structure
   - Simple iconic illustrations at each stage
   - Curved connecting line or arrow showing progression
   
3. KEY MOMENT highlighted:
   - Quote bubble or callout box
   - The pivotal insight or lesson
   
4. METRICS as milestones: {metrics}
   - Displayed along the journey path

=== STYLE NOTES ===
- Warm, personal, narrative feel
- Clean illustrations (not photos)
- Easy to follow left-to-right
- Human, relatable, authentic

DO NOT use stock photos. Use illustrations or icons to tell the story."""
}

# Default fallback template
DEFAULT_IMAGE_PROMPT = IMAGE_PROMPT_LIBRARY["storytelling"]


async def generate_ai_image(hook_text: str, topic: str, style: str = "professional", full_content: str = None) -> str:
    """
    Generate an AI image using Gemini 2.5 Flash Image (Nano Banana).
    Uses style-based prompt library for specialized visuals.
    
    Args:
        hook_text: The main hook/headline to feature
        topic: The overall topic for context
        style: The writing style (storytelling, technical, thought_leadership, inspirational, professional)
        full_content: The complete post content for deeper analysis
        
    Returns:
        Path to the saved image, or None if generation fails
    """
    if not NANO_BANANA_AVAILABLE:
        print("Nano Banana not available - google-genai package not installed")
        return None
        
    try:
        # Initialize client with API key from environment
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("GOOGLE_API_KEY not found for Nano Banana")
            return None
            
        client = genai.Client(api_key=api_key)
        
        # Use full content if available, otherwise use topic + hook
        content_to_analyze = full_content or f"{topic}\n\n{hook_text}"
        
        # Extract key elements for dynamic prompt
        metrics = re.findall(r'\d+%|\$[\d,]+[KMB]?|\d+x|\d+\+', content_to_analyze)
        metrics_text = ", ".join(metrics[:5]) if metrics else "key insights and data points"
        
        # Extract first sentence as main headline (cleaned up)
        sentences = content_to_analyze.split('.')
        first_sentence = sentences[0].replace('**', '').replace('\n', ' ').strip()
        # Phase 1 Fix: Shorter headline (50 chars) + word boundary truncation
        if len(first_sentence) > 50:
            truncated = first_sentence[:50].rsplit(' ', 1)[0]
            first_sentence = truncated + "..." if truncated else first_sentence[:50] + "..."
        
        # Remove first sentence from content to avoid duplication in image
        remaining_content = '.'.join(sentences[1:]).strip() if len(sentences) > 1 else content_to_analyze
        
        # Get the appropriate prompt template based on style
        style_key = style.lower().replace(" ", "_")
        prompt_template = IMAGE_PROMPT_LIBRARY.get(style_key, DEFAULT_IMAGE_PROMPT)
        
        # Fill in the template with dynamic content (using remaining_content to avoid headline duplication)
        prompt = prompt_template.format(
            content=remaining_content[:1500],
            headline=first_sentence,
            metrics=metrics_text
        )
        
        # Append quality rules to ensure spelling, margins, and text visibility
        prompt += IMAGE_QUALITY_RULES
        
        print(f"[IMAGE] Generating {style_key} style image with Nano Banana...")

        # Generate image using Nano Banana
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"]
            )
        )
        
        # Extract image from response
        OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "outputs")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data is not None:
                # Use as_image() method to get PIL Image directly
                try:
                    image = part.as_image()
                    # Include style name in filename for easy identification
                    filename = f"ai_post_{style_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
                    output_path = os.path.join(OUTPUT_DIR, filename)
                    image.save(output_path)
                    print(f"[OK] Nano Banana AI image generated: {filename}")
                    return _upload_or_fallback(output_path, style_key)
                except AttributeError:
                    # Fallback: try raw data approach
                    image_data = part.inline_data.data
                    if isinstance(image_data, str):
                        # Base64 encoded string
                        image_data = base64.b64decode(image_data)
                    filename = f"ai_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
                    output_path = os.path.join(OUTPUT_DIR, filename)
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    print(f"[OK] Nano Banana AI image generated (raw): {filename}")
                    return _upload_or_fallback(output_path, style_key)
        
        print("No image data in Nano Banana response")
        return None
        
    except Exception as e:
        print(f"Nano Banana image generation error: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_branded_image(text: str, author_name: str, subtitle: str = "SAP Program Leader | Founder at GNX") -> str:
    """Create a branded LinkedIn image with CENTER-ALIGNED text and professional design"""
    try:
        W, H = 1200, 675
        bg_color = (18, 29, 43)  # Dark navy
        accent_color = (0, 188, 212)  # Cyan accent
        img = Image.new('RGB', (W, H), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Get assets directory
        ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "assets")
        OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "outputs")
        
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Try to load fonts
        try:
            font_bold_path = os.path.join(ASSETS_DIR, "Poppins-Bold.ttf")
            font_regular_path = os.path.join(ASSETS_DIR, "Poppins-Regular.ttf")
            
            # Font sizes
            font = ImageFont.truetype(font_bold_path, 48)  # Main text - BOLD for impact
            font_author = ImageFont.truetype(font_bold_path, 26)  # Author name
            font_subtitle = ImageFont.truetype(font_regular_path, 18)  # Subtitle
        except:
            font = ImageFont.load_default()
            font_author = ImageFont.load_default()
            font_subtitle = ImageFont.load_default()

        # Extract and clean hook text
        hook_text = text.split('\n')[0].replace('**', '')
        # Remove emojis completely (not demojize which leaves text like 'fire')
        hook_text = emoji.replace_emoji(hook_text, replace='')
        hook_text = hook_text.strip()
        
        # Ensure first letter is capitalized
        if hook_text:
            hook_text = hook_text[0].upper() + hook_text[1:] if len(hook_text) > 1 else hook_text.upper()
        
        # Smart truncation at sentence/clause boundaries
        if len(hook_text) > IMAGE_HOOK_LIMIT:
            truncated = hook_text[:IMAGE_HOOK_LIMIT]
            found_boundary = False
            
            # Try to find sentence-ending punctuation
            for punct in ['. ', '! ', '? ', ': ', '; ', '— ', '– ']:
                last_punct = truncated.rfind(punct)
                if last_punct > IMAGE_HOOK_LIMIT // 3:  # Allow finding earlier boundaries
                    hook_text = truncated[:last_punct + 1].strip()
                    found_boundary = True
                    break
            
            # If no sentence boundary, try finding comma for clause boundary
            if not found_boundary:
                last_comma = truncated.rfind(', ')
                if last_comma > IMAGE_HOOK_LIMIT // 2:
                    hook_text = truncated[:last_comma].strip() + "..."
                    found_boundary = True
            
            # Last resort: truncate at last word and add ellipsis
            if not found_boundary:
                last_space = truncated.rfind(' ')
                if last_space > 0:
                    hook_text = truncated[:last_space].strip() + "..."
                else:
                    hook_text = truncated.strip() + "..."
        
        # Layout constants
        BOTTOM_SECTION_HEIGHT = 120
        CONTENT_AREA_TOP = 60
        CONTENT_AREA_BOTTOM = H - BOTTOM_SECTION_HEIGHT - 40
        CONTENT_AREA_HEIGHT = CONTENT_AREA_BOTTOM - CONTENT_AREA_TOP
        
        # === DRAW ACCENT LINE (top decorative element) ===
        accent_y = 40
        accent_width = 80
        draw.rectangle([(W//2 - accent_width//2, accent_y), (W//2 + accent_width//2, accent_y + 4)], fill=accent_color)
        
        # Wrap text into lines
        lines = textwrap.wrap(hook_text, width=32)[:4]  # Fewer chars per line for centered look
        num_lines = len(lines)
        LINE_SPACING = 65
        total_text_height = num_lines * LINE_SPACING
        
        # Center text vertically in content area
        start_y = CONTENT_AREA_TOP + (CONTENT_AREA_HEIGHT - total_text_height) // 2
        
        # === DRAW CENTERED TEXT ===
        current_h = start_y
        for line in lines:
            # Calculate center position for each line
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_centered = (W - text_width) // 2
            
            draw.text((x_centered, current_h), line, font=font, fill='white')
            current_h += LINE_SPACING
        
        # === DRAW BOTTOM ACCENT LINE ===
        bottom_accent_y = CONTENT_AREA_BOTTOM + 10
        draw.rectangle([(W//2 - accent_width//2, bottom_accent_y), (W//2 + accent_width//2, bottom_accent_y + 4)], fill=accent_color)
        
        # === BOTTOM SECTION (Author + Logo) ===
        bottom_section_y = H - 110
        
        # Profile picture
        profile_x = 60
        profile_y = bottom_section_y
        profile_added = False
        
        try:
            profile_pic_path = os.path.join(ASSETS_DIR, "headshot_Kunal.JPG")
            if os.path.exists(profile_pic_path):
                profile_size = 75
                profile_img = Image.open(profile_pic_path).resize((profile_size, profile_size))
                
                # Circular mask
                mask = Image.new('L', (profile_size, profile_size), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, profile_size, profile_size), fill=255)
                
                img.paste(profile_img, (profile_x, profile_y), mask)
                profile_added = True
        except:
            pass

        # Author info
        author_x = profile_x + 95 if profile_added else profile_x
        author_y_name = profile_y + 12
        author_y_subtitle = profile_y + 42
        
        draw.text((author_x, author_y_name), author_name, font=font_author, fill='white')
        draw.text((author_x, author_y_subtitle), subtitle, font=font_subtitle, fill=(150, 150, 150))

        # GNX Logo (BOTTOM-RIGHT)
        try:
            logo_path = os.path.join(ASSETS_DIR, "GNX_Automation_Logo-removebg-preview.png")
            if os.path.exists(logo_path):
                logo_size = 95
                logo_img = Image.open(logo_path).resize((logo_size, logo_size))
                logo_x = W - logo_size - 60
                logo_y = bottom_section_y - 10
                img.paste(logo_img, (logo_x, logo_y), logo_img)
        except:
            pass

        # Save
        filename = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(OUTPUT_DIR, filename)
        img.save(output_path, format='PNG')
        
        return _upload_or_fallback(output_path, "branded")

    except Exception as e:
        print(f"Image generation error: {e}")
        import traceback
        traceback.print_exc()
        return None