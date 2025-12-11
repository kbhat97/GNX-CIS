"""
Test suite for API Rate Limiter functionality.

Tests that the rate limiter correctly limits:
- 10 post generations per hour per user
- Returns 429 status code when limit exceeded
- Provides retry_after information
"""

import pytest
import asyncio
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.rate_limiter import (
    check_generation_limit,
    get_rate_limiter,
    RateLimiter
)


class TestRateLimiter:
    """Test rate limiter functionality"""
    
    def setup_method(self):
        """Reset rate limiter state before each test"""
        # Clear any existing rate limit data for test user
        limiter = get_rate_limiter()
        limiter.reset_limit("test_rate_limit_user", "generation")
    
    def test_allows_first_10_requests(self):
        """Test that first 10 requests are allowed"""
        test_user = "test_rate_limit_user_10"
        limiter = get_rate_limiter()
        limiter.reset_limit(test_user, "generation")
        
        results = []
        for i in range(10):
            is_allowed, info = check_generation_limit(test_user)
            results.append({
                'request_num': i + 1,
                'allowed': is_allowed,
                'remaining': info.get('remaining', 0)
            })
            print(f"Request {i+1}: allowed={is_allowed}, remaining={info.get('remaining', 0)}")
        
        # All 10 should be allowed
        allowed_count = sum(1 for r in results if r['allowed'])
        assert allowed_count == 10, f"Expected 10 allowed, got {allowed_count}"
        
        # Last request should show 0 remaining
        assert results[-1]['remaining'] == 0, f"Expected 0 remaining after 10 requests, got {results[-1]['remaining']}"
    
    def test_blocks_11th_request(self):
        """Test that 11th request is blocked"""
        test_user = "test_rate_limit_user_11"
        limiter = get_rate_limiter()
        limiter.reset_limit(test_user, "generation")
        
        # Make 10 successful requests
        for i in range(10):
            is_allowed, info = check_generation_limit(test_user)
            assert is_allowed, f"Request {i+1} should be allowed but was blocked"
        
        # 11th request should be blocked
        is_allowed, info = check_generation_limit(test_user)
        
        print(f"11th request: allowed={is_allowed}")
        print(f"Info: {info}")
        
        assert not is_allowed, "11th request should be blocked"
        assert info.get('retry_after', 0) > 0, "Should provide retry_after when blocked"
        assert info.get('remaining', 1) == 0, "Should show 0 remaining"
    
    def test_blocks_12th_request(self):
        """Test that 12th request is also blocked"""
        test_user = "test_rate_limit_user_12"
        limiter = get_rate_limiter()
        limiter.reset_limit(test_user, "generation")
        
        # Make 10 successful requests
        for i in range(10):
            is_allowed, _ = check_generation_limit(test_user)
            assert is_allowed, f"Request {i+1} should be allowed"
        
        # 11th and 12th should be blocked
        is_allowed_11, info_11 = check_generation_limit(test_user)
        is_allowed_12, info_12 = check_generation_limit(test_user)
        
        print(f"11th request: allowed={is_allowed_11}, retry_after={info_11.get('retry_after')}")
        print(f"12th request: allowed={is_allowed_12}, retry_after={info_12.get('retry_after')}")
        
        assert not is_allowed_11, "11th request should be blocked"
        assert not is_allowed_12, "12th request should be blocked"
    
    def test_full_12_request_sequence(self):
        """
        Full integration test: Make 12 requests, verify first 10 succeed and last 2 fail.
        This is the main test requested by the user.
        """
        test_user = f"test_rate_limit_user_full_{datetime.now().strftime('%H%M%S')}"
        limiter = get_rate_limiter()
        limiter.reset_limit(test_user, "generation")
        
        results = []
        
        print("\n" + "="*60)
        print("RATE LIMITER TEST: 12 Request Sequence")
        print("="*60)
        print(f"Test User: {test_user}")
        print(f"Limit: 10 requests per hour")
        print("="*60)
        
        for i in range(12):
            is_allowed, info = check_generation_limit(test_user)
            result = {
                'request_num': i + 1,
                'allowed': is_allowed,
                'remaining': info.get('remaining', 0),
                'retry_after': info.get('retry_after', 0)
            }
            results.append(result)
            
            status = "✅ ALLOWED" if is_allowed else "❌ BLOCKED"
            print(f"Request {i+1:2d}: {status} | remaining={info.get('remaining', 0):2d} | retry_after={info.get('retry_after', 0)}s")
        
        print("="*60)
        
        # Verify first 10 are allowed
        allowed_count = sum(1 for r in results[:10] if r['allowed'])
        assert allowed_count == 10, f"Expected first 10 requests to be allowed, got {allowed_count}"
        
        # Verify last 2 are blocked
        blocked_count = sum(1 for r in results[10:] if not r['allowed'])
        assert blocked_count == 2, f"Expected last 2 requests to be blocked, got {blocked_count}"
        
        print(f"✅ TEST PASSED: {allowed_count}/10 allowed, {blocked_count}/2 blocked")
        print("="*60)
    
    def test_different_users_have_separate_limits(self):
        """Test that different users have independent rate limits"""
        user_a = "test_user_a"
        user_b = "test_user_b"
        
        limiter = get_rate_limiter()
        limiter.reset_limit(user_a, "generation")
        limiter.reset_limit(user_b, "generation")
        
        # User A makes 5 requests
        for _ in range(5):
            is_allowed, _ = check_generation_limit(user_a)
            assert is_allowed
        
        # User B should still have full 10 available
        is_allowed, info = check_generation_limit(user_b)
        assert is_allowed, "User B should be allowed"
        assert info.get('remaining') == 9, f"User B should have 9 remaining, got {info.get('remaining')}"
    
    def test_reset_limit_works(self):
        """Test that reset_limit clears the rate limit state"""
        test_user = "test_reset_user"
        limiter = get_rate_limiter()
        
        # Exhaust the limit
        limiter.reset_limit(test_user, "generation")
        for _ in range(10):
            check_generation_limit(test_user)
        
        # Should be blocked
        is_allowed, _ = check_generation_limit(test_user)
        assert not is_allowed, "Should be blocked after 10 requests"
        
        # Reset the limit
        limiter.reset_limit(test_user, "generation")
        
        # Should be allowed again
        is_allowed, info = check_generation_limit(test_user)
        assert is_allowed, "Should be allowed after reset"
        assert info.get('remaining') == 9, "Should have 9 remaining after reset + 1 request"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])
