import os
import textwrap
import re
from PIL import Image, ImageDraw, ImageFont
import uuid
from datetime import datetime
import emoji
import base64
import io

# Try to import google genai for Nano Banana support
try:
    from google import genai
    from google.genai import types
    NANO_BANANA_AVAILABLE = True
except ImportError:
    NANO_BANANA_AVAILABLE = False

IMAGE_HOOK_LIMIT = 250  # Increased for complete sentences

# ═══════════════════════════════════════════════════════════════════
# STYLE-BASED IMAGE PROMPT LIBRARY
# Each style maps to a specialized visual template
# ═══════════════════════════════════════════════════════════════════

# Quality rules appended to ALL image prompts
IMAGE_QUALITY_RULES = """

=== CRITICAL QUALITY RULES (MUST FOLLOW) ===
1. SPELLING CHECK: VERIFY EVERY WORD IS SPELLED CORRECTLY before rendering.
   - "tension" NOT "tention"
   - "palpable" NOT "paldable"  
   - "improvement" NOT "imprevvement"
   - Double-check ALL text character by character.
2. NO TRUNCATED TEXT: All text must be fully visible - no text cut off at edges or running outside the image.
3. MARGINS: Keep at least 60px padding from all edges. No text or elements should touch the border.
4. COMPLETE SENTENCES: Every text element must be a complete word or phrase - no half-words.
5. READABLE: All text must be large enough to read clearly (minimum 16pt equivalent).
6. NO DUPLICATES: Each text element should appear ONLY ONCE in the image.
7. ASPECT RATIO: Image must be exactly 16:9 (1200x675 pixels) - landscape orientation.
8. LINE LENGTH: Maximum 50 characters per line of text. Break long text into multiple shorter lines.
9. TEXT FITTING: Ensure ALL text fits within the visible area. If text is too long, wrap to next line or reduce font size.
"""

IMAGE_PROMPT_LIBRARY = {
    "storytelling": """Create a HANDWRITTEN SKETCH STYLE INFOGRAPHIC that tells a visual story:

=== CONTENT TO VISUALIZE ===
{content}

=== DESIGN SPECIFICATIONS ===
STYLE: Handwritten sketch on cream/white paper, like a consultant explaining on a whiteboard
FORMAT: 16:9 aspect ratio (1200x675 pixels) for LinkedIn
ASPECT RATIO: Must be exactly 16:9 horizontal/landscape
BACKGROUND: Clean white or light cream paper texture with subtle texture

=== REQUIRED VISUAL ELEMENTS ===
1. HEADLINE at top: "{headline}" (handwritten style, bold)
   - CRITICAL: If headline is longer than 50 characters, MUST wrap into 2-3 SHORT lines
   - Each line MAXIMUM 50 characters
   - Center-align the wrapped headline
   - Ensure ALL text is visible with 60px margins from edges
2. NARRATIVE FLOW showing the story progression:
   - Use curved arrows (→) connecting story beats
   - Show "before" → "transformation" → "after" journey
   - Include small character sketches (stick figures with expressions)
3. KEY MOMENTS highlighted in speech bubbles or callout boxes
4. EMOTIONAL MARKERS: Use faces/emojis to show feelings at each stage
5. METRICS in circles: {metrics}
6. CALL TO ACTION at bottom with engagement question

=== HANDWRITTEN STYLE ===
- Black ink with blue/red accents for emphasis
- Varying line thickness like real hand drawing
- Annotations with arrows pointing to key insights
- Small doodles and icons related to the story
- Make it feel personal and authentic

DO NOT use stock photos or photorealistic images. MUST look hand-drawn.""",

    "technical": """Create a HANDWRITTEN TECHNICAL SKETCH that explains this concept:

=== CONTENT TO VISUALIZE ===
{content}

=== DESIGN SPECIFICATIONS ===
STYLE: Hand-drawn technical diagram on whiteboard/paper, like an engineer sketching on a whiteboard
FORMAT: 16:9 aspect ratio (1200x675 pixels) for LinkedIn
ASPECT RATIO: Must be exactly 16:9 horizontal/landscape
BACKGROUND: White or cream paper with subtle texture

=== REQUIRED VISUAL ELEMENTS ===
1. TITLE at top: "{headline}" (handwritten but legible)
   - CRITICAL: If headline is longer than 50 characters, MUST wrap into 2-3 SHORT lines
   - Each line MAXIMUM 50 characters
   - Ensure ALL text is visible with 60px margins from edges
2. HAND-DRAWN FLOWCHART showing the process:
   - Sketched rectangles for processes
   - Hand-drawn diamonds for decision points
   - Sketched cylinders for databases
   - Arrows with handwritten labels
3. NUMBERED STEPS in circles
4. SKETCHED ICONS for tools/technologies
5. METRICS in hand-circled callouts: {metrics}
6. Simple legend with hand-drawn symbols

=== SKETCH STYLE ===
- Black ink with blue/green accents
- Slightly imperfect lines (hand-drawn look)
- Handwritten labels and annotations
- Grid paper or whiteboard texture
- Feels like an expert explaining at a whiteboard

DO NOT use stock photos. MUST look hand-sketched and authentic.""",

    "thought_leadership": """Create a HANDWRITTEN THOUGHT LEADERSHIP SKETCH with bold insights:

=== CONTENT TO VISUALIZE ===
{content}

=== DESIGN SPECIFICATIONS ===
STYLE: Hand-sketched bold statement graphic, like a CEO presenting on whiteboard
FORMAT: 16:9 aspect ratio (1200x675 pixels) for LinkedIn
ASPECT RATIO: Must be exactly 16:9 horizontal/landscape
BACKGROUND: White or cream paper with bold hand-drawn elements

=== REQUIRED VISUAL ELEMENTS ===
1. MAIN STATEMENT at center: "{headline}" (large, bold, handwritten)
   - CRITICAL: If headline is longer than 50 characters, MUST wrap into 2-3 SHORT lines
   - Each line MAXIMUM 50 characters
   - Center-align the wrapped headline
   - Ensure ALL text is visible with 60px margins from edges
2. CONTRARIAN ELEMENT: Hand-drawn "X" over myth, arrow to truth
3. KEY POINTS as 3-4 hand-drawn bullet callouts with sketched icons
4. METRICS in bold hand-drawn circles: {metrics}
5. VISUAL HIERARCHY: Main point biggest, supporting points smaller
6. PROVOCATIVE QUESTION at bottom with hand-drawn underline

=== SKETCH STYLE ===
- Bold black ink with blue/red accents for emphasis
- Large, confident handwritten text
- Hand-drawn boxes, circles, and arrows
- Simple sketched icons for visual impact
- Make it look like an expert's bold presentation

DO NOT use stock photos. MUST look hand-drawn and impactful.""",

    "inspirational": """Create a HANDWRITTEN INSPIRATIONAL JOURNEY sketch:

=== CONTENT TO VISUALIZE ===
{content}

=== DESIGN SPECIFICATIONS ===
STYLE: Hand-drawn motivational journey, like a coach sketching your success path
FORMAT: 16:9 aspect ratio (1200x675 pixels) for LinkedIn
ASPECT RATIO: Must be exactly 16:9 horizontal/landscape
BACKGROUND: White or cream paper with warm hand-drawn elements

=== REQUIRED VISUAL ELEMENTS ===
1. HEADLINE at top: "{headline}" (inspiring, handwritten style)
   - CRITICAL: If headline is longer than 50 characters, MUST wrap into 2-3 SHORT lines
   - Each line MAXIMUM 50 characters
   - Center-align the wrapped headline
   - Ensure ALL text is visible with 60px margins from edges
2. TRANSFORMATION JOURNEY (hand-drawn):
   - Sketched figure on left showing "before" (small, struggling)
   - Hand-drawn winding path/mountain in middle with milestones
   - Triumphant figure on right showing "after" (success!)
3. MILESTONE MARKERS along the path (numbered circles)
4. MOTIVATIONAL PHRASES in hand-drawn speech bubbles
5. METRICS as hand-drawn achievement badges: {metrics}
6. CALL TO ACTION at bottom with hand-drawn arrow

=== SKETCH STYLE ===
- Black ink with warm color accents (orange, gold, red)
- Hand-drawn hearts, stars, and growth symbols
- Upward-pointing arrows and elements
- Stick figures with expressive faces
- Feels warm, personal, and achievable

DO NOT use stock photos. MUST look hand-sketched and motivating.""",

    "professional": """Create a HANDWRITTEN BUSINESS INFOGRAPHIC sketch:

=== CONTENT TO VISUALIZE ===
{content}

=== DESIGN SPECIFICATIONS ===
STYLE: Hand-drawn business infographic, like a consultant's whiteboard explanation
FORMAT: 16:9 aspect ratio (1200x675 pixels) for LinkedIn
ASPECT RATIO: Must be exactly 16:9 horizontal/landscape
BACKGROUND: White or cream paper with grid lines (like graph paper)

=== REQUIRED VISUAL ELEMENTS ===
1. HEADLINE at top: "{headline}" (professional handwritten)
   - CRITICAL: If headline is longer than 50 characters, MUST wrap into 2-3 SHORT lines
   - Each line MAXIMUM 50 characters
   - Center-align the wrapped headline
   - Ensure ALL text is visible with 60px margins from edges
2. DATA VISUALIZATION (hand-sketched):
   - Hand-drawn bar charts or line graphs
   - Before/After comparison with arrows
   - ROI stats in circled callouts
3. KEY INSIGHTS as 3-4 hand-drawn icon+text pairs
4. METRICS prominently in hand-drawn circles: {metrics}
5. Simple icons (lightbulb, chart, checkmark)
6. TAKEAWAY at bottom with hand-drawn box

=== SKETCH STYLE ===
- Black ink with blue accent color
- Clean but hand-drawn lines
- Simple sketched charts and graphs
- Professional handwritten fonts
- Looks like a consultant explaining at whiteboard

DO NOT use stock photos. MUST look hand-sketched and professional."""
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
        if len(first_sentence) > 60:
            first_sentence = first_sentence[:60] + "..."
        
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
                    return os.path.abspath(output_path)
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
                    return os.path.abspath(output_path)
        
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
        
        return os.path.abspath(output_path)

    except Exception as e:
        print(f"Image generation error: {e}")
        import traceback
        traceback.print_exc()
        return None