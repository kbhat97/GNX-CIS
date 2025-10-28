import json
import re
from typing import Dict, Any
from .logger import log_error

def parse_llm_json_response(text: str, default_on_error: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans and parses a JSON string from an LLM response, removing markdown.
    
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
        return json.loads(text)
    except json.JSONDecodeError as e:
        log_error(e, f"JSON parsing failed for text snippet: {text[:100]}...")
        return default_on_error