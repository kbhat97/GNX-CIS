import google.generativeai as genai
import os
import json
from typing import Dict, List
from database.supabase_client import supabase_client
from datetime import datetime, timedelta

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class ReflectorAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def analyze_weekly_performance(self) -> Dict:
        """
        Analyze past week's posts and extract learnings
        
        Returns:
            {
                "insights": [...],
                "top_performers": [...],
                "underperformers": [...],
                "recommendations": [...]
            }
        """
        
        # Get posts from last 7 days
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        posts = supabase_client.table("posts") \
            .select("*") \
            .eq("status", "published") \
            .gte("published_at", week_ago) \
            .execute()
        
        if not posts.data:
            return {
                "insights": ["No posts in the last week"],
                "recommendations": ["Generate first post"]
            }
        
        # Format posts for analysis
        posts_summary = []
        for post in posts.data:
            metrics = post.get("metrics", {})
            engagement_rate = self._calculate_engagement_rate(metrics)
            
            posts_summary.append({
                "topic": post.get("topic", "Unknown"),
                "virality_score": post.get("virality_score", 0),
                "actual_engagement_rate": engagement_rate,
                "likes": metrics.get("likes", 0),
                "comments": metrics.get("comments", 0),
                "shares": metrics.get("shares", 0),
                "post_excerpt": post.get("post_text", "")[:150] + "..."
            })
        
        # Ask Gemini to analyze
        prompt = f"""
        Analyze performance of {len(posts_summary)} LinkedIn posts from the past week.
        
        POSTS DATA:
        {json.dumps(posts_summary, indent=2)}
        
        ANALYSIS TASKS:
        1. Identify top-performing posts (what made them successful?)
        2. Identify underperforming posts (what went wrong?)
        3. Extract content patterns (topics, structures, lengths)
        4. Compare predicted virality vs actual engagement
        5. Provide actionable recommendations for next week
        
        OUTPUT (JSON):
        {{
          "insights": [
            "key insight 1",
            "key insight 2",
            "key insight 3"
          ],
          "top_performers": [
            {{"topic": "...", "why_successful": "..."}}
          ],
          "underperformers": [
            {{"topic": "...", "improvement_needed": "..."}}
          ],
          "recommendations": [
            "specific action 1",
            "specific action 2"
          ],
          "optimal_patterns": {{
            "best_topics": ["..."],
            "best_post_length": "range",
            "best_posting_time": "..."
          }}
        }}
        """
        
        response = await self.model.generate_content_async(prompt)
        
        try:
            result = json.loads(response.text)
            
            # Store insights in memory
            for insight in result.get("insights", []):
                supabase_client.table("agent_memory").insert({
                    "memory_type": "insight",
                    "content": insight,
                    "metadata": {"week": datetime.now().strftime("%Y-W%U")}
                }).execute()
            
            return result
        except json.JSONDecodeError:
            return {
                "error": "Could not parse analysis",
                "raw": response.text
            }
    
    def _calculate_engagement_rate(self, metrics: Dict) -> float:
        """
        Calculate engagement rate from metrics
        
        Engagement Rate = (Likes + Comments + Shares) / Impressions * 100
        """
        if not metrics:
            return 0.0
        
        impressions = metrics.get("impressions", 1)  # Avoid division by zero
        interactions = (
            metrics.get("likes", 0) + 
            metrics.get("comments", 0) + 
            metrics.get("shares", 0)
        )
        
        if impressions > 0:
            return round((interactions / impressions) * 100, 2)
        return 0.0
    
    async def update_content_strategy(self, insights: Dict) -> Dict:
        """
        Update the content strategy based on performance insights
        """
        
        # Extract patterns from successful posts
        optimal_patterns = insights.get("optimal_patterns", {})
        
        # Store strategy updates
        strategy_update = {
            "updated_at": datetime.now().isoformat(),
            "focus_topics": optimal_patterns.get("best_topics", []),
            "avoid_topics": [],
            "optimal_length": optimal_patterns.get("best_post_length", "200-300 words"),
            "posting_schedule": optimal_patterns.get("best_posting_time", "9-11 AM ET"),
            "key_learnings": insights.get("insights", [])
        }
        
        # Save to agent memory
        supabase_client.table("agent_memory").insert({
            "memory_type": "strategy",
            "content": json.dumps(strategy_update),
            "metadata": {"type": "weekly_update"}
        }).execute()
        
        return strategy_update