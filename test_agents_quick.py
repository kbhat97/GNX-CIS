"""
Quick test to verify agents work correctly
"""
import asyncio
from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent

async def test_generation():
    print("Creating agents...")
    content_agent = ContentAgent()
    virality_agent = ViralityAgent()
    
    profile = {
        "writing_tone": "Professional & Insightful",
        "target_audience": "Business professionals",
        "personality_traits": ["Thought Leader"],
        "full_name": "Kunal Bhat"
    }
    
    print("Generating content...")
    draft = await content_agent.generate_post_text(
        topic="SAP S/4HANA migration challenges",
        use_history=False,
        user_id="test_user",
        style="Technical",
        profile=profile
    )
    
    post_text = draft.get("post_text", "")
    print(f"\nGenerated post ({len(post_text)} chars):")
    print(post_text[:200] + "...")
    
    print("\nScoring post...")
    score_result = await virality_agent.score_post(post_text)
    
    print(f"\nScore: {score_result.get('score')}/100")
    print(f"Confidence: {score_result.get('confidence')}")
    print(f"Suggestions: {len(score_result.get('suggestions', []))}")
    
    return {
        "content": post_text,
        "score": score_result.get("score", 0),
        "confidence": score_result.get("confidence", ""),
    }

if __name__ == "__main__":
    print("Testing CIS agents...")
    result = asyncio.run(test_generation())
    print("\n✅ Test completed successfully!")
    print(f"Final score: {result['score']}/100")
