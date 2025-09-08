"""
Comprehensive Input Sanitization Utility
Prevents XSS, injection attacks, and ensures data integrity
"""

import re
import html
import bleach
from typing import Any, Dict, List, Optional, Union
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class SanitizationConfig:
    """Configuration for input sanitization"""
    # HTML sanitization
    allowed_tags: List[str] = None
    allowed_attributes: Dict[str, List[str]] = None
    strip_comments: bool = True
    strip_unknown_tags: bool = True
    
    # String sanitization
    max_length: Optional[int] = None
    trim_whitespace: bool = True
    normalize_unicode: bool = True
    
    # Security options
    prevent_xss: bool = True
    prevent_sql_injection: bool = True
    prevent_command_injection: bool = True
    
    def __post_init__(self):
        if self.allowed_tags is None:
            self.allowed_tags = ['p', 'br', 'strong', 'em', 'u']
        
        if self.allowed_attributes is None:
            self.allowed_attributes = {
                '*': ['class'],
                'a': ['href', 'title'],
            }

class InputSanitizer:
    """
    Comprehensive input sanitization utility
    """
    
    # Patterns for detecting potential attacks
    XSS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'<iframe[^>]*>', re.IGNORECASE),
        re.compile(r'<object[^>]*>', re.IGNORECASE),
        re.compile(r'<embed[^>]*>', re.IGNORECASE),
        re.compile(r'vbscript:', re.IGNORECASE),
        re.compile(r'data:text/html', re.IGNORECASE),
    ]
    
    SQL_INJECTION_PATTERNS = [
        re.compile(r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)", re.IGNORECASE),
        re.compile(r"[';\"]\s*;\s*", re.IGNORECASE),
        re.compile(r"--", re.IGNORECASE),
        re.compile(r"/\*.*?\*/", re.IGNORECASE | re.DOTALL),
        re.compile(r"\bOR\s+\d+\s*=\s*\d+", re.IGNORECASE),
        re.compile(r"\bAND\s+\d+\s*=\s*\d+", re.IGNORECASE),
        re.compile(r"'\s*OR\s*'.*?'\s*=\s*'", re.IGNORECASE),
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        re.compile(r'[;&|`$<>]'),
        re.compile(r'\$\(.*?\)', re.IGNORECASE),
        re.compile(r'`.*?`', re.IGNORECASE),
        re.compile(r'\|\|\s*\w+', re.IGNORECASE),
        re.compile(r'&&\s*\w+', re.IGNORECASE),
    ]
    
    # Safe character patterns
    SAFE_FILENAME = re.compile(r'^[a-zA-Z0-9._-]+$')
    SAFE_IDENTIFIER = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    SAFE_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def __init__(self):
        # Default configurations for different contexts
        self.configs = {
            'strict': SanitizationConfig(
                allowed_tags=[],
                allowed_attributes={},
                max_length=1000,
                prevent_xss=True,
                prevent_sql_injection=True,
                prevent_command_injection=True
            ),
            'basic': SanitizationConfig(
                allowed_tags=['p', 'br', 'strong', 'em'],
                allowed_attributes={'*': []},
                max_length=5000,
                prevent_xss=True,
                prevent_sql_injection=True,
                prevent_command_injection=True
            ),
            'rich_text': SanitizationConfig(
                allowed_tags=['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'ul', 'ol', 'li'],
                allowed_attributes={
                    '*': ['class'],
                    'a': ['href', 'title']
                },
                max_length=10000,
                prevent_xss=True,
                prevent_sql_injection=True,
                prevent_command_injection=False  # More permissive for rich text
            )
        }
    
    def sanitize_string(
        self,
        input_str: str,
        config: Union[str, SanitizationConfig] = 'basic',
        context: str = 'general'
    ) -> str:
        """
        Sanitize a string input based on configuration
        """
        if not isinstance(input_str, str):
            input_str = str(input_str)
        
        # Get configuration
        if isinstance(config, str):
            config = self.configs.get(config, self.configs['basic'])
        
        # Trim whitespace
        if config.trim_whitespace:
            input_str = input_str.strip()
        
        # Normalize unicode
        if config.normalize_unicode:
            input_str = input_str.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Length restriction
        if config.max_length and len(input_str) > config.max_length:
            logger.warning(f"Input truncated from {len(input_str)} to {config.max_length} characters")
            input_str = input_str[:config.max_length]
        
        # Security checks
        if config.prevent_xss:
            input_str = self._sanitize_xss(input_str, config)
        
        if config.prevent_sql_injection:
            input_str = self._sanitize_sql_injection(input_str)
        
        if config.prevent_command_injection:
            input_str = self._sanitize_command_injection(input_str)
        
        # HTML sanitization
        if config.allowed_tags is not None:
            input_str = self._sanitize_html(input_str, config)
        
        return input_str
    
    def _sanitize_xss(self, input_str: str, config: SanitizationConfig) -> str:
        """Remove XSS attack vectors"""
        # Remove dangerous patterns
        for pattern in self.XSS_PATTERNS:
            input_str = pattern.sub('', input_str)
        
        # HTML escape if no HTML allowed
        if not config.allowed_tags:
            input_str = html.escape(input_str)
        
        # URL encode dangerous characters in URLs
        if 'http' in input_str.lower():
            input_str = self._sanitize_urls(input_str)
        
        return input_str
    
    def _sanitize_sql_injection(self, input_str: str) -> str:
        """Remove SQL injection attack vectors"""
        original_length = len(input_str)
        
        for pattern in self.SQL_INJECTION_PATTERNS:
            matches = pattern.findall(input_str)
            if matches:
                logger.warning(f"Potential SQL injection detected: {matches}")
                input_str = pattern.sub(' ', input_str)
        
        if len(input_str) != original_length:
            logger.warning("Input modified due to SQL injection patterns")
        
        return input_str
    
    def _sanitize_command_injection(self, input_str: str) -> str:
        """Remove command injection attack vectors"""
        original_length = len(input_str)
        
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if pattern.search(input_str):
                logger.warning(f"Potential command injection detected in: {input_str[:100]}")
                input_str = pattern.sub('', input_str)
        
        if len(input_str) != original_length:
            logger.warning("Input modified due to command injection patterns")
        
        return input_str
    
    def _sanitize_html(self, input_str: str, config: SanitizationConfig) -> str:
        """Sanitize HTML content"""
        return bleach.clean(
            input_str,
            tags=config.allowed_tags,
            attributes=config.allowed_attributes,
            strip=config.strip_unknown_tags,
            strip_comments=config.strip_comments
        )
    
    def _sanitize_urls(self, input_str: str) -> str:
        """Sanitize URLs within text"""
        # Find URLs and validate them
        url_pattern = re.compile(r'https?://[^\s]+')
        
        def sanitize_url(match):
            url = match.group(0)
            try:
                parsed = urllib.parse.urlparse(url)
                # Only allow http/https schemes
                if parsed.scheme.lower() not in ['http', 'https']:
                    return '[URL_REMOVED]'
                
                # Encode the URL properly
                safe_url = urllib.parse.urlunparse(parsed)
                return safe_url
            except Exception:
                return '[INVALID_URL_REMOVED]'
        
        return url_pattern.sub(sanitize_url, input_str)
    
    def sanitize_dict(
        self,
        input_dict: Dict[str, Any],
        field_configs: Optional[Dict[str, Union[str, SanitizationConfig]]] = None
    ) -> Dict[str, Any]:
        """
        Sanitize all string values in a dictionary
        """
        if field_configs is None:
            field_configs = {}
        
        sanitized = {}
        
        for key, value in input_dict.items():
            # Sanitize the key itself
            safe_key = self.sanitize_string(key, 'strict', 'field_name')
            
            # Get config for this field
            field_config = field_configs.get(key, 'basic')
            
            if isinstance(value, str):
                sanitized[safe_key] = self.sanitize_string(value, field_config)
            elif isinstance(value, dict):
                sanitized[safe_key] = self.sanitize_dict(value, field_configs.get(key, {}))
            elif isinstance(value, list):
                sanitized[safe_key] = self.sanitize_list(value, field_config)
            else:
                # For non-string types, keep as-is but validate
                sanitized[safe_key] = self._sanitize_primitive(value)
        
        return sanitized
    
    def sanitize_list(
        self,
        input_list: List[Any],
        config: Union[str, SanitizationConfig] = 'basic'
    ) -> List[Any]:
        """Sanitize all items in a list"""
        sanitized = []
        
        for item in input_list:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item, config))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item, config))
            else:
                sanitized.append(self._sanitize_primitive(item))
        
        return sanitized
    
    def _sanitize_primitive(self, value: Any) -> Any:
        """Sanitize primitive values (int, float, bool, etc.)"""
        # Basic type validation and conversion
        if isinstance(value, (int, float, bool, type(None))):
            return value
        
        if isinstance(value, datetime):
            return value
        
        # Convert unknown types to string and sanitize
        return self.sanitize_string(str(value), 'strict')
    
    def validate_safe_identifier(self, identifier: str) -> bool:
        """Validate that a string is a safe identifier"""
        return bool(self.SAFE_IDENTIFIER.match(identifier))
    
    def validate_safe_filename(self, filename: str) -> bool:
        """Validate that a string is a safe filename"""
        return bool(self.SAFE_FILENAME.match(filename))
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        return bool(self.SAFE_EMAIL.match(email))
    
    def sanitize_for_database(self, input_str: str) -> str:
        """Sanitize input specifically for database storage"""
        return self.sanitize_string(
            input_str,
            SanitizationConfig(
                allowed_tags=[],
                max_length=65535,  # TEXT column limit
                prevent_xss=True,
                prevent_sql_injection=True,
                prevent_command_injection=True
            )
        )
    
    def sanitize_for_display(self, input_str: str) -> str:
        """Sanitize input for safe display in web interfaces"""
        return self.sanitize_string(input_str, 'basic')
    
    def sanitize_for_logging(self, input_str: str) -> str:
        """Sanitize input for safe logging"""
        # More restrictive for logs to prevent log injection
        sanitized = self.sanitize_string(input_str, 'strict')
        
        # Remove line breaks and control characters for logs
        sanitized = re.sub(r'[\r\n\t\x00-\x1f\x7f-\x9f]', ' ', sanitized)
        
        # Truncate for logs
        if len(sanitized) > 500:
            sanitized = sanitized[:497] + '...'
        
        return sanitized
    
    def get_sanitization_report(
        self,
        original: str,
        sanitized: str
    ) -> Dict[str, Any]:
        """Generate a report of what was changed during sanitization"""
        return {
            'original_length': len(original),
            'sanitized_length': len(sanitized),
            'was_modified': original != sanitized,
            'length_changed': len(original) != len(sanitized),
            'contains_html': bool(re.search(r'<[^>]+>', original)),
            'contains_urls': bool(re.search(r'https?://', original)),
            'potential_xss': any(pattern.search(original) for pattern in self.XSS_PATTERNS),
            'potential_sql_injection': any(pattern.search(original) for pattern in self.SQL_INJECTION_PATTERNS),
            'potential_command_injection': any(pattern.search(original) for pattern in self.COMMAND_INJECTION_PATTERNS),
        }

# Global sanitizer instance
sanitizer = InputSanitizer()

# Convenience functions
def sanitize_string(input_str: str, config: str = 'basic') -> str:
    """Convenience function for string sanitization"""
    return sanitizer.sanitize_string(input_str, config)

def sanitize_dict(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for dictionary sanitization"""
    return sanitizer.sanitize_dict(input_dict)

def sanitize_for_db(input_str: str) -> str:
    """Convenience function for database sanitization"""
    return sanitizer.sanitize_for_database(input_str)

def sanitize_for_display(input_str: str) -> str:
    """Convenience function for display sanitization"""
    return sanitizer.sanitize_for_display(input_str)