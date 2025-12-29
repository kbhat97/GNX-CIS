"""
Supabase Storage Utility for GNX CIS
Uploads generated images to Supabase Storage for persistent URLs
"""
import os
from supabase import create_client, Client
from datetime import datetime
import uuid

# Initialize Supabase client
_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get or create Supabase client singleton."""
    global _supabase_client
    
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
        
        if not url or not key:
            print("[STORAGE] Supabase credentials not found - using local storage fallback")
            return None
            
        _supabase_client = create_client(url, key)
    
    return _supabase_client


def upload_image_to_supabase(local_path: str, style: str = "general") -> str:
    """
    Upload an image to Supabase Storage and return the public URL.
    
    Args:
        local_path: Path to the local image file
        style: The style of the image (for folder organization)
        
    Returns:
        Public URL of the uploaded image, or None if upload fails
    """
    try:
        client = get_supabase_client()
        if not client:
            print("[STORAGE] No Supabase client - returning local path")
            return None
            
        # Read the image file
        with open(local_path, 'rb') as f:
            file_data = f.read()
        
        # Generate unique filename with timestamp and UUID
        original_filename = os.path.basename(local_path)
        ext = os.path.splitext(original_filename)[1] or '.png'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{style}/{timestamp}_{unique_id}{ext}"
        
        # Upload to Supabase Storage bucket 'images'
        bucket_name = "images"
        
        # Check if bucket exists, create if not
        try:
            buckets = client.storage.list_buckets()
            bucket_exists = any(b.name == bucket_name for b in buckets)
            if not bucket_exists:
                # Create public bucket for images
                client.storage.create_bucket(bucket_name, options={"public": True})
                print(f"[STORAGE] Created bucket: {bucket_name}")
        except Exception as e:
            print(f"[STORAGE] Bucket check/create warning: {e}")
        
        # Upload the file
        result = client.storage.from_(bucket_name).upload(
            path=filename,
            file=file_data,
            file_options={"content-type": "image/png", "upsert": True}
        )
        
        # Get public URL
        public_url = client.storage.from_(bucket_name).get_public_url(filename)
        
        print(f"[STORAGE] Uploaded to Supabase: {public_url}")
        
        # Optionally delete local file to save container space
        try:
            os.remove(local_path)
            print(f"[STORAGE] Cleaned up local file: {local_path}")
        except:
            pass
            
        return public_url
        
    except Exception as e:
        print(f"[STORAGE] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def delete_image_from_supabase(public_url: str) -> bool:
    """
    Delete an image from Supabase Storage.
    
    Args:
        public_url: The public URL of the image to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
            
        # Extract path from URL
        # URL format: https://xxx.supabase.co/storage/v1/object/public/images/style/filename.png
        if "/storage/v1/object/public/images/" in public_url:
            path = public_url.split("/storage/v1/object/public/images/")[1]
            client.storage.from_("images").remove([path])
            print(f"[STORAGE] Deleted: {path}")
            return True
            
        return False
        
    except Exception as e:
        print(f"[STORAGE] Delete failed: {e}")
        return False
