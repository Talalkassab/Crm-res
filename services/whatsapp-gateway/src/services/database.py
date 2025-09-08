import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseService:
    def __init__(self):
        self.supabase: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_ANON_KEY
        )
    
    async def update_customer_interaction(
        self,
        whatsapp_number: str,
        restaurant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            result = self.supabase.table('customers').update({
                'last_interaction': datetime.utcnow().isoformat(),
                'whatsapp_number': whatsapp_number
            }).eq('whatsapp_number', whatsapp_number).execute()
            
            if not result.data:
                result = self.supabase.table('customers').insert({
                    'id': str(uuid.uuid4()),
                    'whatsapp_number': whatsapp_number,
                    'restaurant_id': restaurant_id,
                    'last_interaction': datetime.utcnow().isoformat(),
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
            
            logger.info(f"Customer interaction updated for {whatsapp_number}")
            return {"success": True, "customer": result.data[0] if result.data else None}
            
        except Exception as e:
            logger.error(f"Error updating customer interaction: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def store_message(
        self,
        conversation_id: str,
        message_data: Dict[str, Any],
        sender: str = "customer",
        status: str = "received"
    ) -> Dict[str, Any]:
        try:
            message_entry = {
                "id": str(uuid.uuid4()),
                "sender": sender,
                "content": message_data.get("text", {}).get("body", "") if message_data.get("type") == "text" else f"[{message_data.get('type')} message]",
                "timestamp": datetime.utcnow().isoformat(),
                "whatsapp_message_id": message_data.get("id"),
                "status": status,
                "message_type": message_data.get("type"),
                "raw_data": message_data
            }
            
            conversation = self.supabase.table('conversations').select('messages').eq('id', conversation_id).execute()
            
            if conversation.data:
                existing_messages = conversation.data[0].get('messages', [])
                existing_messages.append(message_entry)
                
                result = self.supabase.table('conversations').update({
                    'messages': existing_messages,
                    'last_message_at': datetime.utcnow().isoformat(),
                    'status': 'active'
                }).eq('id', conversation_id).execute()
            else:
                result = self.supabase.table('conversations').insert({
                    'id': conversation_id,
                    'messages': [message_entry],
                    'status': 'active',
                    'last_message_at': datetime.utcnow().isoformat(),
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
            
            logger.info(f"Message stored in conversation {conversation_id}")
            return {"success": True, "message_id": message_entry["id"]}
            
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_message_status(
        self,
        whatsapp_message_id: str,
        status: str,
        recipient_id: str
    ) -> Dict[str, Any]:
        try:
            conversations = self.supabase.table('conversations').select('id, messages').execute()
            
            for conv in conversations.data:
                messages = conv.get('messages', [])
                updated = False
                
                for msg in messages:
                    if msg.get('whatsapp_message_id') == whatsapp_message_id:
                        msg['status'] = status
                        msg['status_updated_at'] = datetime.utcnow().isoformat()
                        updated = True
                        break
                
                if updated:
                    result = self.supabase.table('conversations').update({
                        'messages': messages
                    }).eq('id', conv['id']).execute()
                    
                    logger.info(f"Message status updated: {whatsapp_message_id} -> {status}")
                    return {"success": True, "conversation_id": conv['id']}
            
            logger.warning(f"Message not found for status update: {whatsapp_message_id}")
            return {"success": False, "error": "Message not found"}
            
        except Exception as e:
            logger.error(f"Error updating message status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_or_create_conversation(
        self,
        customer_phone: str,
        restaurant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            customer_result = self.supabase.table('customers').select('id').eq('whatsapp_number', customer_phone).execute()
            
            if not customer_result.data:
                customer_insert = self.supabase.table('customers').insert({
                    'id': str(uuid.uuid4()),
                    'whatsapp_number': customer_phone,
                    'restaurant_id': restaurant_id,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
                customer_id = customer_insert.data[0]['id']
            else:
                customer_id = customer_result.data[0]['id']
            
            conversation_result = self.supabase.table('conversations').select('id').eq('customer_id', customer_id).eq('status', 'active').execute()
            
            if not conversation_result.data:
                conversation_id = str(uuid.uuid4())
                self.supabase.table('conversations').insert({
                    'id': conversation_id,
                    'customer_id': customer_id,
                    'restaurant_id': restaurant_id,
                    'status': 'active',
                    'created_at': datetime.utcnow().isoformat(),
                    'messages': []
                }).execute()
            else:
                conversation_id = conversation_result.data[0]['id']
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "customer_id": customer_id
            }
            
        except Exception as e:
            logger.error(f"Error getting/creating conversation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_restaurant_by_phone(self, whatsapp_number: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.supabase.table('restaurants').select('*').eq('whatsapp_number', whatsapp_number).execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting restaurant by phone: {str(e)}")
            return None
    
    async def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        try:
            self.supabase.table('error_logs').insert({
                'id': str(uuid.uuid4()),
                'error_type': error_type,
                'error_message': error_message,
                'context': context,
                'correlation_id': correlation_id or str(uuid.uuid4()),
                'service': 'whatsapp-gateway',
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Error logging to database: {str(e)}")

database_service = DatabaseService()