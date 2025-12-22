import json
import re
from typing import Dict, Any
from .logger import log_error

def _fix_multiline_json_strings(text: str) -> str:
    """
    Fix literal newlines inside JSON string values.
    LLMs often return multi-line content inside JSON which is invalid.
    This converts literal newlines to \\n escape sequences.
    """
    # More aggressive approach: replace newlines between quotes
    # First, let's try to identify if we're inside a string value
    result = []
    in_string = False
    i = 0
    while i < len(text):
        char = text[i]
        
        if char == '"' and (i == 0 or text[i-1] != '\\'):
            in_string = not in_string
            result.append(char)
        elif char == '\n' and in_string:
            result.append('\\n')
        elif char == '\r' and in_string:
            # Skip \r if followed by \n
            if i + 1 < len(text) and text[i+1] == '\n':
                pass  # Will be handled as \n
            else:
                result.append('\\n')
        else:
            result.append(char)
        i += 1
    
    return ''.join(result)

def parse_llm_json_response(text: str, default_on_error: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans and parses a JSON string from an LLM response, removing markdown and handling control characters.
    
    Args:
        text: The raw text response from the language model.
        default_on_error: The dictionary to return if parsing fails.
    
    Returns:
        A parsed dictionary or the default error dictionary.
    """
    # Remove markdown code blocks (e.g., ```json ... ```)
    # Handle various formats: ```json, ``` alone, with or without newlines
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'```\s*$', '', text.strip())
    text = text.strip()
    
    try:
        # Try parsing with strict=False to handle control characters
        return json.loads(text, strict=False)
    except json.JSONDecodeError as e:
        # If Unterminated string error, try escaping newlines
        if "Unterminated string" in str(e) or "Invalid control character" in str(e):
            try:
                fixed_text = _fix_multiline_json_strings(text)
                return json.loads(fixed_text, strict=False)
            except:
                pass
        
        # Try cleaning control characters manually
        try:
            # Remove invalid control characters (keep \n, \r, \t)
            cleaned_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
            return json.loads(cleaned_text, strict=False)
        except json.JSONDecodeError as e2:
            # If still failing, try extracting JSON object manually
            try:
                # Find first { and last }
                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1:
                    json_str = text[start:end+1]
                    # Clean and escape newlines
                    json_str = _fix_multiline_json_strings(json_str)
                    json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)
                    return json.loads(json_str, strict=False)
            except:
                pass
            
            log_error(e, f"JSON parsing failed for text snippet: {text[:100]}...")
            return default_on_error