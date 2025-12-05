"""
Content moderation and filtering for CIS.

Detects and filters:
- Harmful content
- Hate speech
- Spam
- Inappropriate content
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ContentRiskLevel(Enum):
    """Risk levels for content"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentCategory(Enum):
    """Categories of problematic content"""
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SEXUAL = "sexual"
    SPAM = "spam"
    PROFANITY = "profanity"
    PERSONAL_INFO = "personal_info"
    SCAM = "scam"


class ContentFilter:
    """Filters and moderates user-generated content"""
    
    # Profanity patterns (basic list - expand as needed)
    PROFANITY_PATTERNS = [
        r'\bf+u+c+k+',
        r'\bs+h+i+t+',
        r'\ba+s+s+h+o+l+e+',
        r'\bb+i+t+c+h+',
        r'\bd+a+m+n+',
        r'\bc+r+a+p+',
    ]
    
    # Hate speech indicators (simplified - use ML model in production)
    HATE_SPEECH_PATTERNS = [
        r'\b(hate|kill|destroy)\s+(all\s+)?(jews|muslims|christians|blacks|whites|asians)',
        r'\b(inferior|superior)\s+race',
        r'\bgenocide\b',
    ]
    
    # Violence indicators
    VIOLENCE_PATTERNS = [
        r'\b(kill|murder|assassinate|bomb|shoot|stab)\s+(him|her|them|you)',
        r'\bmass\s+(shooting|murder)',
        r'\bterrorist\s+attack',
    ]
    
    # Spam indicators
    SPAM_PATTERNS = [
        r'(click|buy|order)\s+now',
        r'limited\s+time\s+offer',
        r'act\s+fast',
        r'100%\s+(free|guaranteed)',
        r'make\s+\$\d+\s+(per|a)\s+(day|hour|week)',
        r'work\s+from\s+home',
        r'(viagra|cialis|pharmacy)',
    ]
    
    # Personal information patterns
    PII_PATTERNS = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{16}\b',  # Credit card
        r'\b\d{3}-\d{3}-\d{4}\b',  # Phone number
    ]
    
    # Scam indicators
    SCAM_PATTERNS = [
        r'nigerian\s+prince',
        r'won\s+the\s+lottery',
        r'claim\s+your\s+prize',
        r'verify\s+your\s+account',
        r'urgent\s+action\s+required',
        r'suspended\s+account',
    ]
    
    @staticmethod
    def moderate_content(text: str) -> Dict[str, any]:
        """
        Moderate content and return risk assessment.
        
        Args:
            text: Content to moderate
            
        Returns:
            Dict with:
                - risk_level: ContentRiskLevel
                - is_safe: bool
                - flags: List[ContentCategory]
                - reasons: List[str]
                - filtered_text: str (with PII removed)
        """
        flags = []
        reasons = []
        risk_score = 0
        
        text_lower = text.lower()
        
        # Check for hate speech
        for pattern in ContentFilter.HATE_SPEECH_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                flags.append(ContentCategory.HATE_SPEECH)
                reasons.append("Contains hate speech")
                risk_score += 50
                break
        
        # Check for violence
        for pattern in ContentFilter.VIOLENCE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                flags.append(ContentCategory.VIOLENCE)
                reasons.append("Contains violent content")
                risk_score += 40
                break
        
        # Check for spam
        spam_count = 0
        for pattern in ContentFilter.SPAM_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                spam_count += 1
        
        if spam_count >= 2:  # Multiple spam indicators
            flags.append(ContentCategory.SPAM)
            reasons.append("Appears to be spam")
            risk_score += 30
        
        # Check for profanity
        profanity_count = 0
        for pattern in ContentFilter.PROFANITY_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                profanity_count += 1
        
        if profanity_count > 0:
            flags.append(ContentCategory.PROFANITY)
            reasons.append(f"Contains profanity ({profanity_count} instances)")
            risk_score += min(profanity_count * 5, 20)  # Cap at 20
        
        # Check for PII
        filtered_text = text
        pii_found = False
        for pattern in ContentFilter.PII_PATTERNS:
            if re.search(pattern, text):
                pii_found = True
                # Redact PII
                filtered_text = re.sub(pattern, '[REDACTED]', filtered_text)
        
        if pii_found:
            flags.append(ContentCategory.PERSONAL_INFO)
            reasons.append("Contains personal information (redacted)")
            risk_score += 15
        
        # Check for scams
        for pattern in ContentFilter.SCAM_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                flags.append(ContentCategory.SCAM)
                reasons.append("Appears to be a scam")
                risk_score += 35
                break
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = ContentRiskLevel.CRITICAL
        elif risk_score >= 35:
            risk_level = ContentRiskLevel.HIGH
        elif risk_score >= 20:
            risk_level = ContentRiskLevel.MEDIUM
        elif risk_score >= 10:
            risk_level = ContentRiskLevel.LOW
        else:
            risk_level = ContentRiskLevel.SAFE
        
        is_safe = risk_level in [ContentRiskLevel.SAFE, ContentRiskLevel.LOW]
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'is_safe': is_safe,
            'flags': flags,
            'reasons': reasons,
            'filtered_text': filtered_text,
        }
    
    @staticmethod
    def is_safe_for_generation(text: str) -> Tuple[bool, Optional[str]]:
        """
        Quick check if content is safe for generation.
        
        Args:
            text: Content to check
            
        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        result = ContentFilter.moderate_content(text)
        
        if not result['is_safe']:
            reason = "; ".join(result['reasons'])
            return False, reason
        
        return True, None
    
    @staticmethod
    def filter_profanity(text: str, replacement: str = "***") -> str:
        """
        Replace profanity with replacement string.
        
        Args:
            text: Text to filter
            replacement: Replacement string
            
        Returns:
            Filtered text
        """
        filtered = text
        for pattern in ContentFilter.PROFANITY_PATTERNS:
            filtered = re.sub(pattern, replacement, filtered, flags=re.IGNORECASE)
        return filtered
    
    @staticmethod
    def remove_pii(text: str) -> str:
        """
        Remove personally identifiable information.
        
        Args:
            text: Text to filter
            
        Returns:
            Text with PII removed
        """
        filtered = text
        for pattern in ContentFilter.PII_PATTERNS:
            filtered = re.sub(pattern, '[REDACTED]', filtered)
        return filtered
    
    @staticmethod
    def check_spam_score(text: str) -> int:
        """
        Calculate spam score (0-100).
        
        Args:
            text: Text to check
            
        Returns:
            Spam score (higher = more likely spam)
        """
        score = 0
        text_lower = text.lower()
        
        # Check spam patterns
        for pattern in ContentFilter.SPAM_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 15
        
        # Check for excessive capitalization
        if text.isupper() and len(text) > 20:
            score += 20
        
        # Check for excessive exclamation marks
        exclamation_count = text.count('!')
        if exclamation_count > 3:
            score += min(exclamation_count * 5, 25)
        
        # Check for excessive URLs
        url_count = len(re.findall(r'https?://', text_lower))
        if url_count > 2:
            score += min(url_count * 10, 30)
        
        return min(score, 100)


# Convenience functions
def moderate_content(text: str) -> Dict[str, any]:
    """Moderate content and return risk assessment"""
    return ContentFilter.moderate_content(text)


def is_safe_for_generation(text: str) -> Tuple[bool, Optional[str]]:
    """Check if content is safe for generation"""
    return ContentFilter.is_safe_for_generation(text)


def filter_profanity(text: str, replacement: str = "***") -> str:
    """Filter profanity from text"""
    return ContentFilter.filter_profanity(text, replacement)


def remove_pii(text: str) -> str:
    """Remove PII from text"""
    return ContentFilter.remove_pii(text)


def check_spam_score(text: str) -> int:
    """Calculate spam score"""
    return ContentFilter.check_spam_score(text)
