import asyncio
from typing import Dict, Any
from datetime import datetime
import google.generativeai as genai
from supabase import create_client
from tools.linkedin_tools import LinkedInAPI
from config import config
from utils.logger import log_agent_action, log_error
import logging
import requests
import os

logger = logging.getLogger(__name__)

class HealthCheck:
    """Comprehensive system health check for production readiness"""
    
    def __init__(self):
        self.checks = {}
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        logger.info("🏥 Starting comprehensive health checks...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "HEALTHY",
            "environment": config.ENVIRONMENT,
            "checks": {},
            "warnings": [],
            "errors": []
        }
        
        # Define all health checks
        health_checks = [
            ("Configuration", self.check_configuration),
            ("Supabase Database", self.check_supabase),
            ("Gemini AI API", self.check_gemini),
            ("LinkedIn API", self.check_linkedin),
            ("Google Cloud Storage", self.check_gcs),
            ("Environment Setup", self.check_environment)
        ]
        
        # Run each health check
        for check_name, check_func in health_checks:
            try:
                logger.info(f"Checking {check_name}...")
                check_result = await check_func()
                results["checks"][check_name] = check_result
                
                # Collect warnings and errors
                if not check_result["healthy"]:
                    results["errors"].append(f"{check_name}: {check_result['message']}")
                elif check_result.get("warning"):
                    results["warnings"].append(f"{check_name}: {check_result['warning']}")
                
                # Log result
                status_icon = "✅" if check_result["healthy"] else "❌"
                logger.info(f"{status_icon} {check_name}: {check_result['message']}")
                
            except Exception as e:
                error_msg = f"Health check failed: {str(e)}"
                results["checks"][check_name] = {
                    "healthy": False,
                    "message": error_msg,
                    "error": str(e)
                }
                results["errors"].append(f"{check_name}: {error_msg}")
                logger.error(f"❌ {check_name} health check failed: {e}")
        
        # Determine overall status
        unhealthy_checks = [name for name, check in results["checks"].items() if not check["healthy"]]
        if unhealthy_checks:
            results["overall_status"] = "UNHEALTHY"
            results["failed_checks"] = unhealthy_checks
        elif results["warnings"]:
            results["overall_status"] = "DEGRADED"
        
        logger.info(f"🏥 Health check complete: {results['overall_status']}")
        return results
    
    async def check_configuration(self) -> Dict[str, Any]:
        """Check application configuration"""
        try:
            # Check for missing required configs
            missing_configs = config.get_missing_configs()
            
            if missing_configs:
                return {
                    "healthy": False,
                    "message": f"Missing required configuration: {', '.join(missing_configs)}",
                    "missing_configs": missing_configs
                }
            
            # Check for missing optional configs
            optional_missing = config.get_optional_missing_configs()
            warning = None
            if optional_missing:
                warning = f"Missing optional configs: {', '.join(optional_missing)}"
            
            return {
                "healthy": True,
                "message": "All required configuration present",
                "warning": warning,
                "environment": config.ENVIRONMENT,
                "gcp_project": config.GCP_PROJECT_ID
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Configuration validation failed: {str(e)}",
                "error": str(e)
            }
    
    async def check_supabase(self) -> Dict[str, Any]:
        """Check Supabase database connection and schema"""
        try:
            if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
                return {
                    "healthy": False,
                    "message": "Supabase credentials not configured"
                }
            
            # Test connection
            client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
            
            # Test posts table access
            result = client.table("posts").select("count", count="exact").limit(1).execute()
            post_count = result.count if hasattr(result, 'count') else 0
            
            # Test linkedin_tokens table (it's OK if it doesn't exist yet)
            try:
                token_result = client.table("linkedin_tokens").select("count", count="exact").limit(1).execute()
                token_count = token_result.count if hasattr(token_result, 'count') else 0
            except:
                token_count = 0
            
            return {
                "healthy": True,
                "message": "Database connection successful",
                "url": config.SUPABASE_URL[:30] + "...",
                "post_count": post_count,
                "token_count": token_count
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Database connection failed: {str(e)}",
                "error": str(e)
            }
    
    async def check_gemini(self) -> Dict[str, Any]:
        """Check Google Gemini API connectivity"""
        try:
            if not config.GOOGLE_API_KEY:
                return {
                    "healthy": False,
                    "message": "Google API key not configured"
                }
            
            # Configure and test Gemini
            genai.configure(api_key=config.GOOGLE_API_KEY)
            
            # List available models to test API access
            models = list(genai.list_models())
            available_models = [model.name for model in models if 'gemini' in model.name.lower()]
            
            # Test a simple generation
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Test message for health check")
            
            if response and response.text:
                return {
                    "healthy": True,
                    "message": "Gemini API accessible and responding",
                    "available_models": len(available_models),
                    "test_response_length": len(response.text)
                }
            else:
                return {
                    "healthy": False,
                    "message": "Gemini API not responding properly"
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Gemini API check failed: {str(e)}",
                "error": str(e)
            }
    
    async def check_linkedin(self) -> Dict[str, Any]:
        """Check LinkedIn API configuration"""
        try:
            if not config.LINKEDIN_CLIENT_ID or not config.LINKEDIN_CLIENT_SECRET:
                return {
                    "healthy": False,
                    "message": "LinkedIn API credentials not configured"
                }
            
            # Test basic LinkedIn API setup (without actual token)
            api = LinkedInAPI()
            
            # If we have a system access token, test it
            if config.LINKEDIN_ACCESS_TOKEN:
                try:
                    profile = await api.get_profile()
                    if profile:
                        return {
                            "healthy": True,
                            "message": "LinkedIn API accessible with system token",
                            "has_system_token": True,
                            "profile_id": profile.get("sub", "unknown")
                        }
                except:
                    pass  # Fall through to basic check
            
            # Basic configuration check
            return {
                "healthy": True,
                "message": "LinkedIn API configured (no system token to test)",
                "has_system_token": bool(config.LINKEDIN_ACCESS_TOKEN),
                "client_id": config.LINKEDIN_CLIENT_ID[:10] + "..."
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"LinkedIn API check failed: {str(e)}",
                "error": str(e)
            }
    
    async def check_gcs(self) -> Dict[str, Any]:
        """Check Google Cloud Storage configuration"""
        try:
            if not config.GCS_BUCKET_NAME:
                return {
                    "healthy": False,
                    "message": "GCS bucket not configured"
                }
            
            # Test GCS access (basic check)
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(config.GCS_BUCKET_NAME)
                
                # Test bucket access
                bucket.reload()
                
                return {
                    "healthy": True,
                    "message": "GCS bucket accessible",
                    "bucket_name": config.GCS_BUCKET_NAME,
                    "location": bucket.location if hasattr(bucket, 'location') else "unknown"
                }
                
            except Exception as gcs_error:
                # If GCS library fails, at least check if bucket name is set
                return {
                    "healthy": True,
                    "message": "GCS bucket configured (access not tested)",
                    "warning": f"Could not verify GCS access: {str(gcs_error)}",
                    "bucket_name": config.GCS_BUCKET_NAME
                }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"GCS check failed: {str(e)}",
                "error": str(e)
            }
    
    async def check_environment(self) -> Dict[str, Any]:
        """Check general environment setup"""
        try:
            # Check Python version
            import sys
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            # Check if running in container
            in_container = os.path.exists('/.dockerenv') or os.environ.get('KUBERNETES_SERVICE_HOST')
            
            # Check available memory (if possible)
            try:
                import psutil
                memory_info = psutil.virtual_memory()
                available_memory_gb = round(memory_info.available / (1024**3), 2)
                total_memory_gb = round(memory_info.total / (1024**3), 2)
            except ImportError:
                available_memory_gb = "unknown"
                total_memory_gb = "unknown"
            
            # Check disk space
            import shutil
            try:
                disk_usage = shutil.disk_usage("/")
                free_space_gb = round(disk_usage.free / (1024**3), 2)
                total_space_gb = round(disk_usage.total / (1024**3), 2)
            except:
                free_space_gb = "unknown"
                total_space_gb = "unknown"
            
            return {
                "healthy": True,
                "message": "Environment check passed",
                "python_version": python_version,
                "in_container": in_container,
                "memory": {
                    "available_gb": available_memory_gb,
                    "total_gb": total_memory_gb
                },
                "disk": {
                    "free_gb": free_space_gb,
                    "total_gb": total_space_gb
                },
                "environment": config.ENVIRONMENT
            }
            
        except Exception as e:
            return {
                "healthy": True,  # Non-critical check
                "message": "Environment check completed with warnings",
                "warning": f"Could not gather all environment info: {str(e)}"
            }
    
    async def quick_check(self) -> Dict[str, Any]:
        """Quick health check for frequently called endpoints"""
        try:
            # Just check the most critical components
            checks = {
                "database": await self.check_supabase(),
                "ai_api": await self.check_gemini()
            }
            
            all_healthy = all(check["healthy"] for check in checks.values())
            
            return {
                "status": "healthy" if all_healthy else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "checks": checks
            }
            
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

# Global health checker instance
health_checker = HealthCheck()