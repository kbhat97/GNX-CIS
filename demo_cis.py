"""
Simplified test to show CIS workflow with clean output
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent

async def demo_cis():
    print("\n" + "="*80)
    print("🚀 CIS CONTENT INTELLIGENCE SYSTEM - LIVE DEMO")
    print("="*80 + "\n")
    
    content_agent = ContentAgent()
    virality_agent = ViralityAgent()
    
    topic = "SAP ECC to S/4HANA migration: Early challenges (2015-2020) including data migration, custom code remediation, and achieving cloud adoption"
    
    profile = {
        "writing_tone": "Professional & Insightful",
        "target_audience": "CIOs, SAP Architects, Enterprise IT Leaders",
        "personality_traits": ["Thought Leader"],
        "full_name": "Kunal Bhat"
    }
    
    print(f"📝 TOPIC: {topic}\n")
    print("🤖 AGENT 1: ContentAgent - Generating post...")
    
    draft = await content_agent.generate_post_text(
        topic=topic,
        use_history=False,
        user_id="test",
        style="Thought Leadership",
        profile=profile
    )
    
    post_text = draft.get("post_text", "")
    
    print("\n✅ GENERATED POST:")
    print("-"*80)
    print(post_text)
    print("-"*80)
    
    print("\n📊 AGENT 2: ViralityAgent - Scoring...")
    score_result = await virality_agent.score_post(post_text)
    score = score_result.get("score", 0)
    
    print(f"\n🎯 VIRALITY SCORE: {score}/100")
    print(f"🔍 CONFIDENCE: {score_result.get('confidence')}")
    print(f"\n💡 REASONING:")
    print(f"   {score_result.get('reasoning')}")
    
    print(f"\n📋 IMPROVEMENT SUGGESTIONS:")
    for i, suggestion in enumerate(score_result.get("suggestions", []), 1):
        print(f"   {i}. {suggestion}")
    
    print("\n" + "="*80)
    print("✅ CIS WORKFLOW COMPLETE")
    print("="*80 + "\n")
    
    return {"post": post_text, "score": score}

if __name__ == "__main__":
    asyncio.run(demo_cis())
