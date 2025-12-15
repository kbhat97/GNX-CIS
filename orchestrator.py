import logging
import json
import os
from typing import Dict, Any
from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent
from agents.history_agent import HistoryAgent
from utils.image_generator import create_branded_image
from database.supabase_client import save_draft_post, get_post, update_draft_post
from utils.logger import log_agent_action, log_error

logger = logging.getLogger("LinkedInAgent")

async def run_post_creation_workflow(topic: str, use_history: bool, user_id: str) -> Dict[str, Any]:
    log_agent_action("Orchestrator", "Starting post creation workflow", f"User: {user_id}, Topic: {topic}")
    content_agent = ContentAgent()
    virality_agent = ViralityAgent()
    history_agent = HistoryAgent()
    
    try:
        # Step 1: Get user's learning profile (if history enabled)
        user_profile = None
        if use_history:
            log_agent_action("Orchestrator", "[LEARN] Getting user learning profile", user_id)
            user_profile = await history_agent.analyze_user_history(user_id)
            
            # Check if learning is active (20+ posts)
            if user_profile.get("learning_active") == False:
                posts_needed = user_profile.get("posts_needed", 20)
                log_agent_action("Orchestrator", f"[WAIT] Learning not active yet ({posts_needed} more posts needed)", user_id)
        
        # Step 2: Generate content with profile (if available)
        content_result = await content_agent.generate_post_text(
            topic, use_history, user_id, profile=user_profile
        )
        if "error" in content_result or not content_result.get("post_text"):
            raise Exception(f"Content generation failed: {content_result.get('reasoning', 'Unknown error')}")
        
        post_text = content_result["post_text"]
        
        # Step 3: Independent scoring by ViralityAgent (no self-scoring)
        score_result = await virality_agent.score_post(post_text)
        
        # Step 4: Generate image
        full_image_path = create_branded_image(post_text, "KUNAL BHAT, PMP")
        log_agent_action("Orchestrator", "Image created", full_image_path)
        
        # Step 5: Save draft (this adds to the learning book for future)
        post_data = {
            "user_id": user_id, "topic": topic, "post_text": post_text,
            "reasoning": content_result.get("reasoning"), "virality_score": score_result.get("score"),
            "suggestions": json.dumps(score_result.get("suggestions", [])), "status": "draft", 
            "image_path": full_image_path
        }
        saved_post = save_draft_post(post_data)
        log_agent_action("Orchestrator", "Workflow complete, draft saved", f"Post ID: {saved_post.get('id')}")
        return saved_post
    except Exception as e:
        log_error(e, "Post creation workflow failed")
        return {"error": str(e)}

async def run_post_improvement_workflow(post_id: str, user_id: str, feedback: str) -> Dict[str, Any]:
    log_agent_action("Orchestrator", "Starting post improvement workflow", f"Post ID: {post_id}")
    content_agent = ContentAgent()
    virality_agent = ViralityAgent()
    try:
        original_post = get_post(user_id, post_id)
        if not original_post: raise Exception("Original post not found.")
        
        improved_content = await content_agent.improve_post_text(original_post['post_text'], feedback)
        if "error" in improved_content or not improved_content.get("post_text"):
            raise Exception(f"Content improvement failed: {improved_content.get('reasoning')}")
        
        # --- APPLY THE FIX HERE AS WELL ---
        new_post_text = improved_content["post_text"]
        # ----------------------------------

        new_score_result = await virality_agent.score_post(new_post_text)
        full_image_path = create_branded_image(new_post_text, "KUNAL BHAT, PMP")

        update_data = {
            "post_text": new_post_text,
            "reasoning": improved_content.get("reasoning"),
            "virality_score": new_score_result.get("score"),
            "suggestions": json.dumps(new_score_result.get("suggestions", [])),
            "image_path": full_image_path
        }
        updated_post = update_draft_post(post_id, user_id, update_data)
        log_agent_action("Orchestrator", "Improvement workflow complete", f"Post ID: {post_id}")
        return updated_post
    except Exception as e:
        log_error(e, "Post improvement workflow failed")
        return {"error": str(e)}