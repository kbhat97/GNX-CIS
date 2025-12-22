#!/usr/bin/env python
"""Test the JSON fixer"""
import sys
sys.path.insert(0, '.')
from utils.json_parser import _fix_multiline_json_strings
import json

# Test with literal newline inside string
test_input = '{\n    "post_text": "Hello\nworld\nthird line"\n}'

print("=== INPUT ===")
print(repr(test_input))

print("\n=== FIXED ===")
fixed = _fix_multiline_json_strings(test_input)
print(repr(fixed))

print("\n=== PARSE ===")
try:
    result = json.loads(fixed)
    print("SUCCESS:", result)
except Exception as e:
    print("FAIL:", e)
