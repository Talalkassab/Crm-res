from celery import Celery
from celery.exceptions import MaxRetriesExceededError
import logging
import json
from typing import Dict, Any
from src.utils.config import config

logger = logging.getLogger(__name__)

celery_app = Celery(
    'whatsapp_gateway',
    broker=config.REDIS_URL,
    backend=config.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=1,
    task_max_retries=3,
    task_default_retry_kwargs={'countdown': 1, 'backoff': True, 'backoff_base': 2}
)

@celery_app.task(bind=True, max_retries=3)
def process_incoming_message(self, message_data: Dict[str, Any]):
    try:
        logger.info(f"Processing message: {message_data.get('id')}")
        
        from src.handlers.echo import EchoHandler
        from src.services.database import database_service
        import asyncio
        
        handler = EchoHandler()
        
        loop = asyncio.get_event_loop()
        
        from_number = message_data.get('from')
        conversation_result = loop.run_until_complete(
            database_service.get_or_create_conversation(from_number)
        )
        
        if conversation_result.get('success'):
            loop.run_until_complete(
                database_service.store_message(
                    conversation_result['conversation_id'],
                    message_data,
                    sender='customer'
                )
            )
            
            loop.run_until_complete(
                database_service.update_customer_interaction(from_number)
            )
        
        result = loop.run_until_complete(handler.handle_message(message_data))
        
        logger.info(f"Message processed: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        try:
            self.retry(countdown=2 ** self.request.retries)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for message: {message_data.get('id')}")
            send_to_dead_letter_queue.delay(message_data)
            raise

@celery_app.task
def send_to_dead_letter_queue(message_data: Dict[str, Any]):
    logger.error(f"Message sent to DLQ: {message_data.get('id')}")
    
@celery_app.task(bind=True, max_retries=3)
def process_status_update(self, status_data: Dict[str, Any]):
    try:
        logger.info(f"Processing status update: {status_data.get('id')} -> {status_data.get('status')}")
        
        from src.services.database import database_service
        import asyncio
        
        loop = asyncio.get_event_loop()
        
        result = loop.run_until_complete(
            database_service.update_message_status(
                status_data.get('id'),
                status_data.get('status'),
                status_data.get('recipient_id')
            )
        )
        
        return {
            'status': 'processed',
            'message_id': status_data.get('id'),
            'delivery_status': status_data.get('status'),
            'database_update': result.get('success', False)
        }
        
    except Exception as e:
        logger.error(f"Error processing status update: {str(e)}")
        try:
            self.retry(countdown=2 ** self.request.retries)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for status: {status_data.get('id')}")
            raise

def get_queue_health():
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        reserved = inspect.reserved()
        
        return {
            'status': 'healthy' if stats else 'unhealthy',
            'stats': stats,
            'active_tasks': active,
            'reserved_tasks': reserved
        }
    except Exception as e:
        logger.error(f"Error getting queue health: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }