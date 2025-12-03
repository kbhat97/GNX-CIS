#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to create the first LinkedIn post with Imagen 3 image
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8080"
TEST_JWT = "dev_jwt_for_testing"

def create_first_post():
    """Create the first LinkedIn post with AI-generated content and image"""
    
    print("\n" + "="*70)
    print("🚀 CREATING FIRST LINKEDIN POST WITH IMAGEN 3")
    print("="*70)
    
    # Headers
    headers = {
        "Authorization": f"Bearer {TEST_JWT}",
        "Content-Type": "application/json"
    }
    
    # Post data
    post_data = {
        "topic": "AI in Healthcare - Transforming Patient Care",
        "style": "Professional"
    }
    
    print(f"\n📝 Generating post...")
    print(f"   Topic: {post_data['topic']}")
    print(f"   Style: {post_data['style']}")
    print(f"\n⏳ This may take 5-10 seconds (generating content + image)...\n")
    
    try:
        # Generate post
        response = requests.post(
            f"{API_BASE_URL}/posts/generate",
            headers=headers,
            json=post_data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n" + "="*70)
            print("✅ POST CREATED SUCCESSFULLY!")
            print("="*70)
            
            print(f"\n📊 Post Details:")
            print(f"   Status: {data.get('status')}")
            print(f"   Post ID: {data.get('post_id')}")
            
            if 'content' in data:
                print(f"\n📝 Generated Content:")
                print("-" * 70)
                print(data['content'])
                print("-" * 70)
            
            if 'image_path' in data and data['image_path']:
                print(f"\n🎨 Generated Image:")
                print(f"   URL: {data['image_path']}")
                print(f"\n   ✅ Image successfully generated with Imagen 3!")
                print(f"   You can view it at: {data['image_path']}")
            else:
                print(f"\n⚠️ No image generated (Imagen may not be set up yet)")
            
            if 'virality_score' in data:
                print(f"\n📈 Virality Score: {data.get('virality_score')}/10")
            
            if 'suggestions' in data:
                print(f"\n💡 Suggestions:")
                for suggestion in data['suggestions']:
                    print(f"   • {suggestion}")
            
            if 'reasoning' in data:
                print(f"\n🧠 AI Reasoning:")
                print(f"   {data['reasoning']}")
            
            print("\n" + "="*70)
            print("🎉 FIRST POST COMPLETE!")
            print("="*70)
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"first_post_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n💾 Post saved to: {filename}")
            
            return data
            
        else:
            print(f"\n❌ Error creating post:")
            print(f"   Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Message: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out (>30 seconds)")
        print("   This might happen if:")
        print("   1. Imagen is taking longer than expected")
        print("   2. API server is not responding")
        print("   3. Network issues")
        return None
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None

def check_api_health():
    """Check if API is running"""
    print("\n" + "="*70)
    print("🔍 CHECKING API STATUS")
    print("="*70)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API is running!")
            print(f"   Status: {data.get('status')}")
            print(f"   Clerk: {'✅' if data.get('clerk') else '❌'}")
            print(f"   Supabase: {'✅' if data.get('supabase') else '❌'}")
            return True
        else:
            print(f"\n❌ API returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to API at {API_BASE_URL}")
        print(f"   Make sure the API server is running:")
        print(f"   python -m uvicorn main:app --port 8080")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n🎨 LINKEDIN CIS - FIRST POST GENERATOR")
    print("Using Gemini 2.0 Flash + Imagen 3 (Nano Banana Pro)")
    
    # Check API health
    if not check_api_health():
        print("\n⚠️ Please start the API server first")
        exit(1)
    
    # Create first post
    post = create_first_post()
    
    if post:
        print("\n✅ SUCCESS! Your first AI-generated LinkedIn post is ready!")
        print("\nNext steps:")
        print("1. Check the generated image URL (if available)")
        print("2. Review the content")
        print("3. Copy to LinkedIn or use the dashboard")
        print("4. Track engagement!")
    else:
        print("\n❌ Failed to create post. Check the errors above.")
    
    print()
