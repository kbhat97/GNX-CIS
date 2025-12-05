"""
Input sanitization and validation utilities for CIS.

Protects against:
- XSS attacks
- SQL injection
- Prompt injection
- Malicious input
"""

import re
from typing import Optional, Dict, Any
from html import escape
import unicodedata


class InputSanitizer:
    """Sanitizes and validates user input"""
    
    # Maximum lengths for different input types
    MAX_TOPIC_LENGTH = 2000
    MAX_FEEDBACK_LENGTH = 1000
    MAX_EMAIL_LENGTH = 254  # RFC 5321
    MAX_NAME_LENGTH = 100
    
    # Dangerous patterns that might indicate prompt injection
    PROMPT_INJECTION_PATTERNS = [
        r'ignore\s+(previous|above|all)\s+(instructions|prompts|rules)',
        r'system\s*:\s*you\s+are',
        r'<\s*\|\s*im_start\s*\|>',
        r'<\s*\|\s*im_end\s*\|>',
        r'\[\s*INST\s*\]',
        r'\[\s*/\s*INST\s*\]',
        r'###\s*instruction',
        r'forget\s+(everything|all|previous)',
        r'disregard\s+(previous|all)',
        r'new\s+instructions?',
        r'you\s+must\s+now',
        r'override\s+your',
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"('\s*OR\s+'1'\s*=\s*'1)",
        r'("\s*OR\s+"1"\s*=\s*"1)',
        r'(;\s*DROP\s+TABLE)',
        r'(;\s*DELETE\s+FROM)',
        r'(UNION\s+SELECT)',
        r'(INSERT\s+INTO)',
        r'(UPDATE\s+.*\s+SET)',
    ]
    
    @staticmethod
    def sanitize_topic(topic: str) -> str:
        """
        Sanitize topic input for content generation.
        
        Args:
            topic: Raw user input
            
        Returns:
            Sanitized topic string
            
        Raises:
            ValueError: If input is invalid or dangerous
        """
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")
        
        # Normalize unicode characters
        topic = unicodedata.normalize('NFKC', topic)
        
        # Remove null bytes
        topic = topic.replace('\x00', '')
        
        # Trim whitespace
        topic = topic.strip()
        
        # Check length
        if len(topic) > InputSanitizer.MAX_TOPIC_LENGTH:
            raise ValueError(f"Topic exceeds maximum length of {InputSanitizer.MAX_TOPIC_LENGTH} characters")
        
        # Check for prompt injection attempts
        InputSanitizer._check_prompt_injection(topic)
        
        # Check for SQL injection attempts
        InputSanitizer._check_sql_injection(topic)
        
        # Escape HTML to prevent XSS
        topic = escape(topic)
        
        return topic
    
    @staticmethod
    def sanitize_feedback(feedback: str) -> str:
        """
        Sanitize improvement feedback.
        
        Args:
            feedback: Raw user feedback
            
        Returns:
            Sanitized feedback string
            
        Raises:
            ValueError: If input is invalid or dangerous
        """
        if not feedback or not feedback.strip():
            raise ValueError("Feedback cannot be empty")
        
        # Normalize unicode
        feedback = unicodedata.normalize('NFKC', feedback)
        
        # Remove null bytes
        feedback = feedback.replace('\x00', '')
        
        # Trim whitespace
        feedback = feedback.strip()
        
        # Check length
        if len(feedback) > InputSanitizer.MAX_FEEDBACK_LENGTH:
            raise ValueError(f"Feedback exceeds maximum length of {InputSanitizer.MAX_FEEDBACK_LENGTH} characters")
        
        # Check for prompt injection
        InputSanitizer._check_prompt_injection(feedback)
        
        # Escape HTML
        feedback = escape(feedback)
        
        return feedback
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Validate and sanitize email address.
        
        Args:
            email: Raw email input
            
        Returns:
            Sanitized email string
            
        Raises:
            ValueError: If email is invalid
        """
        if not email or not email.strip():
            raise ValueError("Email cannot be empty")
        
        email = email.strip().lower()
        
        # Check length
        if len(email) > InputSanitizer.MAX_EMAIL_LENGTH:
            raise ValueError(f"Email exceeds maximum length of {InputSanitizer.MAX_EMAIL_LENGTH} characters")
        
        # Basic email validation regex (RFC 5322 simplified)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Sanitize user name input.
        
        Args:
            name: Raw name input
            
        Returns:
            Sanitized name string
            
        Raises:
            ValueError: If name is invalid
        """
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        
        # Normalize unicode
        name = unicodedata.normalize('NFKC', name)
        
        # Remove null bytes
        name = name.replace('\x00', '')
        
        # Trim whitespace
        name = name.strip()
        
        # Check length
        if len(name) > InputSanitizer.MAX_NAME_LENGTH:
            raise ValueError(f"Name exceeds maximum length of {InputSanitizer.MAX_NAME_LENGTH} characters")
        
        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValueError("Name contains invalid characters")
        
        # Escape HTML
        name = escape(name)
        
        return name
    
    @staticmethod
    def _check_prompt_injection(text: str) -> None:
        """
        Check for prompt injection attempts.
        
        Args:
            text: Text to check
            
        Raises:
            ValueError: If prompt injection detected
        """
        text_lower = text.lower()
        
        for pattern in InputSanitizer.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise ValueError("Input contains potentially malicious content (prompt injection detected)")
    
    @staticmethod
    def _check_sql_injection(text: str) -> None:
        """
        Check for SQL injection attempts.
        
        Args:
            text: Text to check
            
        Raises:
            ValueError: If SQL injection detected
        """
        text_upper = text.upper()
        
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                raise ValueError("Input contains potentially malicious content (SQL injection detected)")
    
    @staticmethod
    def validate_length(text: str, max_length: int, field_name: str = "Input") -> None:
        """
        Validate text length.
        
        Args:
            text: Text to validate
            max_length: Maximum allowed length
            field_name: Name of the field for error messages
            
        Raises:
            ValueError: If text exceeds max_length
        """
        if len(text) > max_length:
            raise ValueError(f"{field_name} exceeds maximum length of {max_length} characters")
    
    @staticmethod
    def escape_for_prompt(text: str) -> str:
        """
        Escape text for safe use in LLM prompts.
        
        This prevents prompt injection by escaping special sequences.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for prompts
        """
        # Replace special tokens that might confuse the model
        replacements = {
            '<|im_start|>': '[IM_START]',
            '<|im_end|>': '[IM_END]',
            '[INST]': '[INSTRUCTION]',
            '[/INST]': '[/INSTRUCTION]',
            '###': '# # #',
            'System:': 'User says System:',
            'Assistant:': 'User says Assistant:',
        }
        
        escaped = text
        for old, new in replacements.items():
            escaped = escaped.replace(old, new)
        
        return escaped


# Convenience functions
def sanitize_topic(topic: str) -> str:
    """Sanitize topic input"""
    return InputSanitizer.sanitize_topic(topic)


def sanitize_feedback(feedback: str) -> str:
    """Sanitize feedback input"""
    return InputSanitizer.sanitize_feedback(feedback)


def sanitize_email(email: str) -> str:
    """Sanitize email input"""
    return InputSanitizer.sanitize_email(email)


def sanitize_name(name: str) -> str:
    """Sanitize name input"""
    return InputSanitizer.sanitize_name(name)


def escape_for_prompt(text: str) -> str:
    """Escape text for LLM prompts"""
    return InputSanitizer.escape_for_prompt(text)
