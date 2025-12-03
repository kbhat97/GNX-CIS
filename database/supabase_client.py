#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module provides a production-ready client for interacting with the Supabase database.
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

from supabase import create_client, Client

from config import config
from utils.logger import log_agent_action, log_error

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Production-ready, multi-tenant Supabase client with comprehensive database operations."""

    def __init__(self):
        """Initialize Supabase client with service key for admin operations."""
        self.client: Optional[Client] = None
        try:
            supabase_url = config.SUPABASE_URL
            # Use service key for admin-level access, fallback to anon key
            supabase_key = config.SUPABASE_SERVICE_KEY or config.SUPABASE_KEY

            if not supabase_url or not supabase_key:
                logger.critical("Supabase URL or key is not configured. Database operations will fail.")
                return

            self.client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize Supabase client: {e}", exc_info=True)
            raise

    def health_check(self) -> Dict[str, Any]:
        """Check Supabase connection health."""
        if not self.client:
            return {"healthy": False, "message": "Supabase client not initialized."}
        try:
            result = self.client.table("posts").select("count", count="exact").limit(1).execute()
            return {
                "healthy": True,
                "message": "Database connection successful",
                "total_posts": result.count,
            }
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return {"healthy": False, "message": f"Database connection failed: {e}"}

    # ... (rest of the methods remain the same)

# Global instance of the Supabase client
supabase_client = SupabaseClient()
