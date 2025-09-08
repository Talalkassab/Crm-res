"""
FastAPI middleware and dependencies for automatic input sanitization
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any, Optional
import json
import logging

from ..utils.input_sanitizer import sanitizer, SanitizationConfig

logger = logging.getLogger(__name__)

class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically sanitize request inputs
    """
    
    def __init__(self, app, sanitize_query_params: bool = True, sanitize_form_data: bool = True):
        super().__init__(app)
        self.sanitize_query_params = sanitize_query_params
        self.sanitize_form_data = sanitize_form_data
        
        # Configure sanitization for different endpoints
        self.endpoint_configs = {
            # Campaign endpoints - allow some HTML for descriptions
            '/api/feedback-campaigns': {
                'name': 'basic',
                'description': 'rich_text',
                'default': 'basic'
            },
            
            # Upload endpoints - strict sanitization
            '/api/feedback-campaigns/upload': {
                'campaign_name': 'basic',
                'default': 'strict'
            },
            
            # Customer endpoints - basic sanitization
            '/api/customers': {
                'name': 'basic',
                'notes': 'basic',
                'default': 'strict'
            },
            
            # Message endpoints - allow rich text
            '/api/conversations': {
                'content': 'rich_text',
                'title': 'basic',
                'default': 'basic'
            },
            
            # Default config for other endpoints
            'default': {
                'default': 'basic'
            }
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and sanitize inputs"""
        
        # Skip sanitization for certain content types and paths
        if self._should_skip_sanitization(request):
            response = await call_next(request)
            return response
        
        try:
            # Sanitize query parameters
            if self.sanitize_query_params and request.query_params:
                sanitized_params = self._sanitize_query_params(request)
                # Replace query params with sanitized versions
                request._query_params = sanitized_params
            
            # For POST/PUT/PATCH requests, sanitize body
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._sanitize_request_body(request)
            
        except Exception as e:
            logger.error(f"Input sanitization error: {e}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid input data format"}
            )
        
        response = await call_next(request)
        return response
    
    def _should_skip_sanitization(self, request: Request) -> bool:
        """Determine if sanitization should be skipped for this request"""
        
        # Skip for file uploads (handled separately)
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            return True
        
        # Skip for health checks and documentation
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json", "/favicon.ico"]
        if request.url.path in skip_paths:
            return True
        
        # Skip for GET requests (only query params need sanitization)
        if request.method == "GET":
            return False
        
        return False
    
    def _sanitize_query_params(self, request: Request) -> Dict[str, str]:
        """Sanitize query parameters"""
        sanitized = {}
        
        for key, value in request.query_params.items():
            # Sanitize parameter name
            safe_key = sanitizer.sanitize_string(key, 'strict')
            
            # Sanitize parameter value
            safe_value = sanitizer.sanitize_string(value, 'basic')
            
            sanitized[safe_key] = safe_value
        
        return sanitized
    
    async def _sanitize_request_body(self, request: Request):
        """Sanitize request body data"""
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            await self._sanitize_json_body(request)
        elif "application/x-www-form-urlencoded" in content_type:
            await self._sanitize_form_body(request)
    
    async def _sanitize_json_body(self, request: Request):
        """Sanitize JSON request body"""
        try:
            # Read the body
            body = await request.body()
            if not body:
                return
            
            # Parse JSON
            data = json.loads(body)
            
            # Get sanitization config for this endpoint
            endpoint_config = self._get_endpoint_config(request.url.path)
            
            # Sanitize the data
            sanitized_data = self._sanitize_data_with_config(data, endpoint_config)
            
            # Replace the body with sanitized data
            sanitized_body = json.dumps(sanitized_data).encode('utf-8')
            
            # Monkey patch the body (FastAPI internal mechanism)
            async def receive():
                return {"type": "http.request", "body": sanitized_body}
            
            request._receive = receive
            
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        except Exception as e:
            logger.error(f"JSON sanitization error: {e}")
            raise HTTPException(status_code=400, detail="Error processing request data")
    
    async def _sanitize_form_body(self, request: Request):
        """Sanitize form data request body"""
        # This would be more complex - for now, we'll handle it in the endpoint
        pass
    
    def _get_endpoint_config(self, path: str) -> Dict[str, str]:
        """Get sanitization configuration for endpoint"""
        # Try exact match first
        if path in self.endpoint_configs:
            return self.endpoint_configs[path]
        
        # Try prefix matching
        for endpoint_prefix, config in self.endpoint_configs.items():
            if endpoint_prefix != 'default' and path.startswith(endpoint_prefix):
                return config
        
        # Return default config
        return self.endpoint_configs['default']
    
    def _sanitize_data_with_config(
        self,
        data: Any,
        config: Dict[str, str]
    ) -> Any:
        """Sanitize data using field-specific configuration"""
        if isinstance(data, dict):
            sanitized = {}
            default_config = config.get('default', 'basic')
            
            for key, value in data.items():
                # Get config for this field
                field_config = config.get(key, default_config)
                
                # Sanitize key
                safe_key = sanitizer.sanitize_string(key, 'strict')
                
                # Sanitize value recursively
                if isinstance(value, str):
                    sanitized[safe_key] = sanitizer.sanitize_string(value, field_config)
                elif isinstance(value, dict):
                    sanitized[safe_key] = self._sanitize_data_with_config(value, config)
                elif isinstance(value, list):
                    sanitized[safe_key] = [
                        self._sanitize_data_with_config(item, config) 
                        for item in value
                    ]
                else:
                    sanitized[safe_key] = value
            
            return sanitized
        
        elif isinstance(data, list):
            return [self._sanitize_data_with_config(item, config) for item in data]
        
        elif isinstance(data, str):
            default_config = config.get('default', 'basic')
            return sanitizer.sanitize_string(data, default_config)
        
        else:
            return data

# Dependencies for specific sanitization needs
def sanitize_campaign_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Dependency for sanitizing campaign input"""
    config = {
        'name': 'basic',
        'description': 'rich_text',
        'notes': 'basic',
        'default': 'strict'
    }
    
    field_configs = {}
    for field, sanitization_type in config.items():
        if field != 'default':
            field_configs[field] = sanitization_type
    
    return sanitizer.sanitize_dict(data, field_configs)

def sanitize_customer_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Dependency for sanitizing customer input"""
    config = {
        'name': 'basic',
        'email': 'strict',
        'phone': 'strict',
        'notes': 'basic',
        'default': 'strict'
    }
    
    field_configs = {}
    for field, sanitization_type in config.items():
        if field != 'default':
            field_configs[field] = sanitization_type
    
    return sanitizer.sanitize_dict(data, field_configs)

def sanitize_message_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Dependency for sanitizing message input"""
    config = {
        'content': 'rich_text',
        'title': 'basic',
        'subject': 'basic',
        'default': 'basic'
    }
    
    field_configs = {}
    for field, sanitization_type in config.items():
        if field != 'default':
            field_configs[field] = sanitization_type
    
    return sanitizer.sanitize_dict(data, field_configs)

# Validation functions
def validate_campaign_name(name: str) -> str:
    """Validate and sanitize campaign name"""
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Campaign name is required")
    
    sanitized = sanitizer.sanitize_string(name, 'basic')
    
    if len(sanitized) > 255:
        raise HTTPException(status_code=400, detail="Campaign name too long")
    
    if len(sanitized.strip()) < 3:
        raise HTTPException(status_code=400, detail="Campaign name too short")
    
    return sanitized

def validate_phone_number(phone: str) -> str:
    """Validate and sanitize phone number"""
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required")
    
    # Remove all non-digit and non-plus characters
    sanitized = re.sub(r'[^\d+]', '', phone)
    
    if not sanitized:
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    return sanitized

def validate_email(email: str) -> str:
    """Validate and sanitize email"""
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    sanitized = sanitizer.sanitize_string(email, 'strict').lower()
    
    if not sanitizer.validate_email(sanitized):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    return sanitized