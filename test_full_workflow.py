"""
Direct test of CIS agents - bypassing API to see the full workflow
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent

async def test_cis_agents():
    print("🚀 Initializing CIS Agents...\n")
    
    content_agent = ContentAgent()
    virality_agent = ViralityAgent()
    
    # Topic from the SAP image
    topic = "The journey from SAP ECC to S/4HANA (2015-2020): Overcoming early challenges like data migration complexity, custom code remediation, and talent gaps to achieve cloud adoption and industry solutions."
    
    # Mock user profile (SAP expert)
    profile = {
        "writing_tone": "Professional & Insightful",
        "target_audience": "CIOs, SAP Architects, Enterprise IT Leaders",
        "personality_traits": ["Thought Leader"],
        "full_name": "Kunal Bhat"
    }
    
    print(f"📝 Topic: {topic}\n")
    print("=" * 80)
    
    # ITERATION 1: Generate initial draft
    print("\n🤖 AGENT 1: ContentAgent - Generating initial draft...")
    draft_result = await content_agent.generate_post_text(
        topic=topic,
        use_history=False,
        user_id="test_user",
        style="Thought Leadership",
        profile=profile
    )
    
    current_text = draft_result.get("post_text", "")
    print(f"\n✅ Draft Generated:")
    print("-" * 80)
    print(current_text)
    print("-" * 80)
    
    # ITERATION 2: Score the post
    print("\n\n📊 AGENT 2: ViralityAgent - Scoring the post...")
    score_result = await virality_agent.score_post(current_text)
    score = score_result.get("score", 0)
    
    print(f"\n🎯 Virality Score: {score}/100")
    print(f"🔍 Confidence: {score_result.get('confidence')}")
    print(f"💡 Reasoning: {score_result.get('reasoning')}")
    print(f"\n📋 Suggestions:")
    for i, suggestion in enumerate(score_result.get("suggestions", []), 1):
        print(f"   {i}. {suggestion}")
    
    # ITERATION 3: Improve if score < 95
    iteration = 1
    max_iterations = 3
    
    while score < 95 and iteration < max_iterations:
        iteration += 1
        print(f"\n\n{'=' * 80}")
        print(f"🔄 ITERATION {iteration}: Improving post (Current score: {score})")
        print("=" * 80)
        
        # Create feedback based on suggestions
        suggestions = score_result.get("suggestions", [])
        feedback = f"Current score is {score}/100. To reach 95+, focus on: {', '.join(suggestions[:3])}. Make the hook more compelling and add specific metrics or data points."
        
        print(f"\n💬 Feedback to ContentAgent: {feedback}")
        
        # Improve the post
        improved_result = await content_agent.improve_post_text(current_text, feedback)
        current_text = improved_result.get("post_text", current_text)
        
        print(f"\n✅ Improved Draft:")
        print("-" * 80)
        print(current_text)
        print("-" * 80)
        
        # Re-score
        print(f"\n📊 Re-scoring...")
        score_result = await virality_agent.score_post(current_text)
        score = score_result.get("score", 0)
        
        print(f"\n🎯 New Virality Score: {score}/100")
        print(f"🔍 Confidence: {score_result.get('confidence')}")
        print(f"💡 Reasoning: {score_result.get('reasoning')}")
        
        if score >= 95:
            print("\n\n🎉 TARGET ACHIEVED! Score >= 95")
            break
    
    print("\n\n" + "=" * 80)
    print("🏆 FINAL OPTIMIZED POST")
    print("=" * 80)
    print(current_text)
    print("=" * 80)
    print(f"\n📊 Final Score: {score}/100")
    print(f"🔄 Iterations: {iteration}")
    
    return {
        "post_text": current_text,
        "score": score,
        "iterations": iteration
    }

if __name__ == "__main__":
    result = asyncio.run(test_cis_agents())
