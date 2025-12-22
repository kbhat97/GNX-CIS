#!/usr/bin/env python
"""Quick test of Gemini content generation"""
import asyncio
from utils.gemini_config import GeminiConfig, DIVERSITY_CONFIG

async def test():
    model = GeminiConfig.get_model('content')
    prompt = 'Return ONLY valid JSON like: {"post_text": "Hello world", "reasoning": "test"}'
    resp = await model.generate_content_async(prompt, generation_config=DIVERSITY_CONFIG)
    print("=== RAW RESPONSE ===")
    print(repr(resp.text[:200]))
    print("\n=== PARSED ===")
    from utils.json_parser import parse_llm_json_response
    result = parse_llm_json_response(resp.text, {"error": "failed"})
    print("post_text:", result.get("post_text", "MISSING")[:50] if result.get("post_text") else "NONE")
    print("reasoning:", result.get("reasoning", "MISSING")[:50] if result.get("reasoning") else "NONE")
    print("error:", result.get("error", "NO ERROR"))

if __name__ == "__main__":
    asyncio.run(test())
