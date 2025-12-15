"""
User feedback component for CIS Dashboard
Collects user feedback on generated content
"""
import streamlit as st
from datetime import datetime
from typing import Optional
import json
from pathlib import Path
import os

# Feedback storage
FEEDBACK_FILE = Path(__file__).parent.parent / "logs" / "feedback.json"


def load_feedback() -> list:
    """Load existing feedback"""
    if FEEDBACK_FILE.exists():
        try:
            with open(FEEDBACK_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def save_feedback(feedback_list: list):
    """Save feedback to file"""
    FEEDBACK_FILE.parent.mkdir(exist_ok=True)
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback_list, f, indent=2)


def submit_feedback(
    rating: int,
    feedback_text: str,
    post_id: Optional[int] = None,
    user_id: Optional[str] = None,
    category: str = "general"
) -> bool:
    """
    Submit user feedback
    
    Args:
        rating: 1-5 star rating
        feedback_text: User's feedback text
        post_id: Optional ID of the post being rated
        user_id: User who submitted feedback
        category: Feedback category (general, content, ui, performance)
    
    Returns:
        True if saved successfully
    """
    try:
        feedback_list = load_feedback()
        
        feedback_entry = {
            "id": len(feedback_list) + 1,
            "timestamp": datetime.now().isoformat(),
            "rating": rating,
            "text": feedback_text,
            "post_id": post_id,
            "user_id": user_id,
            "category": category
        }
        
        feedback_list.append(feedback_entry)
        save_feedback(feedback_list)
        
        # Send alert for negative feedback (rating <= 2)
        if rating <= 2:
            _send_negative_feedback_alert(feedback_entry)
        
        return True
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return False


def _send_negative_feedback_alert(feedback: dict):
    """Send alert for negative feedback (placeholder - would integrate with email/Slack)"""
    # In production, this would send an email or Slack notification
    print(f"[WARN] NEGATIVE FEEDBACK ALERT: Rating {feedback['rating']} - {feedback['text'][:100]}")


def show_feedback_button():
    """Show feedback button in sidebar"""
    with st.sidebar:
        if st.button("Give Feedback", use_container_width=True):
            st.session_state.show_feedback_form = True


def show_feedback_form(post_id: Optional[int] = None, user_id: Optional[str] = None):
    """Show the feedback form modal"""
    
    if not st.session_state.get('show_feedback_form', False):
        return
    
    st.markdown("---")
    st.markdown("### Share Your Feedback")
    
    with st.form("feedback_form"):
        # Rating
        rating = st.slider(
            "How would you rate your experience?",
            min_value=1,
            max_value=5,
            value=5,
            help="1 = Poor, 5 = Excellent"
        )
        
        # Star display
        stars = "*" * rating + "-" * (5 - rating)
        st.markdown(f"**Rating: {stars}**")
        
        # Category
        category = st.selectbox(
            "Category",
            ["general", "content_quality", "ui_experience", "performance", "feature_request", "bug_report"]
        )
        
        # Feedback text
        feedback_text = st.text_area(
            "Your feedback",
            placeholder="Tell us what you think...",
            height=100
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit = st.form_submit_button("Submit", type="primary", use_container_width=True)
        
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        
        if submit:
            if feedback_text.strip():
                success = submit_feedback(
                    rating=rating,
                    feedback_text=feedback_text,
                    post_id=post_id,
                    user_id=user_id,
                    category=category
                )
                
                if success:
                    st.success("[OK] Thank you for your feedback!")
                    st.session_state.show_feedback_form = False
                    st.balloons()
                else:
                    st.error("Failed to submit feedback. Please try again.")
            else:
                st.warning("Please enter some feedback text.")
        
        if cancel:
            st.session_state.show_feedback_form = False
            st.rerun()


def show_inline_post_feedback(post_id: int, user_id: Optional[str] = None):
    """Show inline feedback for a specific post"""
    
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])
    
    feedback_key = f"post_feedback_{post_id}"
    
    with col1:
        if st.button("Like", key=f"like_{post_id}", help="Great content!"):
            submit_feedback(5, "Liked this post", post_id, user_id, "content_quality")
            st.toast("Thanks for the feedback!")
    
    with col2:
        if st.button("Dislike", key=f"dislike_{post_id}", help="Needs improvement"):
            submit_feedback(2, "Disliked this post", post_id, user_id, "content_quality")
            st.toast("We'll work on improving!")
    
    with col6:
        if st.button("More feedback", key=f"more_{post_id}"):
            st.session_state.show_feedback_form = True
            st.session_state.feedback_post_id = post_id


def get_feedback_stats() -> dict:
    """Get feedback statistics"""
    feedback_list = load_feedback()
    
    if not feedback_list:
        return {
            "total": 0,
            "avg_rating": 0,
            "positive": 0,
            "negative": 0
        }
    
    ratings = [f["rating"] for f in feedback_list]
    
    return {
        "total": len(feedback_list),
        "avg_rating": round(sum(ratings) / len(ratings), 1),
        "positive": len([r for r in ratings if r >= 4]),
        "negative": len([r for r in ratings if r <= 2])
    }
