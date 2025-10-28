import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
import uuid
from .logger import log_error
import io
from google.cloud import storage
from config import config

IMAGE_HOOK_LIMIT = 120

def create_branded_image(text: str, author_name: str, subtitle: str = "SAP Program Leader | AI Founder") -> str:
    try:
        W, H = 1200, 675
        bg_color = (18, 29, 43)
        img = Image.new('RGB', (W, H), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "assets")
        font_bold_path = os.path.join(ASSETS_DIR, "Poppins-Bold.ttf")
        font_regular_path = os.path.join(ASSETS_DIR, "Poppins-Regular.ttf")
        
        font = ImageFont.truetype(font_regular_path, 64) 
        font_author = ImageFont.truetype(font_bold_path, 36)
        font_subtitle = ImageFont.truetype(font_regular_path, 28)

        hook_text = text.split('\n')[0].replace('**', '')
        if len(hook_text) > IMAGE_HOOK_LIMIT:
            truncated = hook_text[:IMAGE_HOOK_LIMIT]
            last_space = truncated.rfind(' ')
            hook_text = truncated[:last_space] + "..."
        
        current_h = 120
        lines = textwrap.wrap(hook_text, width=32)
        for line in lines:
            draw.text((70, current_h), line, font=font, fill='white')
            current_h += 90

        profile_pic_path = os.path.join(ASSETS_DIR, "headshot_Kunal.JPG")
        profile_img = Image.open(profile_pic_path).resize((100, 100))
        mask = Image.new('L', (100, 100), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 100, 100), fill=255)
        img.paste(profile_img, (70, H - 100 - 70), mask)
        draw.text((190, H - 100 - 55), author_name, font=font_author, fill='white')
        draw.text((190, H - 100 - 10), subtitle, font=font_subtitle, fill=(200, 200, 200))

        logo_path = os.path.join(ASSETS_DIR, "GNX_Automation_Logo-removebg-preview.png")
        logo_img = Image.open(logo_path).resize((120, 120))
        logo_w, logo_h = logo_img.size
        img.paste(logo_img, (W - logo_w - 70, H - logo_h - 70), logo_img)

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        storage_client = storage.Client()
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        blob_name = f"{uuid.uuid4()}.png"
        blob = bucket.blob(blob_name)
        
        blob.upload_from_file(buffer, content_type='image/png')
        return blob.public_url

    except Exception as e:
        log_error(e, "Image generation and upload failed")
        return None