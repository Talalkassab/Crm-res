import httpx
import logging
from typing import Dict, Any, Optional, List
from src.utils.config import config
from src.models.whatsapp import WhatsAppOutboundMessage
from src.middleware.rate_limiter import rate_limiter_instance
from src.utils.error_handler import error_handler, webhook_circuit_breaker
from src.utils.logger import get_logger

logger = get_logger(__name__)

class WhatsAppClient:
    def __init__(self):
        self.base_url = config.whatsapp_api_url
        self.access_token = config.WHATSAPP_ACCESS_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_text_message(self, to: str, text: str, is_user_initiated: bool = True) -> Dict[str, Any]:
        try:
            await rate_limiter_instance.wait_if_needed(to, is_user_initiated)
            
            message = WhatsAppOutboundMessage(
                to=to,
                type="text",
                text={"body": text}
            )
            
            async def _send():
                return await self.client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=message.model_dump(exclude_none=True)
                )
            
            response = await webhook_circuit_breaker.call(_send)
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Text message sent to {to}: {result.get('messages', [{}])[0].get('id')}")
            
            return {
                "success": True,
                "message_id": result.get("messages", [{}])[0].get("id"),
                "to": to
            }
            
        except httpx.HTTPStatusError as e:
            error_details = {
                "status_code": e.response.status_code,
                "response": e.response.text
            }
            logger.error(f"HTTP error sending message to {to}: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}",
                "details": error_details
            }
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error sending message to {to}: {str(e)}")
            return {
                "success": False,
                "error": "REQUEST_TIMEOUT",
                "details": {"timeout": "30s"}
            }
        except httpx.ConnectError as e:
            logger.error(f"Connection error sending message to {to}: {str(e)}")
            return {
                "success": False,
                "error": "CONNECTION_ERROR",
                "details": {"message": str(e)}
            }
        except Exception as e:
            logger.error(f"Unexpected error sending message to {to}: {str(e)}")
            return {
                "success": False,
                "error": "UNEXPECTED_ERROR",
                "details": {"message": str(e)}
            }
    
    async def send_template_message(
        self, 
        to: str, 
        template_name: str, 
        language_code: str = "en",
        components: Optional[List[Dict[str, Any]]] = None,
        is_user_initiated: bool = False
    ) -> Dict[str, Any]:
        try:
            await rate_limiter_instance.wait_if_needed(to, is_user_initiated)
            message = WhatsAppOutboundMessage(
                to=to,
                type="template",
                template={
                    "name": template_name,
                    "language": {"code": language_code},
                    "components": components or []
                }
            )
            
            response = await self.client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=message.model_dump(exclude_none=True)
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Template message '{template_name}' sent to {to}: {result.get('messages', [{}])[0].get('id')}")
            
            return {
                "success": True,
                "message_id": result.get("messages", [{}])[0].get("id"),
                "to": to,
                "template": template_name
            }
            
        except httpx.HTTPStatusError as e:
            error_details = {
                "status_code": e.response.status_code,
                "response": e.response.text,
                "template": template_name
            }
            logger.error(f"HTTP error sending template to {to}: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}",
                "details": error_details
            }
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error sending template to {to}: {str(e)}")
            return {
                "success": False,
                "error": "REQUEST_TIMEOUT",
                "details": {"timeout": "30s", "template": template_name}
            }
        except httpx.ConnectError as e:
            logger.error(f"Connection error sending template to {to}: {str(e)}")
            return {
                "success": False,
                "error": "CONNECTION_ERROR",
                "details": {"message": str(e), "template": template_name}
            }
        except Exception as e:
            logger.error(f"Unexpected error sending template to {to}: {str(e)}")
            return {
                "success": False,
                "error": "UNEXPECTED_ERROR",
                "details": {"message": str(e), "template": template_name}
            }
    
    async def send_feedback_request(
        self, 
        to: str, 
        restaurant_name: str,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        components = []
        
        if order_id:
            components.append({
                "type": "body",
                "parameters": [
                    {"type": "text", "text": restaurant_name},
                    {"type": "text", "text": order_id}
                ]
            })
        else:
            components.append({
                "type": "body",
                "parameters": [
                    {"type": "text", "text": restaurant_name}
                ]
            })
        
        return await self.send_template_message(
            to=to,
            template_name="feedback_request",
            language_code="en",
            components=components
        )
    
    async def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        try:
            response = await self.client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json={
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id
                }
            )
            
            response.raise_for_status()
            
            logger.info(f"Message {message_id} marked as read")
            
            return {
                "success": True,
                "message_id": message_id
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error marking message as read: {e.response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_media_url(self, media_id: str) -> Optional[str]:
        try:
            response = await self.client.get(
                f"https://graph.facebook.com/{config.WHATSAPP_API_VERSION}/{media_id}",
                headers=self.headers
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("url")
            
        except Exception as e:
            logger.error(f"Error getting media URL for {media_id}: {str(e)}")
            return None
    
    async def download_media(self, media_url: str) -> Optional[bytes]:
        try:
            response = await self.client.get(
                media_url,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            response.raise_for_status()
            return response.content
            
        except Exception as e:
            logger.error(f"Error downloading media: {str(e)}")
            return None
    
    async def close(self):
        await self.client.aclose()