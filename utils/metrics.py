"""
Metrics tracking for CIS Dashboard
Tracks generation metrics, user metrics, and performance stats
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import json
from pathlib import Path

# Metrics storage file
METRICS_FILE = Path(__file__).parent.parent / "logs" / "metrics.json"


class MetricsTracker:
    """Track and store application metrics"""
    
    def __init__(self):
        self.metrics = self._load_metrics()
    
    def _load_metrics(self) -> Dict:
        """Load metrics from file"""
        if METRICS_FILE.exists():
            try:
                with open(METRICS_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "generations": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "by_date": {},
                "avg_score": 0,
                "avg_duration": 0,
                "scores": [],
                "durations": []
            },
            "users": {
                "total_signups": 0,
                "active_today": set(),
                "by_date": {}
            },
            "models": {
                "gemini-2.5-flash": 0,
                "gemini-3.0-pro": 0
            }
        }
    
    def _save_metrics(self):
        """Save metrics to file"""
        METRICS_FILE.parent.mkdir(exist_ok=True)
        
        # Convert sets to lists for JSON serialization
        metrics_copy = self.metrics.copy()
        if isinstance(metrics_copy.get("users", {}).get("active_today"), set):
            metrics_copy["users"]["active_today"] = list(metrics_copy["users"]["active_today"])
        
        with open(METRICS_FILE, 'w') as f:
            json.dump(metrics_copy, f, indent=2)
    
    def track_generation(self, success: bool, score: int = 0, duration: float = 0, model: str = "gemini-2.5-flash"):
        """Track a content generation event"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        self.metrics["generations"]["total"] += 1
        
        if success:
            self.metrics["generations"]["success"] += 1
            self.metrics["generations"]["scores"].append(score)
            self.metrics["generations"]["durations"].append(duration)
            
            # Update averages
            scores = self.metrics["generations"]["scores"][-100:]  # Last 100
            durations = self.metrics["generations"]["durations"][-100:]
            self.metrics["generations"]["avg_score"] = sum(scores) / len(scores)
            self.metrics["generations"]["avg_duration"] = sum(durations) / len(durations)
        else:
            self.metrics["generations"]["failed"] += 1
        
        # Track by date
        if today not in self.metrics["generations"]["by_date"]:
            self.metrics["generations"]["by_date"][today] = {"success": 0, "failed": 0}
        
        if success:
            self.metrics["generations"]["by_date"][today]["success"] += 1
        else:
            self.metrics["generations"]["by_date"][today]["failed"] += 1
        
        # Track model usage
        if model not in self.metrics["models"]:
            self.metrics["models"][model] = 0
        self.metrics["models"][model] += 1
        
        self._save_metrics()
    
    def track_user_signup(self):
        """Track new user signup"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.metrics["users"]["total_signups"] += 1
        
        if today not in self.metrics["users"]["by_date"]:
            self.metrics["users"]["by_date"][today] = {"signups": 0, "active": 0}
        self.metrics["users"]["by_date"][today]["signups"] += 1
        
        self._save_metrics()
    
    def track_active_user(self, user_id: str):
        """Track active user"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if isinstance(self.metrics["users"]["active_today"], list):
            self.metrics["users"]["active_today"] = set(self.metrics["users"]["active_today"])
        
        self.metrics["users"]["active_today"].add(user_id)
        
        if today not in self.metrics["users"]["by_date"]:
            self.metrics["users"]["by_date"][today] = {"signups": 0, "active": 0}
        self.metrics["users"]["by_date"][today]["active"] = len(self.metrics["users"]["active_today"])
        
        self._save_metrics()
    
    def get_generation_stats(self) -> Dict:
        """Get generation statistics"""
        return {
            "total": self.metrics["generations"]["total"],
            "success": self.metrics["generations"]["success"],
            "failed": self.metrics["generations"]["failed"],
            "success_rate": (self.metrics["generations"]["success"] / max(1, self.metrics["generations"]["total"])) * 100,
            "avg_score": round(self.metrics["generations"]["avg_score"], 1),
            "avg_duration": round(self.metrics["generations"]["avg_duration"], 2)
        }
    
    def get_user_stats(self) -> Dict:
        """Get user statistics"""
        active_count = len(self.metrics["users"]["active_today"]) if isinstance(self.metrics["users"]["active_today"], (list, set)) else 0
        return {
            "total_signups": self.metrics["users"]["total_signups"],
            "active_today": active_count
        }
    
    def get_model_stats(self) -> Dict:
        """Get model usage statistics"""
        return self.metrics["models"]


# Global metrics instance
_metrics_tracker = None

def get_metrics_tracker() -> MetricsTracker:
    """Get or create the global metrics tracker"""
    global _metrics_tracker
    if _metrics_tracker is None:
        _metrics_tracker = MetricsTracker()
    return _metrics_tracker


def show_metrics_dashboard():
    """Display metrics dashboard in Streamlit"""
    tracker = get_metrics_tracker()
    
    st.markdown("## 📊 Metrics Dashboard")
    
    # Generation metrics
    gen_stats = tracker.get_generation_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Generations", gen_stats["total"])
    with col2:
        st.metric("Success Rate", f"{gen_stats['success_rate']:.1f}%")
    with col3:
        st.metric("Avg Score", gen_stats["avg_score"])
    with col4:
        st.metric("Avg Duration", f"{gen_stats['avg_duration']}s")
    
    # User metrics
    st.markdown("### 👥 User Metrics")
    user_stats = tracker.get_user_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Signups", user_stats["total_signups"])
    with col2:
        st.metric("Active Today", user_stats["active_today"])
    
    # Model usage
    st.markdown("### 🤖 Model Usage")
    model_stats = tracker.get_model_stats()
    
    for model, count in model_stats.items():
        st.write(f"**{model}**: {count} calls")
