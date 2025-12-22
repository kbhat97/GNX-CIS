#!/usr/bin/env python
"""Test Gemini output length"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from utils.gemini_config import GeminiConfig, DIVERSITY_CONFIG
    
    model = GeminiConfig.get_model('content')
    
    # Request a long response
    prompt = '''Write a 500 word LinkedIn post about AI in manufacturing.
Return as JSON:
{
    "post_text": "the full 500 word post here",
    "reasoning": "your reasoning"
}'''
    
    print("Sending request...")
    response = await model.generate_content_async(prompt, generation_config=DIVERSITY_CONFIG)
    
    text = response.text or "EMPTY"
    print(f"Response length: {len(text)} chars")
    print(f"First 100: {text[:100]}")
    print(f"Last 100: {text[-100:]}")
    
    # Check for finish_reason
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        print(f"Finish reason: {candidate.finish_reason}")
        if hasattr(candidate, 'safety_ratings'):
            print(f"Safety ratings: {candidate.safety_ratings}")

asyncio.run(test())
