"""
HistoryAgent - The Learning Book
================================
Analyzes user's past posts from Supabase to understand their style and patterns.
Uses incremental summarization to minimize memory usage on each generation.

Key concept: Instead of re-analyzing ALL posts every time, we:
1. Keep a summarized "learning profile" per user (in user_profiles table)
2. Only analyze NEW posts since last analysis
3. Merge new patterns into existing profile

IMPORTANT: Learning only activates after user has 20+ posts (MIN_POSTS_FOR_LEARNING)
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from utils.gemini_config import GeminiConfig
from database.supabase_client import supabase_client
from utils.logger import log_agent_action, log_error
from utils.json_parser import parse_llm_json_response

# Minimum posts required before learning profile is built
MIN_POSTS_FOR_LEARNING = 20


class HistoryAgent:
    """
    The Learning Book: Analyzes user's Supabase posts to build a style profile.
    
    This agent reads from the user's generated posts (not LinkedIn API) and
    builds an incremental learning profile that improves with each post.
    
    NOTE: Learning only activates after MIN_POSTS_FOR_LEARNING (20) posts.
    """

    def __init__(self):
        self.model = GeminiConfig.get_model("analysis")
        self.supabase = supabase_client

    async def analyze_user_history(self, user_id: str, force_full: bool = False) -> Dict[str, Any]:
        """
        Main entry point: Get or build the user's learning profile.
        
        Args:
            user_id: The user's UUID
            force_full: If True, re-analyze all posts (expensive)
            
        Returns:
            Learning profile dict with style, topics, patterns
        """
        try:
            log_agent_action("HistoryAgent", "📚 Getting learning profile", f"User: {user_id}")
            
            # Step 1: Check if user has minimum posts for learning
            total_posts = await self._get_user_post_count(user_id)
            
            if total_posts < MIN_POSTS_FOR_LEARNING:
                log_agent_action(
                    "HistoryAgent", 
                    f"⏳ Not enough posts for learning ({total_posts}/{MIN_POSTS_FOR_LEARNING})", 
                    f"User: {user_id}"
                )
                # Use async version that also fetches onboarding data
                return await self._not_enough_posts_profile_async(user_id, total_posts)
            
            # Step 2: Get existing profile (if any)
            existing_profile = await self._get_user_profile(user_id)
            
            if not existing_profile:
                log_agent_action("HistoryAgent", "No existing profile, analyzing all posts", user_id)
                return await self._build_full_profile(user_id)
            
            # Step 3: Get only NEW posts since last analysis
            last_analyzed = existing_profile.get("last_analyzed_at")
            new_posts = await self._get_new_posts(user_id, since=last_analyzed)
            
            if not new_posts:
                log_agent_action("HistoryAgent", "✅ Profile up to date, no new posts", user_id)
                return existing_profile
            
            # Step 4: Incrementally merge new learnings
            log_agent_action("HistoryAgent", f"🔄 Merging {len(new_posts)} new posts into profile", user_id)
            updated_profile = await self._merge_new_learnings(existing_profile, new_posts)
            
            # Step 5: Save updated profile
            await self._save_user_profile(user_id, updated_profile)
            
            return updated_profile
            
        except Exception as e:
            log_error(e, "HistoryAgent.analyze_user_history")
            return self._default_style_profile()

    async def _get_user_post_count(self, user_id: str) -> int:
        """Get total number of posts for a user."""
        try:
            result = self.supabase.table("posts") \
                .select("id", count="exact") \
                .eq("user_id", user_id) \
                .execute()
            return result.count if result.count else 0
        except Exception as e:
            log_error(e, "HistoryAgent._get_user_post_count")
            return 0

    def _not_enough_posts_profile(self, current_count: int) -> Dict[str, Any]:
        """Return when user doesn't have enough posts for learning."""
        remaining = MIN_POSTS_FOR_LEARNING - current_count
        return {
            "learning_active": False,
            "posts_count": current_count,
            "posts_needed": remaining,
            "message": f"Generate {remaining} more posts to unlock personalized learning!",
            "writing_style": "Default professional style (learning not yet active)",
            "writing_tone": "Professional",
            "common_topics": [],
            "post_structures": ["Hook → Problem → Solution → CTA"],
            "engagement_patterns": f"Need {MIN_POSTS_FOR_LEARNING}+ posts to analyze patterns",
            "dominant_style": "professional",
            "posts_analyzed_count": 0,
            "last_analyzed_at": None
        }

    async def _get_onboarding_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch onboarding data from user_profiles table.
        This gives AI knowledge of user's preferences even before learning is active.
        """
        try:
            result = self.supabase.table("user_profiles") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                profile = result.data
                return {
                    # Onboarding specific fields
                    "industry": profile.get("industry"),
                    "target_audience": profile.get("target_audience"),
                    "content_style": profile.get("content_style"),
                    "topics": profile.get("topics", []),
                    "primary_goal": profile.get("primary_goal"),
                    
                    # Derived/legacy fields
                    "writing_tone": profile.get("writing_tone", profile.get("content_style", "Professional")),
                    "common_topics": profile.get("topics", profile.get("extracted_themes", [])),
                    "dominant_style": profile.get("dominant_style", "professional"),
                    "brand_voice_summary": profile.get("brand_voice_summary"),
                    
                    # Flag that this is onboarding data, not learned
                    "source": "onboarding"
                }
            return None
        except Exception as e:
            log_error(e, "HistoryAgent._get_onboarding_profile")
            return None

    async def _not_enough_posts_profile_async(self, user_id: str, current_count: int) -> Dict[str, Any]:
        """
        Return profile when user doesn't have enough posts for learning.
        BUT still includes onboarding data so AI knows user's preferences.
        """
        remaining = MIN_POSTS_FOR_LEARNING - current_count
        
        # Get onboarding data (if user completed onboarding)
        onboarding_profile = await self._get_onboarding_profile(user_id)
        
        base_profile = {
            "learning_active": False,
            "posts_count": current_count,
            "posts_needed": remaining,
            "message": f"Generate {remaining} more posts to unlock personalized learning!",
            "post_structures": ["Hook → Problem → Solution → CTA"],
            "engagement_patterns": f"Need {MIN_POSTS_FOR_LEARNING}+ posts to analyze patterns",
            "posts_analyzed_count": 0,
            "last_analyzed_at": None
        }
        
        if onboarding_profile:
            # Merge onboarding data into the profile
            base_profile.update({
                "industry": onboarding_profile.get("industry"),
                "target_audience": onboarding_profile.get("target_audience", "Business professionals"),
                "writing_style": onboarding_profile.get("brand_voice_summary", "Default professional style"),
                "writing_tone": onboarding_profile.get("writing_tone", "Professional"),
                "common_topics": onboarding_profile.get("common_topics", []),
                "dominant_style": onboarding_profile.get("dominant_style", "professional"),
                "primary_goal": onboarding_profile.get("primary_goal"),
                "source": "onboarding"
            })
            log_agent_action("HistoryAgent", "📝 Using onboarding profile data", f"User: {user_id}")
        else:
            # No onboarding data - use defaults
            base_profile.update({
                "writing_style": "Default professional style (learning not yet active)",
                "writing_tone": "Professional",
                "common_topics": [],
                "dominant_style": "professional",
            })
        
        return base_profile

    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch existing learning profile from user_profiles table."""
        try:
            result = self.supabase.table("user_profiles") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                # Convert to learning profile format
                profile = result.data
                return {
                    "writing_style": profile.get("brand_voice_summary", ""),
                    "writing_tone": profile.get("writing_tone", ""),
                    "target_audience": profile.get("target_audience", ""),
                    "common_topics": profile.get("extracted_themes", []),
                    "dominant_style": profile.get("dominant_style", ""),
                    "engagement_patterns": profile.get("engagement_patterns", ""),
                    "posts_analyzed": profile.get("analyzed_post_ids", []),
                    "posts_analyzed_count": len(profile.get("analyzed_post_ids", [])),
                    "last_analyzed_at": profile.get("updated_at"),
                    "personality_traits": profile.get("personality_traits", []),
                    "key_values": profile.get("key_values", []),
                }
            return None
        except Exception as e:
            log_error(e, "HistoryAgent._get_user_profile")
            return None

    async def _get_new_posts(self, user_id: str, since: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Fetch posts created after 'since' timestamp.
        Only gets posts we haven't analyzed yet.
        """
        try:
            query = self.supabase.table("posts") \
                .select("id, content, topic, style, virality_score, suggestions, created_at") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit)
            
            if since:
                query = query.gt("created_at", since)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            log_error(e, "HistoryAgent._get_new_posts")
            return []

    async def _build_full_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Build a complete profile from scratch (first time or force refresh).
        Analyzes up to 20 most recent posts.
        """
        posts = await self._get_new_posts(user_id, since=None, limit=20)
        
        if not posts:
            log_agent_action("HistoryAgent", "No posts found for user", user_id)
            return self._default_style_profile()
        
        # Format posts for LLM analysis
        posts_text = self._format_posts_for_analysis(posts)
        
        analysis_prompt = f"""You are analyzing a LinkedIn content creator's writing patterns.

POSTS TO ANALYZE:
{posts_text}

Analyze these posts and provide a comprehensive profile. Return ONLY valid JSON:
{{
    "writing_style": "Description of their unique voice (formal, casual, storytelling, data-driven, etc.)",
    "writing_tone": "Their primary tone (Professional, Inspirational, Technical, etc.)",
    "common_topics": ["topic1", "topic2", "topic3"],
    "post_structures": ["Most common structure patterns they use"],
    "engagement_patterns": "What types of their posts perform best based on virality scores",
    "avg_post_length": "short/medium/long",
    "hashtag_strategy": "How they use hashtags",
    "key_phrases": ["Recurring phrases or expressions"],
    "strengths": ["What they do well"],
    "improvement_areas": ["Suggestions for improvement"],
    "dominant_style": "professional/storytelling/technical/inspirational/thought_leadership"
}}

Be specific based on the actual posts, not generic advice."""

        try:
            response = await self.model.generate_content_async(analysis_prompt)
            analysis = parse_llm_json_response(response.text, self._default_style_profile())
            
            # Track which posts were analyzed
            analysis["posts_analyzed"] = [p["id"] for p in posts]
            analysis["posts_analyzed_count"] = len(posts)
            analysis["last_analyzed_at"] = datetime.now().isoformat()
            
            # Save to user_profiles
            await self._save_user_profile(user_id, analysis)
            
            log_agent_action("HistoryAgent", f"✅ Full profile built from {len(posts)} posts", user_id)
            return analysis
            
        except Exception as e:
            log_error(e, "HistoryAgent._build_full_profile")
            return self._default_style_profile()

    async def _merge_new_learnings(self, existing: Dict[str, Any], new_posts: List[Dict]) -> Dict[str, Any]:
        """
        Incrementally update profile with new posts.
        This is the 'learning book' concept - each post adds to the knowledge.
        """
        posts_text = self._format_posts_for_analysis(new_posts)
        
        merge_prompt = f"""You are updating a content creator's profile with new learnings.

EXISTING PROFILE:
{json.dumps(existing, indent=2)}

NEW POSTS TO LEARN FROM:
{posts_text}

Update the profile by:
1. Keeping successful patterns that appear in new posts
2. Adding any NEW topics, phrases, or structures
3. Updating engagement_patterns if new posts show different trends
4. Noting any evolution in their style

Return the UPDATED profile as JSON with the same structure as the existing profile.
Focus on MERGING, not replacing. The learning book grows with each post."""

        try:
            response = await self.model.generate_content_async(merge_prompt)
            updated = parse_llm_json_response(response.text, existing)
            
            # Update tracking fields
            analyzed_posts = existing.get("posts_analyzed", [])
            new_post_ids = [p["id"] for p in new_posts]
            updated["posts_analyzed"] = analyzed_posts + new_post_ids
            updated["posts_analyzed_count"] = len(updated["posts_analyzed"])
            updated["last_analyzed_at"] = datetime.now().isoformat()
            
            return updated
            
        except Exception as e:
            log_error(e, "HistoryAgent._merge_new_learnings")
            return existing

    async def _save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """Save/update learning profile to user_profiles table."""
        try:
            # Map our profile to database schema
            db_data = {
                "user_id": user_id,
                "brand_voice_summary": profile.get("writing_style", ""),
                "writing_tone": profile.get("writing_tone", ""),
                "target_audience": profile.get("target_audience", ""),
                "extracted_themes": profile.get("common_topics", []),
                "dominant_style": profile.get("dominant_style", ""),
                "engagement_patterns": profile.get("engagement_patterns", ""),
                "analyzed_post_ids": profile.get("posts_analyzed", []),
                "personality_traits": profile.get("personality_traits", []),
                "key_values": profile.get("key_values", []),
                "updated_at": datetime.now().isoformat()
            }
            
            # Upsert (insert or update)
            result = self.supabase.table("user_profiles") \
                .upsert(db_data, on_conflict="user_id") \
                .execute()
            
            log_agent_action("HistoryAgent", "💾 Profile saved to Supabase", user_id)
            return True
            
        except Exception as e:
            log_error(e, "HistoryAgent._save_user_profile")
            return False

    def _format_posts_for_analysis(self, posts: List[Dict]) -> str:
        """Format posts for LLM analysis with relevant metadata."""
        formatted = []
        for i, post in enumerate(posts, 1):
            content = post.get('content', post.get('text', ''))
            topic = post.get('topic', 'Unknown')
            style = post.get('style', 'Unknown')
            score = post.get('virality_score', 0)
            
            formatted.append(
                f"POST {i}:\n"
                f"Topic: {topic}\n"
                f"Style: {style}\n"
                f"Virality Score: {score}/100\n"
                f"Content:\n{content}\n"
                f"---"
            )
        return "\n\n".join(formatted)

    def _default_style_profile(self) -> Dict[str, Any]:
        """Default profile for new users with no posts."""
        return {
            "writing_style": "Professional and engaging. Balances expertise with accessibility.",
            "writing_tone": "Professional",
            "common_topics": [],
            "post_structures": ["Hook → Problem → Solution → CTA"],
            "engagement_patterns": "No data yet - generate posts to build your profile!",
            "avg_post_length": "medium",
            "hashtag_strategy": "3-5 relevant hashtags",
            "key_phrases": [],
            "strengths": [],
            "improvement_areas": ["Generate more posts to build your learning profile"],
            "dominant_style": "professional",
            "posts_analyzed": [],
            "posts_analyzed_count": 0,
            "last_analyzed_at": None
        }

    # Legacy method for backward compatibility
    async def analyze_past_posts(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        DEPRECATED: Use analyze_user_history instead.
        Kept for backward compatibility with existing code.
        """
        log_agent_action("HistoryAgent", "⚠️ Using deprecated analyze_past_posts, migrating to analyze_user_history", user_id)
        return await self.analyze_user_history(user_id)