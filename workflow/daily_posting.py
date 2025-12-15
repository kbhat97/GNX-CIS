import asyncio
import os
import json
import random
from datetime import datetime

# Set Windows event loop policy
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Import agents
from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent
from agents.publisher_agent import PublisherAgent

# Import database
from database.supabase_client import save_draft_post, approve_post

# Import logger
from utils.logger import log, log_agent_action

async def daily_post():
    """Automated daily posting workflow"""
    log("=== Starting Daily Post Workflow ===")
    
    # Load topics from environment
    try:
        topics = json.loads(os.getenv("CONTENT_TOPICS", '["AI agents","Memory management","Production AI"]'))
        topic = random.choice(topics)
        log_agent_action("System", "Topic selected", topic)
    except Exception as e:
        topic = "AI agent architecture"
        log_error(e, "Topic selection")
    
    # Generate content
    try:
        content_agent = ContentAgent()
        post_data = await content_agent.generate_post(topic)
        log_agent_action("ContentAgent", "Generated post", f"Length: {len(post_data['post_text'])}")
    except Exception as e:
        log_error(e, "Content generation")
        return
    
    # Score for virality
    try:
        virality_agent = ViralityAgent()
        virality_result = await virality_agent.score_post(post_data["post_text"])
        score = virality_result["score"]
        log_agent_action("ViralityAgent", "Scored post", f"Score: {score}")
    except Exception as e:
        log_error(e, "Virality scoring")
        score = 50  # Default score
    
    # Save to database
    try:
        draft_data = {
            "post_text": post_data["post_text"],
            "topic": topic,
            "virality_score": score,
            "reasoning": virality_result.get("reasoning", "")
        }
        
        saved_post = save_draft_post(draft_data)
        post_id = saved_post["id"]
        log_agent_action("Database", "Draft saved", post_id)
        
    except Exception as e:
        log_error(e, "Database save")
        return
    
    # Auto-publish if score is high enough
    if score >= 70:
        try:
            approve_post(post_id)
            publisher = PublisherAgent()
            result = await publisher.publish_post(
                post_text=post_data["post_text"],
                post_id=post_id
            )
            
            if result["success"]:
                log_agent_action("PublisherAgent", "Auto-published", result['linkedin_post_id'])
                log(f"[OK] Auto-published post with score {score}")
            else:
                log_error(Exception(result.get('error')), "Auto-publishing")
                
        except Exception as e:
            log_error(e, "Auto-publishing")
    else:
        log(f"[HOLD] Post saved for review (score: {score} < 70)")
    
    log("=== Daily Post Workflow Complete ===")

if __name__ == "__main__":
    asyncio.run(daily_post())