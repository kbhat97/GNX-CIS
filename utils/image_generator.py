import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
import uuid
from datetime import datetime

IMAGE_HOOK_LIMIT = 120

def create_branded_image(text: str, author_name: str, subtitle: str = "SAP Program Leader | AI Founder") -> str:
    """Create a branded LinkedIn image and save locally"""
    try:
        W, H = 1200, 675
        bg_color = (18, 29, 43)
        img = Image.new('RGB', (W, H), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Get assets directory
        ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "assets")
        OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "outputs")
        
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Try to load fonts, fallback to default if not found
        try:
            font_bold_path = os.path.join(ASSETS_DIR, "Poppins-Bold.ttf")
            font_regular_path = os.path.join(ASSETS_DIR, "Poppins-Regular.ttf")
            
            font = ImageFont.truetype(font_regular_path, 64) 
            font_author = ImageFont.truetype(font_bold_path, 36)
            font_subtitle = ImageFont.truetype(font_regular_path, 28)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
            font_author = ImageFont.load_default()
            font_subtitle = ImageFont.load_default()

        # Extract hook text
        hook_text = text.split('\n')[0].replace('**', '')
        if len(hook_text) > IMAGE_HOOK_LIMIT:
            truncated = hook_text[:IMAGE_HOOK_LIMIT]
            last_space = truncated.rfind(' ')
            hook_text = truncated[:last_space] + "..."
        
        # Draw hook text
        current_h = 120
        lines = textwrap.wrap(hook_text, width=32)
        for line in lines:
            draw.text((70, current_h), line, font=font, fill='white')
            current_h += 90

        # Try to add profile picture
        try:
            profile_pic_path = os.path.join(ASSETS_DIR, "headshot_Kunal.JPG")
            if os.path.exists(profile_pic_path):
                profile_img = Image.open(profile_pic_path).resize((100, 100))
                mask = Image.new('L', (100, 100), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, 100, 100), fill=255)
                img.paste(profile_img, (70, H - 100 - 70), mask)
        except:
            pass  # Skip if profile pic not found

        # Draw author info
        draw.text((190, H - 100 - 55), author_name, font=font_author, fill='white')
        draw.text((190, H - 100 - 10), subtitle, font=font_subtitle, fill=(200, 200, 200))

        # Try to add logo
        try:
            logo_path = os.path.join(ASSETS_DIR, "GNX_Automation_Logo-removebg-preview.png")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path).resize((120, 120))
                logo_w, logo_h = logo_img.size
                img.paste(logo_img, (W - logo_w - 70, H - logo_h - 70), logo_img)
        except:
            pass  # Skip if logo not found

        # Save locally
        filename = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(OUTPUT_DIR, filename)
        img.save(output_path, format='PNG')
        
        # Return absolute path for Streamlit
        return os.path.abspath(output_path)

    except Exception as e:
        print(f"Image generation error: {e}")
        import traceback
        traceback.print_exc()
        return None