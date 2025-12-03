#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create a REAL LinkedIn post matching Kunal Bhat's SAP/S4HANA expertise
"""

import sys
import os
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent
from utils.imagen_generator import create_linkedin_image
import json

async def create_kunal_post(topic: str):
    """Create a post matching Kunal's SAP S/4HANA expertise and style"""
    
    print("\n" + "="*70)
    print("🚀 CREATING LINKEDIN POST - KUNAL BHAT STYLE")
    print("="*70)
    print(f"\n📝 Topic: {topic}")
    
    # Kunal's actual profile
    kunal_profile = {
        "name": "KUNAL BHAT, PMP",
        "title": "Project Manager | S/4HANA Cloud & On-Prem Migration Lead",
        "expertise": "SAP S/4HANA, GRC, Compliance, Global Program Delivery",
        "writing_tone": "Professional, Technical, Results-Driven",
        "target_audience": "SAP Professionals, Enterprise IT Leaders, Project Managers",
        "personality_traits": ["Technical expert", "Data-driven", "Transparent about failures"],
        "content_focus": "S/4HANA migrations, GRC automation, compliance, real project results",
        "typical_metrics": ["% cost savings", "audit readiness scores", "team sizes", "budget figures"],
        "hashtags": ["#SAPS4HANA", "#SAPGRC", "#SAPBTP", "#DigitalTransformation", "#ProjectManagement"]
    }
    
    # Enhanced prompt for Kunal's style
    enhanced_prompt = f"""You are KUNAL BHAT, PMP — an expert SAP S/4HANA migration leader with deep GRC and compliance expertise.

YOUR TASK: Create a high-impact LinkedIn post about: "{topic}"

YOUR VOICE & STYLE:
- You lead $3M-$4.5M global S/4HANA migration programs
- You manage teams of 40-50+ consultants across multiple continents
- You focus on GRC automation, compliance (EU AI Act, GDPR), and risk mitigation
- You're transparent about mistakes and lessons learned
- You use SPECIFIC metrics (%, $, scores, timelines)
- You reference real SAP technologies (SAP BTP, GRC Access Control, SoD, Fiori, SAP Activate)

POST STRUCTURE (CRITICAL - FOLLOW EXACTLY):

**HOOK (Line 1):** Start with a BOLD statement or surprising metric
Example: "Our $4.5M S/4HANA program cut migration risks by 15% using predictive AI."
Example: "7 Steps: 2025 Cross-Border S/4HANA Data Migration De-Risking"

**PROBLEM (2-3 lines):** Describe the specific business challenge
- Use real SAP/S4HANA context
- Mention compliance risks (GDPR, EU AI Act, audit failures)
- Include scale (# of users, regions, budget)

**SOLUTION (3-4 lines):** Your specific approach
- Reference SAP technologies (SAP BTP, GRC, etc.)
- Mention team size and methodology (Agile-Waterfall, SAP Activate)
- Explain the technical innovation

**RESULT (2-3 lines):** Quantifiable outcomes
- Use SPECIFIC metrics: "95% audit readiness", "30% reduction", "$500K saved"
- Include timeline achievements
- Show business impact

**CALL TO ACTION:** End with a challenging question
Example: "How are you embedding GRC Automation into your SAP S/4HANA migration?"
Example: "What's the #1 lesson a project mistake has taught you?"

FORMATTING REQUIREMENTS:
- Use **bold** for key terms (GRC, Data Sovereignty, SoD)
- Include 2-3 emojis MAX (not in every line)
- Keep under 1,300 characters
- Add 8-10 relevant hashtags at the end
- Use numbered lists if presenting steps/lessons

TONE: Professional, authoritative, technically credible, transparent

Return ONLY valid JSON:
{{
    "post_text": "your complete post here",
    "reasoning": "brief explanation of structure and hook choice"
}}"""

    content_agent = ContentAgent()
    virality_agent = ViralityAgent()
    
    try:
        print("\n📝 Generating content with Gemini 2.0 Flash...")
        
        # Use the model directly with custom prompt
        response = await content_agent.model.generate_content_async(enhanced_prompt)
        
        # Parse response
        from utils.json_parser import parse_llm_json_response
        error_payload = {"post_text": "Error generating content.", "reasoning": "JSON parsing failed."}
        content_result = parse_llm_json_response(response.text, error_payload)
        
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
        
        # Calculate virality score
        print(f"\n📊 Calculating virality score...")
        virality_result = await virality_agent.score_post(post_text)
        virality_score = virality_result.get("score", 0)
        suggestions = virality_result.get("suggestions", [])
        
        print(f"\n✅ Virality Score: {virality_score}/10")
        
        if suggestions:
            print(f"\n💡 Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")
        
        # Generate SAP-themed professional image
        print(f"\n🎨 Generating professional SAP-themed image with Imagen 3...")
        
        headline = post_text.split('\n')[0].replace('**', '').strip()[:100]
        
        # Try to generate image
        try:
            image_url = create_linkedin_image(
                topic=topic,
                headline=headline,
                style="professional"
            )
            
            if image_url:
                print(f"\n✅ Image generated successfully!")
                print(f"   URL: {image_url}")
            else:
                print(f"\n⚠️ Image generation returned None (check Imagen setup)")
                image_url = None
        except Exception as e:
            print(f"\n⚠️ Image generation error: {str(e)}")
            image_url = None
        
        final_post = {
            "topic": topic,
            "content": post_text,
            "virality_score": virality_score,
            "suggestions": suggestions,
            "reasoning": reasoning,
            "image_url": image_url,
            "created_at": datetime.now().isoformat(),
            "profile": kunal_profile
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kunal_post_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_post, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*70)
        print("🎉 POST CREATED - KUNAL BHAT STYLE!")
        print("="*70)
        print(f"\n💾 Saved to: {filename}")
        
        return final_post
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    print("\n🎨 LINKEDIN CIS - KUNAL BHAT EDITION")
    print("SAP S/4HANA Migration Expert | GRC & Compliance Leader")
    print("="*70)
    
    # SAP-focused topic
    topic = "Why 80% of S/4HANA Migrations Miss Their GRC Audit Targets (And How We Hit 95%)"
    
    post = await create_kunal_post(topic)
    
    if post:
        print("\n✅ SUCCESS! Professional SAP S/4HANA post ready!")
    else:
        print("\n❌ Failed to create post.")

if __name__ == "__main__":
    asyncio.run(main())
