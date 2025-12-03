import json
import re
from typing import Dict, Any
from .logger import log_error

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
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    
    try:
        # Try parsing with strict=False to handle control characters
        return json.loads(text, strict=False)
    except json.JSONDecodeError as e:
        # If that fails, try cleaning control characters manually
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
                    # Clean and try again
                    json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)
                    return json.loads(json_str, strict=False)
            except:
                pass
            
            log_error(e, f"JSON parsing failed for text snippet: {text[:100]}...")
            return default_on_error