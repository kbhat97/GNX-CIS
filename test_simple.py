"""
Simple Gemini 3.0 Pro test - saves output to JSON
"""
import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent
from utils.gemini_config import GeminiConfig

async def test():
    content_agent = ContentAgent()
    virality_agent = ViralityAgent()
    
    result = {
        "test_time": datetime.now().isoformat(),
        "models": {
            "content": GeminiConfig.CONTENT_MODEL,
            "scoring": GeminiConfig.SCORING_MODEL
        }
    }
    
    topic = "SAP ECC to S/4HANA migration challenges (2015-2020)"
    
    profile = {
        "writing_tone": "Professional & Insightful",
        "target_audience": "CIOs, SAP Architects",
        "personality_traits": ["Thought Leader"],
        "full_name": "Kunal Bhat"
    }
    
    # Generate content
    draft = await content_agent.generate_post_text(
        topic=topic,
        use_history=False,
        user_id="test",
        style="Thought Leadership",
        profile=profile
    )
    
    result["generated_post"] = draft.get("post_text", "")
    result["reasoning"] = draft.get("reasoning", "")
    
    # Score it
    score_data = await virality_agent.score_post(result["generated_post"])
    result["virality_score"] = score_data.get("score", 0)
    result["confidence"] = score_data.get("confidence", "")
    result["scoring_reasoning"] = score_data.get("reasoning", "")
    result["suggestions"] = score_data.get("suggestions", [])
    
    # Save to JSON
    with open("gemini_3_test_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Test complete! Results saved to gemini_3_test_result.json")
    print(f"Model used: {result['models']['content']}")
    print(f"Virality Score: {result['virality_score']}/100")
    
    return result

if __name__ == "__main__":
    asyncio.run(test())
