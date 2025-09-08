"""
Real-time Alert Service
Handles negative feedback alerts and notifications
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import asyncio
import json
from enum import Enum

from supabase import create_client, Client
import httpx


class AlertPriority(Enum):
    """Alert priority levels"""
    IMMEDIATE = "immediate"  # 1-2 star ratings
    HIGH = "high"           # Repeated issues
    MEDIUM = "medium"       # 3 star ratings
    LOW = "low"            # General feedback


class AlertService:
    """Manage real-time alerts for feedback"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.webhook_url = None  # Optional webhook for external alerts
        self.alert_rules = self._initialize_alert_rules()
        
    def _initialize_alert_rules(self) -> List[Dict[str, Any]]:
        """Define alert trigger rules"""
        return [
            {
                'id': 'low_rating_immediate',
                'condition': lambda feedback: feedback.get('rating', 5) <= 2,
                'priority': AlertPriority.IMMEDIATE,
                'description': 'Very low rating (1-2 stars)'
            },
            {
                'id': 'medium_rating',
                'condition': lambda feedback: feedback.get('rating', 5) == 3,
                'priority': AlertPriority.MEDIUM,
                'description': 'Medium rating (3 stars)'
            },
            {
                'id': 'negative_sentiment',
                'condition': lambda feedback: feedback.get('sentiment_score', 0) < -0.5,
                'priority': AlertPriority.HIGH,
                'description': 'Strong negative sentiment detected'
            },
            {
                'id': 'food_quality_issue',
                'condition': lambda feedback: 'food quality' in feedback.get('topics', []) 
                                            and feedback.get('sentiment_score', 0) < 0,
                'priority': AlertPriority.HIGH,
                'description': 'Food quality complaint'
            },
            {
                'id': 'service_complaint',
                'condition': lambda feedback: 'service' in feedback.get('topics', []) 
                                            and feedback.get('sentiment_score', 0) < 0,
                'priority': AlertPriority.HIGH,
                'description': 'Service complaint'
            },
            {
                'id': 'repeated_issue',
                'condition': lambda feedback: feedback.get('is_repeated_issue', False),
                'priority': AlertPriority.HIGH,
                'description': 'Repeated customer complaint'
            }
        ]
    
    async def process_feedback_for_alerts(
        self,
        feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Process feedback and generate alerts if needed
        Returns list of generated alerts
        """
        generated_alerts = []
        
        for rule in self.alert_rules:
            if rule['condition'](feedback):
                alert = await self._create_alert(feedback, rule)
                generated_alerts.append(alert)
        
        # Send notifications for high priority alerts
        high_priority_alerts = [
            a for a in generated_alerts 
            if a['priority'] in [AlertPriority.IMMEDIATE.value, AlertPriority.HIGH.value]
        ]
        
        if high_priority_alerts:
            await self._send_notifications(high_priority_alerts, feedback)
        
        return generated_alerts
    
    async def _create_alert(
        self,
        feedback: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an alert record"""
        alert_data = {
            'restaurant_id': feedback.get('restaurant_id'),
            'feedback_id': feedback.get('id'),
            'conversation_id': feedback.get('conversation_id'),
            'rule_id': rule['id'],
            'priority': rule['priority'].value,
            'title': rule['description'],
            'details': {
                'customer_phone': feedback.get('customer_phone'),
                'rating': feedback.get('rating'),
                'sentiment_score': feedback.get('sentiment_score'),
                'message': feedback.get('message'),
                'topics': feedback.get('topics', [])
            },
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        # Store in database
        result = self.supabase.table('feedback_alerts').insert(alert_data).execute()
        
        return result.data[0] if result.data else alert_data
    
    async def _send_notifications(
        self,
        alerts: List[Dict[str, Any]],
        feedback: Dict[str, Any]
    ):
        """Send real-time notifications for alerts"""
        
        # 1. Send via Supabase Realtime
        await self._broadcast_realtime_alert(alerts[0])  # Send highest priority
        
        # 2. Send push notification (if configured)
        await self._send_push_notification(alerts[0], feedback)
        
        # 3. Send webhook (if configured)
        if self.webhook_url:
            await self._send_webhook_notification(alerts, feedback)
    
    async def _broadcast_realtime_alert(self, alert: Dict[str, Any]):
        """Broadcast alert via Supabase Realtime"""
        try:
            # Publish to realtime channel
            channel_name = f"alerts:{alert['restaurant_id']}"
            
            # Note: In production, this would use Supabase Realtime client
            # For now, we'll insert into a special table that triggers realtime
            self.supabase.table('realtime_alerts').insert({
                'channel': channel_name,
                'type': 'feedback_alert',
                'data': alert,
                'created_at': datetime.now().isoformat()
            }).execute()
            
        except Exception as e:
            print(f"Error broadcasting realtime alert: {e}")
    
    async def _send_push_notification(
        self,
        alert: Dict[str, Any],
        feedback: Dict[str, Any]
    ):
        """Send push notification to restaurant owner's mobile"""
        try:
            # Get restaurant owner's device tokens
            owner_data = self.supabase.table('restaurant_owners').select(
                'device_tokens'
            ).eq('restaurant_id', alert['restaurant_id']).execute()
            
            if not owner_data.data:
                return
            
            device_tokens = owner_data.data[0].get('device_tokens', [])
            
            for token in device_tokens:
                # Send via push notification service (FCM/APNS)
                notification_data = {
                    'token': token,
                    'title': f"⚠️ {alert['title']}",
                    'body': f"Customer rated {feedback.get('rating', 'N/A')} stars",
                    'data': {
                        'alert_id': alert.get('id'),
                        'feedback_id': feedback.get('id'),
                        'priority': alert['priority']
                    }
                }
                
                # This would integrate with FCM/APNS
                await self._send_fcm_notification(notification_data)
                
        except Exception as e:
            print(f"Error sending push notification: {e}")
    
    async def _send_fcm_notification(self, notification_data: Dict[str, Any]):
        """Send notification via Firebase Cloud Messaging"""
        # Placeholder for FCM integration
        pass
    
    async def _send_webhook_notification(
        self,
        alerts: List[Dict[str, Any]],
        feedback: Dict[str, Any]
    ):
        """Send alert via webhook"""
        if not self.webhook_url:
            return
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.webhook_url,
                    json={
                        'type': 'feedback_alert',
                        'alerts': alerts,
                        'feedback': feedback,
                        'timestamp': datetime.now().isoformat()
                    },
                    timeout=10.0
                )
        except Exception as e:
            print(f"Error sending webhook: {e}")
    
    async def acknowledge_alert(
        self,
        alert_id: UUID,
        acknowledged_by: UUID,
        notes: Optional[str] = None
    ) -> bool:
        """Mark an alert as acknowledged"""
        try:
            update_data = {
                'status': 'acknowledged',
                'acknowledged_at': datetime.now().isoformat(),
                'acknowledged_by': str(acknowledged_by)
            }
            
            if notes:
                update_data['acknowledgment_notes'] = notes
            
            result = self.supabase.table('feedback_alerts').update(
                update_data
            ).eq('id', str(alert_id)).execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error acknowledging alert: {e}")
            return False
    
    async def get_active_alerts(
        self,
        restaurant_id: UUID,
        priority: Optional[AlertPriority] = None
    ) -> List[Dict[str, Any]]:
        """Get active (unacknowledged) alerts for a restaurant"""
        query = self.supabase.table('feedback_alerts').select('*').eq(
            'restaurant_id', str(restaurant_id)
        ).eq('status', 'pending')
        
        if priority:
            query = query.eq('priority', priority.value)
        
        result = query.order('created_at', desc=True).execute()
        
        return result.data if result.data else []
    
    async def get_alert_statistics(
        self,
        restaurant_id: UUID,
        date_from: datetime,
        date_to: datetime
    ) -> Dict[str, Any]:
        """Get alert statistics for a restaurant"""
        # Query alerts within date range
        result = self.supabase.table('feedback_alerts').select('*').eq(
            'restaurant_id', str(restaurant_id)
        ).gte('created_at', date_from.isoformat()).lte(
            'created_at', date_to.isoformat()
        ).execute()
        
        alerts = result.data if result.data else []
        
        # Calculate statistics
        stats = {
            'total_alerts': len(alerts),
            'by_priority': {},
            'by_status': {},
            'average_response_time': None,
            'top_issues': []
        }
        
        # Count by priority
        for priority in AlertPriority:
            count = len([a for a in alerts if a['priority'] == priority.value])
            stats['by_priority'][priority.value] = count
        
        # Count by status
        for status in ['pending', 'acknowledged', 'resolved']:
            count = len([a for a in alerts if a.get('status') == status])
            stats['by_status'][status] = count
        
        # Calculate average response time for acknowledged alerts
        response_times = []
        for alert in alerts:
            if alert.get('acknowledged_at'):
                created = datetime.fromisoformat(alert['created_at'])
                acknowledged = datetime.fromisoformat(alert['acknowledged_at'])
                response_times.append((acknowledged - created).total_seconds())
        
        if response_times:
            stats['average_response_time'] = sum(response_times) / len(response_times)
        
        # Find top issues
        issue_counts = {}
        for alert in alerts:
            rule_id = alert.get('rule_id')
            if rule_id:
                issue_counts[rule_id] = issue_counts.get(rule_id, 0) + 1
        
        stats['top_issues'] = sorted(
            issue_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return stats