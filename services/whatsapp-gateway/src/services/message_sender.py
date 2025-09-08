import asyncio
import logging
from typing import Dict, Any, Optional, List
from src.services.whatsapp_client import WhatsAppClient
from src.services.queue import celery_app

logger = logging.getLogger(__name__)

class MessageSender:
    def __init__(self):
        self.client = WhatsAppClient()
        self.max_retries = 3
        self.retry_delay = 1
    
    async def send_with_retry(
        self, 
        message_type: str,
        to: str,
        content: Dict[str, Any],
        retries: int = 0
    ) -> Dict[str, Any]:
        try:
            if message_type == "text":
                result = await self.client.send_text_message(
                    to=to,
                    text=content.get("text", "")
                )
            elif message_type == "template":
                result = await self.client.send_template_message(
                    to=to,
                    template_name=content.get("template_name"),
                    language_code=content.get("language_code", "en"),
                    components=content.get("components")
                )
            else:
                return {
                    "success": False,
                    "error": f"Unsupported message type: {message_type}"
                }
            
            if result.get("success"):
                return result
            
            if retries < self.max_retries:
                delay = self.retry_delay * (2 ** retries)
                logger.warning(f"Message send failed, retrying in {delay}s (attempt {retries + 1}/{self.max_retries})")
                await asyncio.sleep(delay)
                return await self.send_with_retry(message_type, to, content, retries + 1)
            
            logger.error(f"Max retries exceeded for message to {to}")
            return result
            
        except Exception as e:
            logger.error(f"Error in send_with_retry: {str(e)}")
            
            if retries < self.max_retries:
                delay = self.retry_delay * (2 ** retries)
                await asyncio.sleep(delay)
                return await self.send_with_retry(message_type, to, content, retries + 1)
            
            return {
                "success": False,
                "error": str(e),
                "max_retries_exceeded": True
            }

@celery_app.task(bind=True, max_retries=3)
def send_message_task(self, message_type: str, to: str, content: Dict[str, Any]):
    try:
        import asyncio
        sender = MessageSender()
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            sender.send_with_retry(message_type, to, content)
        )
        
        if not result.get("success"):
            logger.error(f"Failed to send message to {to}: {result}")
            if not result.get("max_retries_exceeded"):
                self.retry(countdown=2 ** self.request.retries)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in send_message_task: {str(e)}")
        self.retry(countdown=2 ** self.request.retries)

@celery_app.task
def send_bulk_messages(messages: List[Dict[str, Any]]):
    results = []
    for message in messages:
        result = send_message_task.delay(
            message_type=message.get("type"),
            to=message.get("to"),
            content=message.get("content")
        )
        results.append({"task_id": result.id, "to": message.get("to")})
    
    return results