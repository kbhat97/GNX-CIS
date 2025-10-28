import os
from typing import Optional
from google.cloud import secretmanager
import logging

logger = logging.getLogger(__name__)


class Config:
    """Production configuration management"""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "gnx-cis")
        self.environment = os.getenv("ENVIRONMENT", "production")
        
        # Initialize Secret Manager client
        if self.environment == "production":
            self.secret_client = secretmanager.SecretManagerServiceClient()
        
        # Load all secrets
        self._load_config()
    
    def _get_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from GCP Secret Manager"""
        if self.environment != "production":
            # Development: use .env
            return os.getenv(secret_name)
        
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8").strip()
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            return None
    
    def _load_config(self):
        """Load all configuration"""
        # Clerk Configuration
        self.CLERK_SECRET_KEY = self._get_secret("CLERK_SECRET_KEY")
        self.CLERK_PUBLISHABLE_KEY = self._get_secret("CLERK_PUBLISHABLE_KEY")
        self.CLERK_JWT_KEY = self._get_secret("CLERK_JWT_KEY")  # For JWT verification
        
        # Supabase Configuration (Database only, no auth)
        self.SUPABASE_URL = self._get_secret("SUPABASE_URL")
        self.SUPABASE_KEY = self._get_secret("SUPABASE_KEY")  # Service role key
        
        # LinkedIn Configuration
        self.LINKEDIN_CLIENT_ID = self._get_secret("LINKEDIN_CLIENT_ID")
        self.LINKEDIN_CLIENT_SECRET = self._get_secret("LINKEDIN_CLIENT_SECRET")
        self.LINKEDIN_REDIRECT_URI = os.getenv(
            "LINKEDIN_REDIRECT_URI",
            "https://cis-api-msb3mkgy2q-uc.a.run.app/auth/linkedin/callback"
        )
        
        # Google Gemini Configuration
        self.GOOGLE_API_KEY = self._get_secret("GOOGLE_API_KEY")
        
        # API Configuration
        self.API_BASE_URL = os.getenv(
            "API_BASE_URL",
            "https://cis-api-msb3mkgy2q-uc.a.run.app"
        )
        self.FRONTEND_URL = os.getenv(
            "FRONTEND_URL",
            "https://cis-frontend-666167524553.us-central1.run.app"
        )
        
        # CORS Origins
        self.ALLOWED_ORIGINS = [
            self.FRONTEND_URL,
            "http://localhost:8501",  # Local development
            "http://localhost:3000"
        ]
        
        # JWT Settings (for Clerk)
        self.JWT_ALGORITHM = "RS256"  # Clerk uses RS256
        self.JWT_AUDIENCE = "authenticated"
    
    def validate_config(self) -> bool:
        """Validate all required configuration is present"""
        required_configs = [
            ("CLERK_SECRET_KEY", self.CLERK_SECRET_KEY),
            ("SUPABASE_URL", self.SUPABASE_URL),
            ("SUPABASE_KEY", self.SUPABASE_KEY),
            ("LINKEDIN_CLIENT_ID", self.LINKEDIN_CLIENT_ID),
            ("LINKEDIN_CLIENT_SECRET", self.LINKEDIN_CLIENT_SECRET),
            ("GOOGLE_API_KEY", self.GOOGLE_API_KEY),
        ]
        
        missing = [name for name, value in required_configs if not value]
        
        if missing:
            logger.error(f"Missing required configuration: {', '.join(missing)}")
            return False
        
        logger.info("✅ All required configuration loaded successfully")
        return True
    
    def print_config_summary(self):
        """Print configuration summary (without secrets)"""
        print("\n" + "="*50)
        print("🔧 CONFIGURATION SUMMARY")
        print("="*50)
        print(f"Environment: {self.environment}")
        print(f"Project ID: {self.project_id}")
        print(f"\n🔐 Clerk:")
        print(f"  Secret Key: {'✅ Set' if self.CLERK_SECRET_KEY else '❌ Missing'}")
        print(f"  Publishable Key: {'✅ Set' if self.CLERK_PUBLISHABLE_KEY else '❌ Missing'}")
        print(f"\n💾 Supabase:")
        print(f"  URL: {self.SUPABASE_URL if self.SUPABASE_URL else '❌ Missing'}")
        print(f"  Key: {'✅ Set' if self.SUPABASE_KEY else '❌ Missing'}")
        print(f"\n🔗 LinkedIn:")
        print(f"  Client ID: {'✅ Set' if self.LINKEDIN_CLIENT_ID else '❌ Missing'}")
        print(f"  Client Secret: {'✅ Set' if self.LINKEDIN_CLIENT_SECRET else '❌ Missing'}")
        print(f"  Redirect URI: {self.LINKEDIN_REDIRECT_URI}")
        print(f"\n🤖 Gemini:")
        print(f"  API Key: {'✅ Set' if self.GOOGLE_API_KEY else '❌ Missing'}")
        print(f"\n🌐 URLs:")
        print(f"  API: {self.API_BASE_URL}")
        print(f"  Frontend: {self.FRONTEND_URL}")
        print("="*50 + "\n")


# Global config instance
config = Config()


if __name__ == "__main__":
    # Test configuration
    config.print_config_summary()
    if config.validate_config():
        print("✅ Configuration is valid and ready!")
    else:
        print("❌ Configuration is incomplete. Check missing values above.")
