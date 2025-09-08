"""
Celery Tasks for Feedback Processing
Handles scheduled sending and metrics updates
"""

from celery import Celery, Task
from datetime import datetime, timedelta
from typing import Dict, Any
import httpx
import json
import asyncio
from uuid import UUID

from ..repositories.campaign_repository import CampaignRepository
from ..services.alert_service import AlertService
import os


# Initialize Celery app
app = Celery(
    'feedback_tasks',
    broker=os.getenv('REDIS_URL', 'redis://redis:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://redis:6379/0')
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


class FeedbackTask(Task):
    """Base task with shared resources"""
    _campaign_repo = None
    _alert_service = None
    
    @property
    def campaign_repo(self):
        if self._campaign_repo is None:
            self._campaign_repo = CampaignRepository()
        return self._campaign_repo
    
    @property
    def alert_service(self):
        if self._alert_service is None:
            self._alert_service = AlertService(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_KEY')
            )
        return self._alert_service


@app.task(base=FeedbackTask, bind=True, name='feedback_tasks.send_feedback_message')
def send_feedback_message(self, message_id: str):
    """
    Send a single feedback request message
    Called by scheduler when message time arrives
    """
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _send_feedback_message_async(self, message_id)
        )
        return result
    except Exception as e:
        # Retry on failure
        raise self.retry(exc=e, countdown=60, max_retries=3)


async def _send_feedback_message_async(task: FeedbackTask, message_id: str):
    """Async implementation of message sending"""
    # Get message details
    message = await task.campaign_repo.get_message(UUID(message_id))
    if not message:
        return {'error': 'Message not found'}
    
    # Check if already sent
    if message['status'] != 'scheduled':
        return {'error': f"Message already {message['status']}"}
    
    # Get campaign details for configuration
    campaign = await task.campaign_repo.get_campaign(
        UUID(message['campaign_id'])
    )
    
    # Prepare WhatsApp message
    whatsapp_payload = {
        'to': message['phone_number'],
        'type': 'template',
        'template': {
            'name': message.get('message_template', 'feedback_request_default'),
            'language': {'code': 'ar'},
            'components': []
        }
    }
    
    # Apply A/B test variant if present
    if message.get('variant_id'):
        variant_config = await _get_variant_config(
            task.campaign_repo,
            campaign['id'],
            message['variant_id']
        )
        if variant_config:
            whatsapp_payload['template']['name'] = variant_config.get(
                'template',
                whatsapp_payload['template']['name']
            )
    
    # Send via WhatsApp API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://whatsapp-gateway:8002/api/messages/send',
                json=whatsapp_payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Update message status
                await task.campaign_repo.update_message_status(
                    UUID(message_id),
                    'sent'
                )
                
                # Update recipient status
                await task.campaign_repo.update_recipient_status(
                    UUID(message['recipient_id']),
                    'sent'
                )
                
                return {
                    'success': True,
                    'message_id': message_id,
                    'whatsapp_id': response.json().get('message_id')
                }
            else:
                return {
                    'error': f"WhatsApp API error: {response.status_code}",
                    'details': response.text
                }
                
    except Exception as e:
        return {'error': f"Failed to send message: {str(e)}"}


@app.task(base=FeedbackTask, bind=True, name='feedback_tasks.send_scheduled_feedback')
def send_scheduled_feedback(self):
    """
    Process scheduled feedback messages
    Runs every 5 minutes to check for messages due to be sent
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(
        _process_scheduled_feedback_async(self)
    )
    return result


async def _process_scheduled_feedback_async(task: FeedbackTask):
    """Process all due scheduled messages"""
    # Get messages scheduled for the next 5 minutes
    cutoff_time = datetime.now() + timedelta(minutes=5)
    
    # Query scheduled messages
    messages = task.campaign_repo.supabase.table('campaign_messages').select('*').eq(
        'status', 'scheduled'
    ).lte('scheduled_send_time', cutoff_time.isoformat()).execute()
    
    if not messages.data:
        return {'processed': 0}
    
    processed_count = 0
    errors = []
    
    for message in messages.data:
        try:
            # Send the message
            result = send_feedback_message.apply_async(
                args=[message['id']],
                eta=datetime.fromisoformat(message['scheduled_send_time'])
            )
            processed_count += 1
            
            # Update status to queued
            await task.campaign_repo.update_message(
                UUID(message['id']),
                {'status': 'queued', 'task_id': result.id}
            )
            
        except Exception as e:
            errors.append({
                'message_id': message['id'],
                'error': str(e)
            })
    
    return {
        'processed': processed_count,
        'errors': errors if errors else None
    }


@app.task(base=FeedbackTask, bind=True, name='feedback_tasks.update_campaign_metrics')
def update_campaign_metrics(self):
    """
    Update metrics for active campaigns
    Runs every 10 minutes
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(
        _update_campaign_metrics_async(self)
    )
    return result


async def _update_campaign_metrics_async(task: FeedbackTask):
    """Update metrics for all active campaigns"""
    # Get active campaigns
    active_campaigns = await task.campaign_repo.list_campaigns(
        filters={'status': 'active'},
        limit=100
    )
    
    updated_count = 0
    
    for campaign in active_campaigns:
        try:
            # Calculate metrics
            metrics = await task.campaign_repo.get_campaign_metrics(
                UUID(campaign['id'])
            )
            
            # Update campaign with latest metrics
            await task.campaign_repo.update_campaign(
                UUID(campaign['id']),
                {'metrics': metrics}
            )
            
            updated_count += 1
            
            # Check if campaign should be marked complete
            if metrics.get('completion_rate', 0) >= 95:
                await task.campaign_repo.update_campaign(
                    UUID(campaign['id']),
                    {'status': 'completed'}
                )
                
        except Exception as e:
            print(f"Error updating metrics for campaign {campaign['id']}: {e}")
    
    return {'updated_campaigns': updated_count}


@app.task(base=FeedbackTask, bind=True, name='feedback_tasks.generate_daily_reports')
def generate_daily_reports(self):
    """
    Generate daily summary reports
    Scheduled to run daily at 6 AM
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(
        _generate_daily_reports_async(self)
    )
    return result


async def _generate_daily_reports_async(task: FeedbackTask):
    """Generate reports for all restaurants with active campaigns"""
    yesterday = datetime.now() - timedelta(days=1)
    
    # Get restaurants with campaigns
    campaigns = await task.campaign_repo.list_campaigns(
        filters={
            'date_range': (yesterday, datetime.now())
        },
        limit=1000
    )
    
    restaurant_ids = list(set(c['restaurant_id'] for c in campaigns if c.get('restaurant_id')))
    reports_generated = 0
    
    for restaurant_id in restaurant_ids:
        try:
            # Call analytics service to generate report
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'http://analytics-service:8003/api/reports/daily-summary',
                    json={
                        'restaurant_id': restaurant_id,
                        'date': yesterday.date().isoformat()
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    reports_generated += 1
                    
        except Exception as e:
            print(f"Error generating report for restaurant {restaurant_id}: {e}")
    
    return {'reports_generated': reports_generated}


@app.task(base=FeedbackTask, bind=True, name='feedback_tasks.process_feedback_response')
def process_feedback_response(self, conversation_id: str, feedback_data: Dict[str, Any]):
    """
    Process a feedback response from a customer
    Triggers alerts if needed
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(
        _process_feedback_response_async(self, conversation_id, feedback_data)
    )
    return result


async def _process_feedback_response_async(
    task: FeedbackTask,
    conversation_id: str,
    feedback_data: Dict[str, Any]
):
    """Process feedback and generate alerts"""
    # Check for alert conditions
    alerts = await task.alert_service.process_feedback_for_alerts(feedback_data)
    
    # Update recipient status
    if feedback_data.get('campaign_recipient_id'):
        await task.campaign_repo.update_recipient_status(
            UUID(feedback_data['campaign_recipient_id']),
            'responded',
            UUID(conversation_id)
        )
    
    # Update message status
    if feedback_data.get('message_id'):
        await task.campaign_repo.update_message_status(
            UUID(feedback_data['message_id']),
            'responded'
        )
    
    return {
        'conversation_id': conversation_id,
        'alerts_generated': len(alerts),
        'rating': feedback_data.get('rating'),
        'sentiment': feedback_data.get('sentiment_score')
    }


async def _get_variant_config(
    campaign_repo: CampaignRepository,
    campaign_id: str,
    variant_id: str
) -> Optional[Dict[str, Any]]:
    """Get configuration for an A/B test variant"""
    # Get active experiment for campaign
    experiments = campaign_repo.supabase.table('feedback_experiments').select('*').eq(
        'campaign_id', campaign_id
    ).eq('status', 'running').execute()
    
    if not experiments.data:
        return None
    
    experiment = experiments.data[0]
    variants = experiment.get('variants', [])
    
    for variant in variants:
        if variant.get('id') == variant_id:
            return variant.get('parameters', {})
    
    return None


# Beat schedule configuration
app.conf.beat_schedule = {
    'process-scheduled-feedback': {
        'task': 'feedback_tasks.send_scheduled_feedback',
        'schedule': 300.0,  # Every 5 minutes
    },
    'update-campaign-metrics': {
        'task': 'feedback_tasks.update_campaign_metrics',
        'schedule': 600.0,  # Every 10 minutes
    },
    'generate-daily-reports': {
        'task': 'feedback_tasks.generate_daily_reports',
        'schedule': {
            'hour': 6,
            'minute': 0
        }
    }
}