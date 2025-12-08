import os
import textwrap
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


async def generate_ai_image(hook_text: str, topic: str, style: str = "professional", full_content: str = None) -> str:
    """
    Generate an AI image using Gemini 2.5 Flash Image (Nano Banana).
    Creates dynamic, content-aware prompts for handwritten sketch-style infographics.
    
    Args:
        hook_text: The main hook/headline to feature
        topic: The overall topic for context
        style: The writing style (professional, technical, etc.)
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
        # Find percentages/metrics
        import re
        metrics = re.findall(r'\d+%|\$[\d,]+[KMB]?|\d+x|\d+\+', content_to_analyze)
        metrics_text = ", ".join(metrics[:5]) if metrics else "key insights"
        
        # Find hashtags for topic keywords
        hashtags = re.findall(r'#(\w+)', content_to_analyze)
        keywords = ", ".join(hashtags[:5]) if hashtags else "business, technology, innovation"
        
        # Clean the hook for display
        clean_hook = hook_text.replace('**', '').replace('\n', ' ').strip()
        if len(clean_hook) > 120:
            clean_hook = clean_hook[:120] + "..."
        
        # Extract first sentence as main headline
        first_sentence = content_to_analyze.split('.')[0].replace('**', '').strip()
        if len(first_sentence) > 100:
            first_sentence = first_sentence[:100] + "..."
        
        # Build a dynamic, content-aware prompt for handwritten sketch infographic
        prompt = f"""Create a HANDWRITTEN SKETCH STYLE INFOGRAPHIC that visually explains this topic:

=== CONTENT TO VISUALIZE ===
{content_to_analyze[:1500]}

=== DESIGN SPECIFICATIONS ===
STYLE: Handwritten sketch on whiteboard/paper, like a consultant's explanation drawing
FORMAT: Landscape 1200x675 (LinkedIn optimal)
BACKGROUND: Clean white or light cream paper texture

=== REQUIRED VISUAL ELEMENTS ===
1. HEADLINE at top: "{first_sentence}"
2. FLOW DIAGRAM showing the main concept progression:
   - Use arrows (→) to connect ideas
   - Use boxes, clouds, or circles to group concepts
   - Show cause-and-effect relationships
3. KEY METRICS to highlight: {metrics_text}
   - Put percentages in circles or callout boxes
   - Make numbers stand out with underlines or bold
4. ICONS/SKETCHES for key concepts:
   - Draw simple icons related to: {keywords}
   - Use handwritten labels
5. CALL TO ACTION at bottom with the main question/engagement prompt

=== HANDWRITTEN STYLE GUIDELINES ===
- Use black/dark ink with occasional accent colors (blue, red for emphasis)
- Vary line thickness like real hand drawing
- Include annotations and handwritten labels
- Add arrows, brackets, underlines for emphasis
- Make it look like an expert explaining on a whiteboard
- Include small doodles/icons relevant to the topic

=== DO NOT ===
- Do NOT use stock photos or photorealistic images
- Do NOT use generic corporate graphics
- Do NOT make it look computer-generated
- MUST look hand-drawn and authentic

Create a visually engaging handwritten infographic that someone would want to save and share."""

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
                    filename = f"ai_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
                    output_path = os.path.join(OUTPUT_DIR, filename)
                    image.save(output_path)
                    print(f"✅ Nano Banana AI image generated: {filename}")
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
                    print(f"✅ Nano Banana AI image generated (raw): {filename}")
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