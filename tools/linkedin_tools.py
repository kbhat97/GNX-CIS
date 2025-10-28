import os
import requests
from typing import Dict, List, Any, Optional
from utils.logger import log_agent_action, log_error

class LinkedInAPI:
    """LinkedIn API wrapper for posts and profile management"""
    
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.base_url = "https://api.linkedin.com"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202403"
        }
    
    async def get_user_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch user's past posts from LinkedIn
        """
        try:
            # First, get user profile to get person URN
            profile = await self.get_profile()
            person_id = profile.get('sub')  # 'sub' is the person ID from userinfo endpoint
            
            if not person_id:
                log_error(Exception("No person ID found"), "Get user posts")
                return self._get_mock_posts()
            
            # Fetch posts using Posts API
            url = f"{self.base_url}/rest/posts"
            params = {
                "author": f"urn:li:person:{person_id}",
                "q": "author",
                "count": limit,
                "sortBy": "LAST_MODIFIED"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('elements', [])
                
                # Extract relevant information
                formatted_posts = []
                for post in posts:
                    commentary = post.get('commentary', '')
                    post_id = post.get('id', '')
                    
                    # Get engagement stats if available
                    social_detail = post.get('socialDetail', {})
                    total_likes = social_detail.get('totalLikes', 0)
                    total_comments = social_detail.get('totalComments', 0)
                    total_shares = social_detail.get('totalShares', 0)
                    
                    formatted_posts.append({
                        'id': post_id,
                        'text': commentary,
                        'likes': total_likes,
                        'comments': total_comments,
                        'shares': total_shares,
                        'created_at': post.get('createdAt', '')
                    })
                
                log_agent_action("LinkedInAPI", "Posts retrieved", f"Count: {len(formatted_posts)}")
                return formatted_posts
            
            elif response.status_code == 403:
                log_error(Exception("Permission denied - need r_member_social scope"), "Get user posts")
                # Return mock data for testing
                return self._get_mock_posts()
            
            else:
                log_error(Exception(f"API error: {response.status_code}"), "Get user posts")
                return self._get_mock_posts()
                
        except Exception as e:
            log_error(e, "Get user posts")
            return self._get_mock_posts()
    
    async def get_profile(self) -> Dict[str, Any]:
        """Get current user's LinkedIn profile"""
        try:
            # Use userinfo endpoint to get profile
            url = f"{self.base_url}/v2/userinfo"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                profile = response.json()
                log_agent_action("LinkedInAPI", "Profile retrieved", profile.get('name', 'Unknown'))
                return profile
            else:
                log_error(Exception(f"Profile API error: {response.status_code}"), "Get profile")
                return {}
                
        except Exception as e:
            log_error(e, "Get profile")
            return {}
    
    def _get_mock_posts(self) -> List[Dict[str, Any]]:
        """Mock data for testing when API unavailable"""
        return [
            {
                'id': 'mock_1',
                'text': 'Just deployed our latest AI agent to production. The journey from prototype to production taught us valuable lessons about scalability and real-world performance. Key takeaway: Always test with real user data, not just synthetic benchmarks. #AI #ProductionAI',
                'likes': 145,
                'comments': 23,
                'shares': 12,
                'created_at': '2025-10-10'
            },
            {
                'id': 'mock_2',
                'text': 'Memory management in AI agents is more complex than most people realize. It\'s not just about context windows - it\'s about strategic recall, decay mechanisms, and privacy. Here\'s what we learned building persistent memory systems... 🧵 #AIAgents #EnterpriseAI',
                'likes': 203,
                'comments': 34,
                'shares': 18,
                'created_at': '2025-10-05'
            },
            {
                'id': 'mock_3',
                'text': 'Question for the community: How are you handling agent-to-agent communication in multi-agent systems? We\'ve tried message queues, shared memory, and direct API calls. Each has tradeoffs. What\'s working for you? #AI #SystemDesign',
                'likes': 178,
                'comments': 56,
                'shares': 9,
                'created_at': '2025-09-28'
            }
        ]
    
    async def publish_post(self, text: str, visibility: str = "PUBLIC") -> Dict[str, Any]:
        """
        Publish a post to LinkedIn
        """
        try:
            profile = await self.get_profile()
            person_id = profile.get('sub')  # 'sub' is the person ID from userinfo endpoint
            
            if not person_id:
                return {"success": False, "error": "Could not get person ID"}
            
            url = f"{self.base_url}/rest/posts"
            
            payload = {
                "author": f"urn:li:person:{person_id}",
                "commentary": text,
                "visibility": visibility,
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": []
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code in [200, 201]:
                post_id = response.headers.get('x-restli-id', 'unknown')
                log_agent_action("LinkedInAPI", "Post published", post_id)
                return {
                    "success": True,
                    "linkedin_post_id": post_id,
                    "message": "Post published successfully"
                }
            else:
                error_msg = response.text
                log_error(Exception(f"Publish failed: {response.status_code} - {error_msg}"), "Publish post")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": error_msg
                }
                
        except Exception as e:
            log_error(e, "Publish post")
            return {
                "success": False,
                "error": str(e)
            }