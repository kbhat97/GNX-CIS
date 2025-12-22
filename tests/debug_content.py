#!/usr/bin/env python
"""Full ContentAgent test"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from agents.content_agent import ContentAgent
    
    print("=== Creating ContentAgent ===")
    agent = ContentAgent()  # No supabase
    
    print("\n=== Calling generate_post_text ===")
    result = await agent.generate_post_text('AI in manufacturing', False, 'test_user')
    
    print("\n=== RESULT ===")
    post = result.get('post_text', 'MISSING')
    print("post_text length:", len(post))
    print("Is error?:", post.startswith("Error"))
    if not post.startswith("Error"):
        print("First 200 chars:", post[:200])
    else:
        print("Error:", post)
        print("Reasoning:", result.get('reasoning', 'NONE'))

asyncio.run(test())
