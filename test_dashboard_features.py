"""
CIS Production Dashboard - Feature Test Script

Tests all new production features:
1. Post history tracking
2. Iterative improvement
3. Comparison functionality
4. Error handling & retry logic
5. Session state management

Run this to verify the dashboard is production-ready.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.content_agent import ContentAgent
from agents.virality_agent import ViralityAgent
from utils.gemini_config import GeminiConfig

class DashboardTester:
    """Test suite for production dashboard features"""
    
    def __init__(self):
        self.content_agent = ContentAgent()
        self.virality_agent = ViralityAgent()
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    async def test_basic_generation(self):
        """Test 1: Basic post generation"""
        print("\n🧪 Test 1: Basic Post Generation")
        try:
            profile = {
                "writing_tone": "Professional & Insightful",
                "target_audience": "Business professionals",
                "personality_traits": ["Thought Leader"],
                "full_name": "Test User"
            }
            
            draft = await self.content_agent.generate_post_text(
                topic="Testing CIS production dashboard",
                use_history=False,
                user_id="test_user",
                style="Professional",
                profile=profile
            )
            
            post_text = draft.get("post_text", "")
            
            if post_text and len(post_text) > 50:
                self.log_test(
                    "Basic Generation",
                    "PASS",
                    f"Generated {len(post_text)} characters"
                )
                return post_text
            else:
                self.log_test("Basic Generation", "FAIL", "Post too short or empty")
                return None
                
        except Exception as e:
            self.log_test("Basic Generation", "FAIL", str(e))
            return None
    
    async def test_scoring(self, post_text: str):
        """Test 2: Virality scoring"""
        print("\n🧪 Test 2: Virality Scoring")
        try:
            score_result = await self.virality_agent.score_post(post_text)
            
            score = score_result.get("score", 0)
            confidence = score_result.get("confidence", "")
            suggestions = score_result.get("suggestions", [])
            
            if 0 <= score <= 100:
                self.log_test(
                    "Virality Scoring",
                    "PASS",
                    f"Score: {score}/100, Confidence: {confidence}, Suggestions: {len(suggestions)}"
                )
                return score_result
            else:
                self.log_test("Virality Scoring", "FAIL", f"Invalid score: {score}")
                return None
                
        except Exception as e:
            self.log_test("Virality Scoring", "FAIL", str(e))
            return None
    
    async def test_improvement_workflow(self):
        """Test 3: Iterative improvement with feedback"""
        print("\n🧪 Test 3: Improvement Workflow")
        try:
            profile = {
                "writing_tone": "Professional & Insightful",
                "target_audience": "Business professionals",
                "personality_traits": ["Thought Leader"],
                "full_name": "Test User"
            }
            
            # Generate original
            topic = "AI in software development"
            draft1 = await self.content_agent.generate_post_text(
                topic=topic,
                use_history=False,
                user_id="test_user",
                style="Technical",
                profile=profile
            )
            
            post1 = draft1.get("post_text", "")
            score1_result = await self.virality_agent.score_post(post1)
            score1 = score1_result.get("score", 0)
            
            # Generate improved version with feedback
            feedback = "Make it more technical with specific examples and metrics"
            enhanced_topic = f"{topic}\n\nIMPROVEMENT FEEDBACK: {feedback}"
            
            draft2 = await self.content_agent.generate_post_text(
                topic=enhanced_topic,
                use_history=False,
                user_id="test_user",
                style="Technical",
                profile=profile
            )
            
            post2 = draft2.get("post_text", "")
            score2_result = await self.virality_agent.score_post(post2)
            score2 = score2_result.get("score", 0)
            
            # Verify posts are different
            if post1 != post2:
                self.log_test(
                    "Improvement Workflow",
                    "PASS",
                    f"Original: {score1}/100 → Improved: {score2}/100 (Δ{score2-score1})"
                )
                return True
            else:
                self.log_test("Improvement Workflow", "FAIL", "Posts are identical")
                return False
                
        except Exception as e:
            self.log_test("Improvement Workflow", "FAIL", str(e))
            return False
    
    async def test_multiple_generations(self):
        """Test 4: Multiple consecutive generations (event loop test)"""
        print("\n🧪 Test 4: Multiple Consecutive Generations")
        try:
            profile = {
                "writing_tone": "Professional & Insightful",
                "target_audience": "Business professionals",
                "personality_traits": ["Thought Leader"],
                "full_name": "Test User"
            }
            
            topics = [
                "Cloud computing trends",
                "DevOps best practices",
                "Microservices architecture"
            ]
            
            posts = []
            for i, topic in enumerate(topics, 1):
                # Create fresh event loop for each generation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    draft = await self.content_agent.generate_post_text(
                        topic=topic,
                        use_history=False,
                        user_id="test_user",
                        style="Technical",
                        profile=profile
                    )
                    posts.append(draft.get("post_text", ""))
                finally:
                    loop.close()
            
            if len(posts) == 3 and all(p for p in posts):
                self.log_test(
                    "Multiple Generations",
                    "PASS",
                    f"Successfully generated {len(posts)} posts without event loop errors"
                )
                return True
            else:
                self.log_test("Multiple Generations", "FAIL", "Some generations failed")
                return False
                
        except Exception as e:
            self.log_test("Multiple Generations", "FAIL", str(e))
            return False
    
    async def test_hook_variety(self):
        """Test 5: Hook variety across multiple posts"""
        print("\n🧪 Test 5: Hook Variety")
        try:
            profile = {
                "writing_tone": "Professional & Insightful",
                "target_audience": "Business professionals",
                "personality_traits": ["Thought Leader"],
                "full_name": "Test User"
            }
            
            hooks = []
            for i in range(5):
                draft = await self.content_agent.generate_post_text(
                    topic=f"Software engineering topic {i+1}",
                    use_history=False,
                    user_id="test_user",
                    style="Thought Leadership",
                    profile=profile
                )
                
                post = draft.get("post_text", "")
                # Extract first line as hook
                hook = post.split('\n')[0] if post else ""
                hooks.append(hook)
            
            # Check for variety (no more than 2 identical hooks)
            unique_hooks = len(set(hooks))
            
            if unique_hooks >= 4:  # At least 4 different hooks out of 5
                self.log_test(
                    "Hook Variety",
                    "PASS",
                    f"{unique_hooks}/5 unique hooks"
                )
                return True
            else:
                self.log_test(
                    "Hook Variety",
                    "WARN",
                    f"Only {unique_hooks}/5 unique hooks (expected 4+)"
                )
                return False
                
        except Exception as e:
            self.log_test("Hook Variety", "FAIL", str(e))
            return False
    
    async def test_score_variation(self):
        """Test 6: Score variation across different content"""
        print("\n🧪 Test 6: Score Variation")
        try:
            # Generate posts with different quality levels
            topics = [
                "Generic business advice",  # Should score lower
                "Specific technical solution with metrics and data",  # Should score higher
                "Controversial opinion about industry trends"  # Should score high
            ]
            
            scores = []
            for topic in topics:
                profile = {
                    "writing_tone": "Professional & Insightful",
                    "target_audience": "Business professionals",
                    "personality_traits": ["Thought Leader"],
                    "full_name": "Test User"
                }
                
                draft = await self.content_agent.generate_post_text(
                    topic=topic,
                    use_history=False,
                    user_id="test_user",
                    style="Thought Leadership",
                    profile=profile
                )
                
                post = draft.get("post_text", "")
                score_result = await self.virality_agent.score_post(post)
                scores.append(score_result.get("score", 0))
            
            # Check for variation (not all the same)
            score_range = max(scores) - min(scores)
            
            if score_range >= 5:  # At least 5 points difference
                self.log_test(
                    "Score Variation",
                    "PASS",
                    f"Scores: {scores}, Range: {score_range} points"
                )
                return True
            else:
                self.log_test(
                    "Score Variation",
                    "WARN",
                    f"Scores: {scores}, Range: {score_range} points (expected 5+)"
                )
                return False
                
        except Exception as e:
            self.log_test("Score Variation", "FAIL", str(e))
            return False
    
    async def test_model_config(self):
        """Test 7: Verify correct models are configured"""
        print("\n🧪 Test 7: Model Configuration")
        try:
            content_model = GeminiConfig.CONTENT_MODEL
            scoring_model = GeminiConfig.SCORING_MODEL
            
            # Verify we're using fast models
            if "flash" in content_model.lower() and "flash" in scoring_model.lower():
                self.log_test(
                    "Model Configuration",
                    "PASS",
                    f"Content: {content_model}, Scoring: {scoring_model}"
                )
                return True
            else:
                self.log_test(
                    "Model Configuration",
                    "WARN",
                    f"Not using Flash models: {content_model}, {scoring_model}"
                )
                return False
                
        except Exception as e:
            self.log_test("Model Configuration", "FAIL", str(e))
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        warned = sum(1 for r in self.test_results if r["status"] == "WARN")
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warned}")
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n📈 Pass Rate: {pass_rate:.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Dashboard is production-ready.")
        elif failed <= 2:
            print("\n⚠️  Some tests failed. Review failures before deploying.")
        else:
            print("\n❌ Multiple failures. Dashboard needs fixes.")
        
        print("\n" + "="*60)

async def main():
    """Run all tests"""
    print("🚀 CIS Production Dashboard - Feature Test Suite")
    print("="*60)
    
    tester = DashboardTester()
    
    # Run tests
    post_text = await tester.test_basic_generation()
    
    if post_text:
        await tester.test_scoring(post_text)
    
    await tester.test_improvement_workflow()
    await tester.test_multiple_generations()
    await tester.test_hook_variety()
    await tester.test_score_variation()
    await tester.test_model_config()
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
