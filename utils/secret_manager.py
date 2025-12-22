"""
Utility for loading secrets from GCP Secret Manager.
Falls back to environment variables if Secret Manager is not available.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Google Cloud Secret Manager
try:
    from google.cloud import secretmanager
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False
    logger.warning("[WARN] google-cloud-secret-manager not installed - using environment variables only")


def get_secret(secret_name: str, project_id: Optional[str] = None, default: str = "") -> str:
    """
    Retrieve a secret from GCP Secret Manager or fall back to environment variable.
    
    Args:
        secret_name: Name of the secret (e.g., "STRIPE_SECRET_KEY")
        project_id: GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var)
        default: Default value if secret not found
        
    Returns:
        Secret value as string
    """
    # First, try environment variable (for local development)
    env_value = os.getenv(secret_name)
    if env_value:
        logger.debug(f"[SECRET] Using environment variable for {secret_name}")
        return env_value
    
    # If Secret Manager not available, return default
    if not SECRET_MANAGER_AVAILABLE:
        logger.warning(f"[SECRET] Secret Manager not available, using default for {secret_name}")
        return default
    
    # Try to load from Secret Manager
    try:
        # Get project ID
        project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        if not project:
            logger.warning(f"[SECRET] No project ID configured, using env/default for {secret_name}")
            return default
        
        # Create the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()
        
        # Build the resource name
        name = f"projects/{project}/secrets/{secret_name}/versions/latest"
        
        # Access the secret version
        response = client.access_secret_version(request={"name": name})
        
        # Decode the secret payload
        secret_value = response.payload.data.decode("UTF-8").strip()
        logger.info(f"[SECRET] ✓ Loaded {secret_name} from Secret Manager")
        return secret_value
        
    except Exception as e:
        logger.warning(f"[SECRET] Failed to load {secret_name} from Secret Manager: {e}")
        logger.warning(f"[SECRET] Using default value for {secret_name}")
        return default


def load_stripe_secrets(project_id: Optional[str] = None) -> dict:
    """
    Load all Stripe secrets from Secret Manager or environment.
    
    Args:
        project_id: GCP project ID (optional)
        
    Returns:
        Dictionary with Stripe configuration
    """
    return {
        "STRIPE_SECRET_KEY": get_secret("STRIPE_SECRET_KEY", project_id),
        "STRIPE_PUBLISHABLE_KEY": get_secret("STRIPE_PUBLISHABLE_KEY", project_id),
        "STRIPE_PRICE_PRO": get_secret("STRIPE_PRICE_PRO", project_id),
        "STRIPE_PRICE_BUSINESS": get_secret("STRIPE_PRICE_BUSINESS", project_id),
        "STRIPE_WEBHOOK_SECRET_CIS_PRODUCTION": get_secret("STRIPE_WEBHOOK_SECRET_CIS_PRODUCTION", project_id),
        "STRIPE_WEBHOOK_SECRET_ENGAGING_VICTORY": get_secret("STRIPE_WEBHOOK_SECRET_ENGAGING_VICTORY", project_id),
        "STRIPE_COUPON_ID": get_secret("STRIPE_COUPON_ID", project_id, ""),
    }
