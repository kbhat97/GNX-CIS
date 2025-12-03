#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module handles the configuration of the application.

It uses Google Secret Manager for production environments and a .env file for development.
"""

import os
import logging
from typing import Optional, List
from dotenv import load_dotenv

try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

logger = logging.getLogger(__name__)


class Config:
    """
    Application configuration class.

    Loads configuration from environment variables and Google Secret Manager.
    """

    def __init__(self):
        """Initialize the configuration."""
        load_dotenv()
        self.project_id: Optional[str] = os.getenv("GCP_PROJECT_ID", "gnx-cis")
        self.environment: str = os.getenv("ENVIRONMENT", "production")
        self.secret_client = None

        if self.environment == "production" and secretmanager:
            try:
                self.secret_client = secretmanager.SecretManagerServiceClient()
            except Exception as e:
                logger.error(f"Failed to initialize Secret Manager client: {e}")

        self._load_config()
        self.validate_config()

    def _get_secret(self, secret_name: str) -> Optional[str]:
        """
        Get a secret from GCP Secret Manager or environment variables.

        Args:
            secret_name: The name of the secret to retrieve.

        Returns:
            The secret value, or None if not found.
        """
        if self.environment != "production" or not self.secret_client:
            return os.getenv(secret_name)

        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8").strip()
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            return os.getenv(secret_name) # Fallback to env var

    def _load_config(self):
        """Load all configuration variables."""
        # Clerk Configuration
        self.CLERK_SECRET_KEY: Optional[str] = self._get_secret("CLERK_SECRET_KEY")
        self.CLERK_PUBLISHABLE_KEY: Optional[str] = self._get_secret("CLERK_PUBLISHABLE_KEY")
        self.CLERK_JWT_KEY: Optional[str] = self._get_secret("CLERK_JWT_KEY")

        # Supabase Configuration
        self.SUPABASE_URL: Optional[str] = self._get_secret("SUPABASE_URL")
        self.SUPABASE_KEY: Optional[str] = self._get_secret("SUPABASE_KEY")
        self.SUPABASE_SERVICE_KEY: Optional[str] = self._get_secret("SUPABASE_SERVICE_KEY")

        # LinkedIn Configuration
        self.LINKEDIN_CLIENT_ID: Optional[str] = self._get_secret("LINKEDIN_CLIENT_ID")
        self.LINKEDIN_CLIENT_SECRET: Optional[str] = self._get_secret("LINKEDIN_CLIENT_SECRET")
        self.LINKEDIN_REDIRECT_URI: str = os.getenv(
            "LINKEDIN_REDIRECT_URI",
            "https://cis-api-msb3mkgy2q-uc.a.run.app/auth/linkedin/callback",
        )

        # Google Gemini Configuration
        self.GOOGLE_API_KEY: Optional[str] = self._get_secret("GOOGLE_API_KEY")

        # API and Frontend Configuration
        self.API_BASE_URL: str = os.getenv("API_BASE_URL", "https://cis-api-msb3mkgy2q-uc.a.run.app")
        self.FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://cis-frontend-666167524553.us-central1.run.app")
        self.PORT: int = int(os.getenv("PORT", "8080"))

        # CORS Origins
        self.ALLOWED_ORIGINS: List[str] = [
            self.FRONTEND_URL,
            "http://localhost:8501",
            "http://localhost:3000",
        ]

        # JWT Settings
        self.JWT_ALGORITHM: str = "RS256"
        self.JWT_AUDIENCE: str = "authenticated"

        # Google Cloud Platform Configuration
        self.GCP_REGION: str = os.getenv("GCP_REGION", "us-central1")
        self.GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "cis-linkedin-images")
        
        # Development Settings
        self.TEST_MODE: bool = os.getenv("TEST_MODE", "0") == "1"
        self.DEBUG: bool = os.getenv("DEBUG", "0") == "1"

    def validate_config(self) -> bool:
        """
        Validate that all required configuration variables are present.

        Returns:
            True if the configuration is valid, False otherwise.
        """
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

        logger.info("All required configuration loaded successfully")
        return True


# Global config instance
config = Config()
