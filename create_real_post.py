#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create a REAL LinkedIn post with actual AI generation
Bypasses DEV_MODE to use real Gemini 2.0 Flash + Imagen 3
"""

import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent
from utils.imagen_generator import create_linkedin_image
import json

async def create_real_post(topic: str, style: str = "Professional"):
    """
    Create a real LinkedIn post with:
    - Gemini 2.0 Flash content generation
    - Virality scoring
    - Imagen 3 image generation
    """
    
    print("\n" + "="*70)
    print("🚀 CREATING REAL LINKEDIN POST")
    print("="*70)
    print(f"\n📝 Topic: {topic}")
    print(f"🎨 Style: {style}")
    print("\n⏳ Generating content with Gemini 2.0 Flash...")
    
    # Initialize agents
    content_agent = ContentAgent()
    virality_agent = ViralityAgent()
    
    # Mock user profile (you can customize this)
    user_profile = {
        "writing_tone": "Professional & Engaging",
        "target_audience": "Technology Leaders & AI Practitioners",
        "personality_traits": ["Thought leader", "Technical expert", "Innovative"],
        "content_focus": "AI Agents, Automation, Production Systems"
    }
    
    try:
        # Step 1: Generate content
        print("\n📝 Step 1: Generating viral content...")
        content_result = await content_agent.generate_post_text(
            topic=topic,
            use_history=False,
            user_id="real_user_001",
            style=style,
            profile=user_profile
        )
        
        if "error" in content_result:
            print(f"\n❌ Content generation failed: {content_result['error']}")
            return None
        
        post_text = content_result.get("post_text", "")
        reasoning = content_result.get("reasoning", "")
        
        print(f"\n✅ Content generated!")
        print(f"\n📄 Generated Content:")
        print("-" * 70)
        print(post_text)
        print("-" * 70)
        
        print(f"\n🧠 AI Reasoning:")
        print(f"   {reasoning}")
        
        # Step 2: Calculate virality score
        print(f"\n📊 Step 2: Calculating virality score...")
        virality_result = await virality_agent.score_post(post_text)
        
        virality_score = virality_result.get("score", 0)
        suggestions = virality_result.get("suggestions", [])
        
        print(f"\n✅ Virality Score: {virality_score}/10")
        
        if suggestions:
            print(f"\n💡 Improvement Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")
        
        # Step 3: Generate image with Imagen 3
        print(f"\n🎨 Step 3: Generating professional image with Imagen 3...")
        
        # Extract headline from content (first line)
        headline = post_text.split('\n')[0].replace('**', '').strip()
        if len(headline) > 100:
            headline = headline[:97] + "..."
        
        image_url = create_linkedin_image(
            topic=topic,
            headline=headline,
            style=style.lower()
        )
        
        if image_url:
            print(f"\n✅ Image generated successfully!")
            print(f"   URL: {image_url}")
        else:
            print(f"\n⚠️ Image generation skipped (Imagen not fully configured)")
            image_url = None
        
        # Step 4: Compile final post
        final_post = {
            "topic": topic,
            "style": style,
            "content": post_text,
            "virality_score": virality_score,
            "suggestions": suggestions,
            "reasoning": reasoning,
            "image_url": image_url,
            "created_at": datetime.now().isoformat(),
            "user_profile": user_profile
        }
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_post_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_post, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*70)
        print("🎉 REAL POST CREATED SUCCESSFULLY!")
        print("="*70)
        
        print(f"\n📊 Final Summary:")
        print(f"   ✅ Content: {len(post_text)} characters")
        print(f"   ✅ Virality Score: {virality_score}/10")
        print(f"   ✅ Image: {'Generated' if image_url else 'Skipped'}")
        print(f"   ✅ Suggestions: {len(suggestions)}")
        
        print(f"\n💾 Saved to: {filename}")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Review the content above")
        print(f"   2. Check the image URL (if generated)")
        print(f"   3. Copy to LinkedIn or use the API to publish")
        print(f"   4. Track engagement!")
        
        return final_post
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main function"""
    print("\n🎨 LINKEDIN CIS - REAL POST GENERATOR")
    print("Using Gemini 2.0 Flash + Imagen 3 (Nano Banana Pro)")
    print("="*70)
    
    # Get topic from user or use default
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = "Building AI Agents That Actually Work - 3 Lessons from Production Systems"
    
    # Create the post
    post = await create_real_post(topic, style="Professional")
    
    if post:
        print("\n✅ SUCCESS! Your professional LinkedIn post is ready!")
    else:
        print("\n❌ Failed to create post. Check errors above.")

if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
