#!/usr/bin/env python
"""Test error message matching"""
import json
import sys
sys.path.insert(0, '.')

# Test JSON with literal newline
test_json = '{\n    "post_text": "Hello\nWorld"\n}'

print("=== Test JSON ===")
print(repr(test_json))

print("\n=== Try parsing ===")
try:
    json.loads(test_json)
except json.JSONDecodeError as e:
    print("Error message:", str(e))
    print("Has 'Unterminated string':", "Unterminated string" in str(e))
    print("Has 'Invalid control':", "Invalid control" in str(e))

print("\n=== Test with parser ===")
from utils.json_parser import parse_llm_json_response
error_payload = {"post_text": "Error", "reasoning": "Failed"}
result = parse_llm_json_response(test_json, error_payload)
print("Result:", result)
print("Is error?:", result.get("post_text") == "Error")
