import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.services.whatsapp_client import WhatsAppClient

logger = logging.getLogger(__name__)

class EchoHandler:
    def __init__(self):
        self.client = WhatsAppClient()
    
    async def handle_text_message(self, from_number: str, text: str, message_id: str) -> Dict[str, Any]:
        timestamp = datetime.utcnow().isoformat()
        response_text = f"Message received at {timestamp}: {text}"
        
        logger.info(f"Echoing text message from {from_number}")
        
        result = await self.client.send_text_message(
            to=from_number,
            text=response_text
        )
        
        return {
            'type': 'echo_response',
            'original_message_id': message_id,
            'response_sent': result.get('success', False),
            'timestamp': timestamp
        }
    
    async def handle_media_message(
        self, 
        from_number: str, 
        media_type: str, 
        media_id: str, 
        caption: Optional[str], 
        message_id: str
    ) -> Dict[str, Any]:
        timestamp = datetime.utcnow().isoformat()
        caption_text = f" with caption: {caption}" if caption else ""
        response_text = f"Media ({media_type}) received at {timestamp}{caption_text}"
        
        logger.info(f"Echoing media message from {from_number}: {media_type}")
        
        result = await self.client.send_text_message(
            to=from_number,
            text=response_text
        )
        
        return {
            'type': 'echo_response',
            'original_message_id': message_id,
            'media_type': media_type,
            'media_id': media_id,
            'response_sent': result.get('success', False),
            'timestamp': timestamp
        }
    
    async def handle_interactive_message(
        self, 
        from_number: str, 
        interactive_type: str, 
        interactive_data: Dict[str, Any], 
        message_id: str
    ) -> Dict[str, Any]:
        timestamp = datetime.utcnow().isoformat()
        
        if interactive_type == 'button_reply':
            button_id = interactive_data.get('button_reply', {}).get('id')
            button_title = interactive_data.get('button_reply', {}).get('title')
            response_text = f"Button pressed at {timestamp}: {button_title} (ID: {button_id})"
        elif interactive_type == 'list_reply':
            list_id = interactive_data.get('list_reply', {}).get('id')
            list_title = interactive_data.get('list_reply', {}).get('title')
            response_text = f"List item selected at {timestamp}: {list_title} (ID: {list_id})"
        else:
            response_text = f"Interactive message ({interactive_type}) received at {timestamp}"
        
        logger.info(f"Echoing interactive message from {from_number}: {interactive_type}")
        
        result = await self.client.send_text_message(
            to=from_number,
            text=response_text
        )
        
        return {
            'type': 'echo_response',
            'original_message_id': message_id,
            'interactive_type': interactive_type,
            'response_sent': result.get('success', False),
            'timestamp': timestamp
        }
    
    async def handle_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from_number = message_data.get('from')
            message_type = message_data.get('type')
            message_id = message_data.get('id')
            
            if not from_number or not message_type:
                logger.error(f"Invalid message data: missing from or type")
                return {'error': 'Invalid message data'}
            
            if message_type == 'text':
                text = message_data.get('text', {}).get('body', '')
                return await self.handle_text_message(from_number, text, message_id)
            
            elif message_type in ['image', 'video', 'audio', 'document']:
                media_data = message_data.get(message_type, {})
                media_id = media_data.get('id')
                caption = media_data.get('caption')
                return await self.handle_media_message(
                    from_number, message_type, media_id, caption, message_id
                )
            
            elif message_type == 'interactive':
                interactive_data = message_data.get('interactive', {})
                interactive_type = interactive_data.get('type')
                return await self.handle_interactive_message(
                    from_number, interactive_type, interactive_data, message_id
                )
            
            else:
                logger.warning(f"Unsupported message type: {message_type}")
                response_text = f"Message type '{message_type}' received but not yet supported"
                
                result = await self.client.send_text_message(
                    to=from_number,
                    text=response_text
                )
                
                return {
                    'type': 'echo_response',
                    'original_message_id': message_id,
                    'unsupported_type': message_type,
                    'response_sent': result.get('success', False)
                }
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return {
                'error': str(e),
                'message_id': message_data.get('id')
            }