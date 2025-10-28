import time
from collections import defaultdict
from typing import Dict

class RateLimiter:
    """Production-grade rate limiter for API calls"""
    
    def __init__(self):
        self.calls: Dict[str, list] = defaultdict(list)
        self.limits = {
            "linkedin_api": {"calls": 100, "period": 3600},  # 100 per hour
            "gemini_api": {"calls": 60, "period": 60}  # 60 per minute
        }
    
    def check_rate_limit(self, api_name: str) -> bool:
        """Check if API call is within rate limit"""
        now = time.time()
        limit_config = self.limits.get(api_name, {"calls": 100, "period": 3600})
        
        # Clean old calls
        self.calls[api_name] = [
            call_time for call_time in self.calls[api_name]
            if now - call_time < limit_config["period"]
        ]
        
        # Check limit
        if len(self.calls[api_name]) >= limit_config["calls"]:
            return False
        
        # Record this call
        self.calls[api_name].append(now)
	return True
    
    def wait_if_needed(self, api_name: str) -> float:
        """Wait if rate limit exceeded, return wait time"""
        if not self.check_rate_limit(api_name):
            limit_config = self.limits.get(api_name, {"calls": 100, "period": 3600})
            oldest_call = min(self.calls[api_name])
            wait_time = limit_config["period"] - (time.time() - oldest_call)
            
            if wait_time > 0:
                print(f"⏳ Rate limit reached for {api_name}. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                return wait_time
        
        return 0.0

# Global rate limiter instance
rate_limiter = RateLimiter()