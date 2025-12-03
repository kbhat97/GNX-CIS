"""
Quick test of Gemini 3.0 Pro content generation
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force reload of config
import importlib
import utils.gemini_config
importlib.reload(utils.gemini_config)

from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent

async def test_gemini_3_pro():
    print("\n" + "="*80)
    print("🚀 TESTING GEMINI 3.0 PRO CONTENT GENERATION")
    print("="*80 + "\n")
    
    content_agent = ContentAgent()
    virality_agent = ViralityAgent()
    
    # Check which model is being used
    from utils.gemini_config import GeminiConfig
    print(f"📊 Content Model: {GeminiConfig.CONTENT_MODEL}")
    print(f"📊 Scoring Model: {GeminiConfig.SCORING_MODEL}\n")
    
    topic = "SAP ECC to S/4HANA migration: Overcoming data migration complexity, custom code remediation, and talent gaps (2015-2020)"
    
    profile = {
        "writing_tone": "Professional & Insightful",
        "target_audience": "CIOs, SAP Architects, Enterprise IT Leaders",
        "personality_traits": ["Thought Leader"],
        "full_name": "Kunal Bhat"
    }
    
    print(f"📝 TOPIC: {topic}\n")
    print("🤖 ContentAgent (Gemini 3.0 Pro) - Generating post...\n")
    
    draft = await content_agent.generate_post_text(
        topic=topic,
        use_history=False,
        user_id="test",
        style="Thought Leadership",
        profile=profile
    )
    
    post_text = draft.get("post_text", "")
    
    print("✅ GENERATED POST:")
    print("-"*80)
    print(post_text)
    print("-"*80)
    
    print("\n📊 ViralityAgent (Gemini 2.0 Flash) - Scoring...\n")
    score_result = await virality_agent.score_post(post_text)
    score = score_result.get("score", 0)
    
    print(f"🎯 VIRALITY SCORE: {score}/100")
    print(f"🔍 CONFIDENCE: {score_result.get('confidence')}")
    print(f"\n💡 REASONING:")
    print(f"   {score_result.get('reasoning')}")
    
    print(f"\n📋 IMPROVEMENT SUGGESTIONS:")
    for i, suggestion in enumerate(score_result.get("suggestions", []), 1):
        print(f"   {i}. {suggestion}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")
    
    return {"post": post_text, "score": score}

if __name__ == "__main__":
    asyncio.run(test_gemini_3_pro())
