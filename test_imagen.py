#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for Imagen 3 (Nano Banana Pro) image generation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.imagen_generator import create_linkedin_image, imagen_generator

def test_imagen_setup():
    """Test if Imagen is properly set up"""
    print("\n" + "="*60)
    print("IMAGEN 3 (NANO BANANA PRO) SETUP TEST")
    print("="*60)
    
    # Check if Imagen is enabled
    if not imagen_generator.enabled:
        print("\n❌ Imagen is NOT enabled")
        print("\nPossible reasons:")
        print("1. Vertex AI libraries not installed")
        print("2. Google Cloud authentication not configured")
        print("3. APIs not enabled")
        print("\nSee IMAGEN_SETUP_GUIDE.md for setup instructions")
        return False
    
    print("\n✅ Imagen is enabled and ready!")
    print(f"   Project: {imagen_generator.model._model_name if imagen_generator.model else 'N/A'}")
    print(f"   Bucket: {imagen_generator.bucket.name if imagen_generator.bucket else 'N/A'}")
    
    return True

def test_image_generation():
    """Test generating a sample image"""
    print("\n" + "="*60)
    print("TESTING IMAGE GENERATION")
    print("="*60)
    
    if not imagen_generator.enabled:
        print("\n⚠️ Skipping image generation test (Imagen not enabled)")
        return
    
    print("\nGenerating test image...")
    print("Topic: AI in Healthcare")
    print("Headline: 95% of healthcare AI projects fail. Here's why.")
    
    try:
        image_url = create_linkedin_image(
            topic="AI in Healthcare",
            headline="95% of healthcare AI projects fail. Here's why.",
            style="professional"
        )
        
        if image_url:
            print(f"\n✅ Image generated successfully!")
            print(f"\nPublic URL:")
            print(f"{image_url}")
            print(f"\nYou can view this image in your browser or use it in LinkedIn posts.")
        else:
            print("\n❌ Image generation failed (returned None)")
            print("Check logs for details")
            
    except Exception as e:
        print(f"\n❌ Error during image generation:")
        print(f"   {str(e)}")
        print("\nCheck IMAGEN_SETUP_GUIDE.md for troubleshooting")

def test_quote_card():
    """Test generating a quote card"""
    print("\n" + "="*60)
    print("TESTING QUOTE CARD GENERATION")
    print("="*60)
    
    if not imagen_generator.enabled:
        print("\n⚠️ Skipping quote card test (Imagen not enabled)")
        return
    
    print("\nGenerating quote card...")
    
    try:
        image_url = imagen_generator.generate_quote_card(
            quote="Innovation distinguishes between a leader and a follower",
            author="Steve Jobs"
        )
        
        if image_url:
            print(f"\n✅ Quote card generated successfully!")
            print(f"\nPublic URL:")
            print(f"{image_url}")
        else:
            print("\n❌ Quote card generation failed")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    print("\n🎨 IMAGEN 3 (NANO BANANA PRO) TEST SUITE")
    print("Project: gnx-cis")
    print("Region: us-central1")
    
    # Test 1: Setup verification
    setup_ok = test_imagen_setup()
    
    if setup_ok:
        # Test 2: Basic image generation
        test_image_generation()
        
        # Test 3: Quote card
        # test_quote_card()  # Uncomment to test quote cards
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nNext steps:")
    if not setup_ok:
        print("1. Follow IMAGEN_SETUP_GUIDE.md to complete setup")
        print("2. Run: gcloud auth application-default login")
        print("3. Run: pip install google-cloud-aiplatform")
        print("4. Run this test again")
    else:
        print("1. ✅ Imagen is ready to use!")
        print("2. Images will automatically generate when creating posts")
        print("3. Check your GCS bucket for generated images")
        print("4. Monitor costs in Google Cloud Console")
    print()
