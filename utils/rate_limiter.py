"""
Rate limiter for CIS using Redis or in-memory storage.

Implements:
- Token bucket algorithm
- Sliding window rate limiting
- Per-user and per-IP limits
"""

import time
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import logging

from utils.cache import get_cache

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with multiple strategies"""
    
    def __init__(self):
        """Initialize rate limiter"""
        self.cache = get_cache()
    
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        resource: str = "default"
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limit using sliding window.
        
        Args:
            identifier: User ID, IP address, or other identifier
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            resource: Resource name (e.g., "generation", "api_call")
            
        Returns:
            Tuple of (is_allowed, info_dict)
            info_dict contains: remaining, reset_at, retry_after
        """
        key = f"rate_limit:{resource}:{identifier}"
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        try:
            # Get current request timestamps
            timestamps_json = self.cache.get(key)
            
            if timestamps_json:
                timestamps = timestamps_json if isinstance(timestamps_json, list) else []
            else:
                timestamps = []
            
            # Remove timestamps outside the window
            timestamps = [ts for ts in timestamps if ts > window_start]
            
            # Check if limit exceeded
            if len(timestamps) >= max_requests:
                # Calculate when the oldest request will expire
                oldest_timestamp = min(timestamps)
                retry_after = oldest_timestamp + window_seconds - current_time
                
                return False, {
                    'allowed': False,
                    'remaining': 0,
                    'limit': max_requests,
                    'reset_at': oldest_timestamp + window_seconds,
                    'retry_after': max(retry_after, 0),
                    'window_seconds': window_seconds
                }
            
            # Add current timestamp
            timestamps.append(current_time)
            
            # Save back to cache
            self.cache.set(key, timestamps, ttl=window_seconds + 60)
            
            remaining = max_requests - len(timestamps)
            reset_at = current_time + window_seconds
            
            return True, {
                'allowed': True,
                'remaining': remaining,
                'limit': max_requests,
                'reset_at': reset_at,
                'retry_after': 0,
                'window_seconds': window_seconds
            }
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On error, allow the request (fail open)
            return True, {
                'allowed': True,
                'remaining': max_requests,
                'limit': max_requests,
                'error': str(e)
            }
    
    def check_token_bucket(
        self,
        identifier: str,
        capacity: int,
        refill_rate: float,
        resource: str = "default"
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check rate limit using token bucket algorithm.
        
        Args:
            identifier: User ID or identifier
            capacity: Maximum tokens (burst capacity)
            refill_rate: Tokens added per second
            resource: Resource name
            
        Returns:
            Tuple of (is_allowed, info_dict)
        """
        key = f"token_bucket:{resource}:{identifier}"
        current_time = time.time()
        
        try:
            # Get bucket state
            bucket_data = self.cache.get(key)
            
            if bucket_data:
                tokens = bucket_data.get('tokens', capacity)
                last_refill = bucket_data.get('last_refill', current_time)
            else:
                tokens = capacity
                last_refill = current_time
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * refill_rate
            tokens = min(capacity, tokens + tokens_to_add)
            
            # Check if we have at least 1 token
            if tokens >= 1:
                # Consume 1 token
                tokens -= 1
                
                # Save bucket state
                self.cache.set(key, {
                    'tokens': tokens,
                    'last_refill': current_time
                }, ttl=int(capacity / refill_rate) + 60)
                
                return True, {
                    'allowed': True,
                    'tokens_remaining': int(tokens),
                    'capacity': capacity,
                    'refill_rate': refill_rate
                }
            else:
                # Calculate retry after
                tokens_needed = 1 - tokens
                retry_after = tokens_needed / refill_rate
                
                return False, {
                    'allowed': False,
                    'tokens_remaining': 0,
                    'capacity': capacity,
                    'refill_rate': refill_rate,
                    'retry_after': int(retry_after) + 1
                }
                
        except Exception as e:
            logger.error(f"Token bucket check error: {e}")
            # On error, allow the request
            return True, {
                'allowed': True,
                'error': str(e)
            }
    
    def reset_limit(self, identifier: str, resource: str = "default") -> bool:
        """
        Reset rate limit for an identifier.
        
        Args:
            identifier: User ID or identifier
            resource: Resource name
            
        Returns:
            True if successful
        """
        try:
            key = f"rate_limit:{resource}:{identifier}"
            return self.cache.delete(key)
        except Exception as e:
            logger.error(f"Rate limit reset error: {e}")
            return False
    
    def get_limit_info(
        self,
        identifier: str,
        resource: str = "default"
    ) -> Optional[Dict[str, any]]:
        """
        Get current rate limit info without consuming quota.
        
        Args:
            identifier: User ID or identifier
            resource: Resource name
            
        Returns:
            Info dict or None
        """
        try:
            key = f"rate_limit:{resource}:{identifier}"
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Get limit info error: {e}")
            return None


# Global rate limiter instance
_rate_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter_instance
    
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter()
    
    return _rate_limiter_instance


# Convenience functions for common rate limits
def check_generation_limit(user_id: str) -> Tuple[bool, Dict[str, any]]:
    """
    Check if user can generate a post (max 10 per HOUR).
    
    Args:
        user_id: User identifier
        
    Returns:
        Tuple of (is_allowed, info_dict)
    """
    return get_rate_limiter().check_rate_limit(
        identifier=user_id,
        max_requests=10,
        window_seconds=3600,  # 1 hour
        resource="generation"
    )


def check_api_limit(user_id: str) -> Tuple[bool, Dict[str, any]]:
    """
    Check if user can make API call (max 100 per hour).
    
    Args:
        user_id: User identifier
        
    Returns:
        Tuple of (is_allowed, info_dict)
    """
    return get_rate_limiter().check_rate_limit(
        identifier=user_id,
        max_requests=100,
        window_seconds=3600,
        resource="api_call"
    )


def check_improvement_limit(user_id: str) -> Tuple[bool, Dict[str, any]]:
    """
    Check if user can improve a post (max 20 per hour).
    
    Args:
        user_id: User identifier
        
    Returns:
        Tuple of (is_allowed, info_dict)
    """
    return get_rate_limiter().check_rate_limit(
        identifier=user_id,
        max_requests=20,
        window_seconds=3600,
        resource="improvement"
    )


def format_retry_message(info: Dict[str, any]) -> str:
    """
    Format user-friendly rate limit message.
    
    Args:
        info: Rate limit info dict
        
    Returns:
        Formatted message
    """
    if info.get('allowed'):
        return f"✅ {info.get('remaining', 0)} requests remaining"
    
    retry_after = info.get('retry_after', 0)
    
    if retry_after < 60:
        return f"⏳ Rate limit exceeded. Try again in {retry_after} seconds."
    elif retry_after < 3600:
        minutes = retry_after // 60
        return f"⏳ Rate limit exceeded. Try again in {minutes} minutes."
    else:
        hours = retry_after // 3600
        return f"⏳ Rate limit exceeded. Try again in {hours} hours."
