"""
Feedback Scheduling Service
Manages scheduled sending of feedback requests with prayer time awareness
Enhanced with circuit breaker for external API resilience
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
import asyncio
from celery import Celery
import httpx
import json
import logging

from ..repositories.campaign_repository import CampaignRepository
from ..utils.circuit_breaker import circuit_registry, CommonConfigs, CircuitBreakerException

logger = logging.getLogger(__name__)


class FeedbackScheduler:
    """Schedule and manage feedback message sending"""
    
    def __init__(self):
        self.campaign_repo = CampaignRepository()
        self.celery_app = self._setup_celery()
        self.prayer_api_url = "http://ai-processor:8001/api/prayer-times"
        self.min_delay_hours = 2
        self.max_delay_hours = 4
        
        # Setup circuit breaker for prayer time API
        self.prayer_api_breaker = circuit_registry.get_breaker(
            "prayer_time_api",
            CommonConfigs.EXTERNAL_API
        )
        
        # Cache for prayer time data to reduce API calls
        self._prayer_cache = {}
        self._cache_ttl = 3600  # 1 hour cache
        
    def _setup_celery(self) -> Celery:
        """Initialize Celery app with Redis backend"""
        app = Celery(
            'feedback_scheduler',
            broker='redis://redis:6379/0',
            backend='redis://redis:6379/0'
        )
        
        app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            beat_schedule={
                'process-scheduled-feedback': {
                    'task': 'feedback_tasks.send_scheduled_feedback',
                    'schedule': 300.0,  # Every 5 minutes
                },
                'update-campaign-metrics': {
                    'task': 'feedback_tasks.update_campaign_metrics',
                    'schedule': 600.0,  # Every 10 minutes
                }
            }
        )
        
        return app
    
    async def schedule_campaign(
        self,
        campaign_id: UUID,
        schedule_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Schedule all messages for a campaign
        Returns list of scheduled job details
        """
        # Get campaign recipients
        recipients = await self.campaign_repo.get_campaign_recipients(campaign_id)
        scheduled_jobs = []
        
        for recipient in recipients:
            # Calculate optimal send time
            send_time = await self._calculate_send_time(
                recipient['visit_timestamp'],
                recipient['phone_number']
            )
            
            # Check if send time is within campaign window
            if schedule_params.get('start_time') and send_time < schedule_params['start_time']:
                send_time = schedule_params['start_time']
            if schedule_params.get('end_time') and send_time > schedule_params['end_time']:
                continue  # Skip if outside window
            
            # Create scheduled message
            message_data = {
                'campaign_id': campaign_id,
                'recipient_id': recipient['id'],
                'phone_number': recipient['phone_number'],
                'scheduled_send_time': send_time,
                'status': 'scheduled',
                'message_template': schedule_params.get('template', 'default'),
                'variant_id': None  # Will be assigned if A/B test active
            }
            
            # Store in database
            message = await self.campaign_repo.create_campaign_message(message_data)
            
            # Schedule Celery task
            task = self.celery_app.send_task(
                'feedback_tasks.send_feedback_message',
                args=[str(message['id'])],
                eta=send_time
            )
            
            scheduled_jobs.append({
                'message_id': message['id'],
                'task_id': task.id,
                'scheduled_time': send_time.isoformat(),
                'phone_number': recipient['phone_number']
            })
        
        return scheduled_jobs
    
    async def _calculate_send_time(
        self,
        visit_timestamp: datetime,
        phone_number: str
    ) -> datetime:
        """
        Calculate optimal send time considering prayer times
        Default: 2-4 hours after visit
        """
        # Base calculation: 3 hours after visit
        base_send_time = visit_timestamp + timedelta(hours=3)
        
        # Check prayer times
        prayer_check = await self._check_prayer_time_conflict(base_send_time)
        
        if prayer_check['is_prayer_time']:
            # Adjust to after prayer time
            base_send_time = prayer_check['next_available_time']
        
        # Ensure within min/max delay window
        min_time = visit_timestamp + timedelta(hours=self.min_delay_hours)
        max_time = visit_timestamp + timedelta(hours=self.max_delay_hours)
        
        if base_send_time < min_time:
            return min_time
        elif base_send_time > max_time:
            return max_time
        
        return base_send_time
    
    async def _check_prayer_time_conflict(
        self,
        proposed_time: datetime,
        location: str = 'Riyadh'
    ) -> Dict[str, Any]:
        """
        Check if proposed time conflicts with prayer time
        Returns adjusted time if needed
        Uses circuit breaker and caching for resilience
        """
        # Check cache first
        cache_key = f"{location}_{proposed_time.date().isoformat()}"
        cached_data = self._get_cached_prayer_times(cache_key)
        
        if cached_data:
            return self._check_prayer_conflict_from_cache(proposed_time, cached_data)
        
        try:
            # Use circuit breaker for API call
            prayer_data = await self.prayer_api_breaker.call(
                self._fetch_prayer_times,
                proposed_time,
                location
            )
            
            # Cache the result
            self._cache_prayer_times(cache_key, prayer_data)
            
            if prayer_data and prayer_data.get('is_prayer_time'):
                # Add 30 minutes buffer after prayer time
                next_available = datetime.fromisoformat(
                    prayer_data['prayer_end_time']
                ) + timedelta(minutes=30)
                
                return {
                    'is_prayer_time': True,
                    'next_available_time': next_available,
                    'prayer_name': prayer_data.get('prayer_name', 'Unknown'),
                    'source': 'api'
                }
                
        except CircuitBreakerException as e:
            logger.warning(f"Prayer time API circuit breaker open: {e}")
            return self._fallback_prayer_check(proposed_time, location)
        except Exception as e:
            logger.error(f"Prayer time check failed: {e}")
            return self._fallback_prayer_check(proposed_time, location)
        
        return {
            'is_prayer_time': False,
            'next_available_time': proposed_time,
            'source': 'api'
        }
    
    async def _fetch_prayer_times(self, proposed_time: datetime, location: str) -> Optional[Dict]:
        """Fetch prayer times from API (wrapped by circuit breaker)"""
        timeout_config = httpx.Timeout(connect=5.0, read=10.0)
        
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            response = await client.post(
                self.prayer_api_url,
                json={
                    'timestamp': proposed_time.isoformat(),
                    'location': location
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Prayer API returned status {response.status_code}")
                return None
    
    def _get_cached_prayer_times(self, cache_key: str) -> Optional[Dict]:
        """Get cached prayer time data"""
        if cache_key in self._prayer_cache:
            cached_entry = self._prayer_cache[cache_key]
            if cached_entry['expires'] > datetime.now().timestamp():
                return cached_entry['data']
            else:
                # Remove expired entry
                del self._prayer_cache[cache_key]
        return None
    
    def _cache_prayer_times(self, cache_key: str, data: Dict):
        """Cache prayer time data"""
        self._prayer_cache[cache_key] = {
            'data': data,
            'expires': datetime.now().timestamp() + self._cache_ttl
        }
        
        # Clean up old cache entries (keep cache size manageable)
        if len(self._prayer_cache) > 100:
            oldest_key = min(
                self._prayer_cache.keys(),
                key=lambda k: self._prayer_cache[k]['expires']
            )
            del self._prayer_cache[oldest_key]
    
    def _check_prayer_conflict_from_cache(
        self,
        proposed_time: datetime,
        cached_data: Dict
    ) -> Dict[str, Any]:
        """Check prayer conflict using cached data"""
        try:
            if cached_data and cached_data.get('is_prayer_time'):
                next_available = datetime.fromisoformat(
                    cached_data['prayer_end_time']
                ) + timedelta(minutes=30)
                
                return {
                    'is_prayer_time': True,
                    'next_available_time': next_available,
                    'prayer_name': cached_data.get('prayer_name', 'Unknown'),
                    'source': 'cache'
                }
        except Exception as e:
            logger.warning(f"Cache data parsing failed: {e}")
        
        return {
            'is_prayer_time': False,
            'next_available_time': proposed_time,
            'source': 'cache'
        }
    
    def _fallback_prayer_check(self, proposed_time: datetime, location: str) -> Dict[str, Any]:
        """
        Fallback prayer time checking using basic rules
        Used when external API is unavailable
        """
        hour = proposed_time.hour
        
        # Basic fallback: avoid common prayer times (approximate for Riyadh)
        prayer_hours = [5, 12, 15, 18, 19]  # Fajr, Dhuhr, Asr, Maghrib, Isha (approximate)
        
        if hour in prayer_hours:
            # Move to next safe hour
            safe_hour = hour + 1
            if safe_hour >= 24:
                safe_hour = 6  # Move to next day, 6 AM
            
            next_available = proposed_time.replace(
                hour=safe_hour,
                minute=0,
                second=0,
                microsecond=0
            )
            
            # If we moved to next day, adjust date
            if safe_hour == 6 and hour >= 19:
                next_available += timedelta(days=1)
            
            return {
                'is_prayer_time': True,
                'next_available_time': next_available,
                'prayer_name': 'Estimated',
                'source': 'fallback'
            }
        
        return {
            'is_prayer_time': False,
            'next_available_time': proposed_time,
            'source': 'fallback'
        }
    
    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics for monitoring"""
        return self.prayer_api_breaker.get_stats()
    
    def reset_circuit_breaker(self):
        """Manually reset the prayer time API circuit breaker"""
        self.prayer_api_breaker.reset()
        logger.info("Prayer time API circuit breaker manually reset")
    
    async def cancel_campaign(self, campaign_id: UUID) -> bool:
        """Cancel all scheduled messages for a campaign"""
        try:
            # Get all scheduled messages
            messages = await self.campaign_repo.get_campaign_messages(
                campaign_id,
                status='scheduled'
            )
            
            for message in messages:
                # Revoke Celery task if exists
                if message.get('task_id'):
                    self.celery_app.control.revoke(
                        message['task_id'],
                        terminate=True
                    )
                
                # Update message status
                await self.campaign_repo.update_message_status(
                    message['id'],
                    'cancelled'
                )
            
            # Update campaign status
            await self.campaign_repo.update_campaign(
                campaign_id,
                {'status': 'cancelled'}
            )
            
            return True
            
        except Exception as e:
            print(f"Error cancelling campaign: {e}")
            return False
    
    async def reschedule_message(
        self,
        message_id: UUID,
        new_send_time: datetime
    ) -> bool:
        """Reschedule a single message"""
        try:
            message = await self.campaign_repo.get_message(message_id)
            
            if not message or message['status'] != 'scheduled':
                return False
            
            # Revoke old task
            if message.get('task_id'):
                self.celery_app.control.revoke(message['task_id'])
            
            # Schedule new task
            task = self.celery_app.send_task(
                'feedback_tasks.send_feedback_message',
                args=[str(message_id)],
                eta=new_send_time
            )
            
            # Update message record
            await self.campaign_repo.update_message(
                message_id,
                {
                    'scheduled_send_time': new_send_time,
                    'task_id': task.id
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Error rescheduling message: {e}")
            return False
    
    def get_campaign_schedule_status(
        self,
        campaign_id: UUID
    ) -> Dict[str, Any]:
        """Get scheduling status for a campaign"""
        # This would query Celery's result backend for task statuses
        # Implementation depends on specific Celery configuration
        pass