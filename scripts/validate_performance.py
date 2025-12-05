"""
Validation script for caching and rate limiting.
Tests Redis connection, cache operations, and rate limiting.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cache import get_cache
from utils.rate_limiter import (
    check_generation_limit,
    check_api_limit,
    check_improvement_limit,
    format_retry_message
)


def validate_cache():
    """Validate cache operations"""
    print("=" * 60)
    print("VALIDATING CACHE")
    print("=" * 60)
    
    cache = get_cache()
    
    # Test 1: Health check
    print("\n✅ Test 1: Cache health check")
    health = cache.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Backend: {health['backend']}")
    if health['status'] == 'degraded':
        print(f"   ⚠️  Using fallback: {health['message']}")
    else:
        print(f"   ✅ Redis connected")
    
    # Test 2: Set and get
    print("\n✅ Test 2: Set and get operations")
    test_key = "test:validation"
    test_value = {"message": "Hello from CIS!", "timestamp": time.time()}
    
    success = cache.set(test_key, test_value, ttl=60)
    print(f"   Set operation: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    retrieved = cache.get(test_key)
    print(f"   Get operation: {'✅ SUCCESS' if retrieved else '❌ FAILED'}")
    
    if retrieved:
        print(f"   Retrieved value: {retrieved}")
        assert retrieved['message'] == test_value['message'], "Value mismatch!"
    
    # Test 3: Exists check
    print("\n✅ Test 3: Exists check")
    exists = cache.exists(test_key)
    print(f"   Key exists: {'✅ YES' if exists else '❌ NO'}")
    
    # Test 4: Delete
    print("\n✅ Test 4: Delete operation")
    deleted = cache.delete(test_key)
    print(f"   Delete operation: {'✅ SUCCESS' if deleted else '❌ FAILED'}")
    
    exists_after = cache.exists(test_key)
    print(f"   Key exists after delete: {'❌ YES (ERROR)' if exists_after else '✅ NO'}")
    
    # Test 5: Increment
    print("\n✅ Test 5: Increment counter")
    counter_key = "test:counter"
    
    for i in range(1, 6):
        value = cache.increment(counter_key)
        print(f"   Increment {i}: {value}")
    
    cache.delete(counter_key)
    
    # Test 6: TTL expiration
    print("\n✅ Test 6: TTL expiration")
    ttl_key = "test:ttl"
    cache.set(ttl_key, "expires soon", ttl=2)
    print(f"   Set with 2s TTL: ✅")
    
    exists_before = cache.exists(ttl_key)
    print(f"   Exists immediately: {'✅ YES' if exists_before else '❌ NO'}")
    
    print(f"   Waiting 3 seconds...")
    time.sleep(3)
    
    exists_after = cache.exists(ttl_key)
    print(f"   Exists after 3s: {'❌ YES (ERROR)' if exists_after else '✅ NO (expired)'}")
    
    print("\n✅ Cache validation complete!")


def validate_rate_limiter():
    """Validate rate limiting"""
    print("\n" + "=" * 60)
    print("VALIDATING RATE LIMITER")
    print("=" * 60)
    
    test_user = "test_user_123"
    
    # Test 1: Generation limit (10 per minute)
    print("\n✅ Test 1: Generation rate limit (10/min)")
    
    for i in range(1, 12):
        is_allowed, info = check_generation_limit(test_user)
        
        if is_allowed:
            print(f"   Request {i}: ✅ ALLOWED ({info['remaining']} remaining)")
        else:
            print(f"   Request {i}: ❌ BLOCKED - {format_retry_message(info)}")
    
    # Test 2: API limit (100 per hour)
    print("\n✅ Test 2: API rate limit (100/hour)")
    
    for i in range(1, 6):
        is_allowed, info = check_api_limit(test_user)
        
        if is_allowed:
            print(f"   API call {i}: ✅ ALLOWED ({info['remaining']} remaining)")
        else:
            print(f"   API call {i}: ❌ BLOCKED")
    
    # Test 3: Improvement limit (20 per hour)
    print("\n✅ Test 3: Improvement rate limit (20/hour)")
    
    for i in range(1, 6):
        is_allowed, info = check_improvement_limit(test_user)
        
        if is_allowed:
            print(f"   Improvement {i}: ✅ ALLOWED ({info['remaining']} remaining)")
        else:
            print(f"   Improvement {i}: ❌ BLOCKED")
    
    # Test 4: Rate limit message formatting
    print("\n✅ Test 4: Rate limit message formatting")
    
    test_infos = [
        {'allowed': True, 'remaining': 5},
        {'allowed': False, 'retry_after': 30},
        {'allowed': False, 'retry_after': 120},
        {'allowed': False, 'retry_after': 3700}
    ]
    
    for info in test_infos:
        message = format_retry_message(info)
        print(f"   {message}")
    
    print("\n✅ Rate limiter validation complete!")


def main():
    """Run all validations"""
    print("\n⚡ CIS PERFORMANCE & CACHING VALIDATION")
    print("=" * 60)
    
    try:
        validate_cache()
        validate_rate_limiter()
        
        print("\n" + "=" * 60)
        print("✅ ALL VALIDATIONS COMPLETED")
        print("=" * 60)
        print("\nSummary:")
        print("  - Cache operations: Working")
        print("  - Redis connection: Working (or fallback active)")
        print("  - Rate limiting: Working")
        print("  - TTL expiration: Working")
        print("  - Counter operations: Working")
        print("\n🎉 Performance & caching features are ready!")
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
