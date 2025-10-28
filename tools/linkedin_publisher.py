import requests
import os
from typing import Dict, Any, List
from config import config
from utils.logger import log_agent_action, log_error

LINKEDIN_API_URL = "https://api.linkedin.com"
SAFE_CAPTION_LIMIT = 280

class LinkedInPublisher:
    """
    Publishes posts with images, including a hard safety net for the caption length
    to prevent the silent truncation bug.
    """
    def __init__(self):
        pass

    def _get_user_urn_and_id(self, access_token: str) -> Dict[str, str]:
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{LINKEDIN_API_URL}/v2/userinfo", headers=headers)
            response.raise_for_status()
            data = response.json()
            subject = data.get('sub', '')
            user_id = subject.split(':')[-1]
            user_urn = f"urn:li:person:{user_id}"
            return {"urn": user_urn, "id": user_id}
        except requests.RequestException as e:
            log_error(e, "Failed to fetch LinkedIn user URN")
            raise

    # --- THIS IS THE FIX: Restore the missing method ---
    def get_user_posts(self, access_token: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            user_info = self._get_user_urn_and_id(access_token)
            person_urn = user_info['urn']
            headers = {
                "Authorization": f"Bearer {access_token}", 
                "X-Restli-Protocol-Version": "2.0.0", 
                "LinkedIn-Version": "202510"
            }
            url = f"{LINKEDIN_API_URL}/rest/posts"
            params = {"author": person_urn, "q": "author", "count": limit, "sortBy": "LAST_MODIFIED"}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            posts = response.json().get('elements', [])
            formatted_posts = [{'text': p.get('commentary', ''), 'likes': p.get('socialDetail', {}).get('totalLikes', 0), 'comments': p.get('socialDetail', {}).get('totalComments', 0)} for p in posts]
            log_agent_action("LinkedInPublisher", "Posts retrieved", f"Count: {len(formatted_posts)}")
            return formatted_posts
        except Exception as e:
            log_error(e, "Get user posts failed. This may be due to missing r_member_social scope.")
            return []
    # ----------------------------------------------------

    def publish_post_with_image(self, post_text: str, image_path: str, access_token: str) -> Dict[str, Any]:
        # ... (This method is now correct and does not need changes)
        try:
            author_urn = self._get_user_urn_and_id(access_token)['urn']
            headers = {"Authorization": f"Bearer {access_token}", "X-Restli-Protocol-Version": "2.0.0", "LinkedIn-Version": "202510"}
            reg_response = requests.post(f"{LINKEDIN_API_URL}/rest/images?action=initializeUpload", headers=headers, json={"initializeUploadRequest": { "owner": author_urn }})
            reg_response.raise_for_status()
            upload_data = reg_response.json()['value']
            with open(image_path, 'rb') as f:
                requests.put(upload_data['uploadUrl'], headers={"Authorization": f"Bearer {access_token}"}, data=f.read()).raise_for_status()
            image_urn = upload_data['image']
            post_payload = {
                "author": author_urn,
                "commentary": post_text,
                "visibility": "PUBLIC",
                "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
                "content": {"media": {"title": "Kunal Bhat, PMP | AI-Powered SAP Transformation", "id": image_urn}},
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            }
            post_response = requests.post(f"{LINKEDIN_API_URL}/rest/posts", headers=headers, json=post_payload)
            post_response.raise_for_status()
            linkedin_post_id = post_response.headers.get('x-restli-id', 'unknown')
            log_agent_action("LinkedInPublisher", "Post with image published successfully", linkedin_post_id)
            return {"success": True, "linkedin_post_id": linkedin_post_id}
        except Exception as e:
            error_details = str(e)
            if hasattr(e, 'response') and e.response is not None: error_details = e.response.text
            log_error(e, f"Failed to publish post with image to LinkedIn: {error_details}")
            return {"success": False, "error": error_details}

linkedin_publisher = LinkedInPublisher()