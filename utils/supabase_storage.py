"""Supabase Storage Utility for GNX CIS
Uploads generated images to Supabase Storage for persistent URLs.

SECURITY NOTE:
- This module creates a PUBLIC bucket by default for image storage.
- All uploaded images will be publicly accessible via URL.
- Do not upload sensitive or personally identifiable images.
- For private storage, manually create a private bucket in Supabase console.

KEY REQUIREMENTS:
- SUPABASE_SERVICE_KEY is recommended for bucket creation privileges.
- SUPABASE_ANON_KEY may fail on bucket creation operations.
"""
import os
import threading
from supabase import create_client, Client
from datetime import datetime
import uuid

# Initialize Supabase client with thread-safe singleton
_supabase_client: Client | None = None
_client_lock = threading.Lock()

# Bucket existence cache to avoid repeated API calls
_bucket_checked = False
_bucket_check_lock = threading.Lock()


def get_content_type(ext: str) -> str:
    """Get content-type from file extension."""
    ext_lower = ext.lower()
    content_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.bmp': 'image/bmp',
        '.ico': 'image/x-icon',
    }
    return content_types.get(ext_lower, 'image/png')


def get_supabase_client() -> Client | None:
    """Get or create Supabase client singleton (thread-safe)."""
    global _supabase_client
    
    with _client_lock:
        if _supabase_client is None:
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
            
            if not url or not key:
                print("[STORAGE] Supabase credentials not found - using local storage fallback")
                return None
                
            _supabase_client = create_client(url, key)
    
    return _supabase_client


def upload_image_to_supabase(local_path: str, style: str = "general", cleanup_local: bool = True) -> str | None:
    """
    Upload an image to Supabase Storage and return the public URL.
    
    Args:
        local_path: Path to the local image file
        style: The style of the image (for folder organization)
        cleanup_local: If True, delete the local file after successful upload (default: True)
        
    Returns:
        Public URL of the uploaded image, or None if upload fails
    """
    try:
        # Sanitize style to prevent path traversal
        safe_style = style.replace('/', '_').replace('\\', '_').replace('..', '_')
        if not safe_style or safe_style.startswith('.'):
            safe_style = "general"
        
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
        filename = f"{safe_style}/{timestamp}_{unique_id}{ext}"
        
        # Get proper content-type based on file extension
        content_type = get_content_type(ext)
        
        # Upload to Supabase Storage bucket 'images'
        bucket_name = "images"
        
        # Check if bucket exists (cached to avoid repeated API calls)
        global _bucket_checked
        with _bucket_check_lock:
            if not _bucket_checked:
                try:
                    buckets = client.storage.list_buckets()
                    bucket_exists = any(b.name == bucket_name for b in buckets)
                    if not bucket_exists:
                        # Create public bucket for images
                        # SECURITY: This creates a PUBLIC bucket - all images are publicly accessible
                        client.storage.create_bucket(bucket_name, options={"public": True})
                        print(f"[STORAGE] Created PUBLIC bucket: {bucket_name}")
                    _bucket_checked = True
                except Exception as e:
                    print(f"[STORAGE] Bucket check/create warning: {e}")
                    # Mark as checked even on error to avoid repeated failures
                    _bucket_checked = True
        
        # Upload the file with correct content-type
        result = client.storage.from_(bucket_name).upload(
            path=filename,
            file=file_data,
            file_options={"content-type": content_type, "upsert": True}
        )
        
        # Verify upload was successful
        if hasattr(result, 'error') and result.error:
            print(f"[STORAGE] Upload error: {result.error}")
            return None
        
        # Get public URL
        public_url = client.storage.from_(bucket_name).get_public_url(filename)
        
        print(f"[STORAGE] Uploaded to Supabase: {public_url}")
        
        # Delete local file only if cleanup_local is True
        if cleanup_local:
            try:
                os.remove(local_path)
                print(f"[STORAGE] Cleaned up local file: {local_path}")
            except OSError as e:
                print(f"[STORAGE] Could not remove local file {local_path}: {e}")
            
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
            # Remove query parameters if present (e.g., ?v=123 cache-busting)
            if "?" in path:
                path = path.split("?")[0]
            result = client.storage.from_("images").remove([path])
            
            # Verify the deletion succeeded
            if hasattr(result, 'error') and result.error:
                print(f"[STORAGE] Delete failed: {result.error}")
                return False
            
            print(f"[STORAGE] Deleted: {path}")
            return True
            
        return False
        
    except Exception as e:
        print(f"[STORAGE] Delete failed: {e}")
        return False
