import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
import uuid
from datetime import datetime
import emoji

IMAGE_HOOK_LIMIT = 180  # Increased for fuller sentences

def create_branded_image(text: str, author_name: str, subtitle: str = "SAP Program Leader | AI Founder") -> str:
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
        hook_text = emoji.demojize(hook_text, delimiters=("", ""))
        
        # Smart truncation at sentence boundaries
        if len(hook_text) > IMAGE_HOOK_LIMIT:
            truncated = hook_text[:IMAGE_HOOK_LIMIT]
            found_sentence = False
            for punct in ['. ', '! ', '? ']:
                last_punct = truncated.rfind(punct)
                if last_punct > IMAGE_HOOK_LIMIT // 2:
                    hook_text = truncated[:last_punct + 1].strip()
                    found_sentence = True
                    break
            if not found_sentence:
                last_space = truncated.rfind(' ')
                if last_space > 0:
                    hook_text = truncated[:last_space].strip() + "..."
        
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