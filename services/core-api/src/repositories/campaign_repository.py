"""
Campaign Repository
Data access layer for feedback campaigns
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID, uuid4
from supabase import create_client, Client
import os


class CampaignRepository:
    """Repository for campaign data operations"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
    
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new feedback campaign"""
        campaign_data['id'] = str(uuid4())
        campaign_data['created_at'] = datetime.now().isoformat()
        
        result = self.supabase.table('feedback_campaigns').insert(
            campaign_data
        ).execute()
        
        return result.data[0] if result.data else None
    
    async def get_campaign(self, campaign_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a campaign by ID"""
        result = self.supabase.table('feedback_campaigns').select('*').eq(
            'id', str(campaign_id)
        ).single().execute()
        
        return result.data if result.data else None
    
    async def update_campaign(
        self,
        campaign_id: UUID,
        update_data: Dict[str, Any]
    ) -> bool:
        """Update campaign data"""
        update_data['updated_at'] = datetime.now().isoformat()
        
        result = self.supabase.table('feedback_campaigns').update(
            update_data
        ).eq('id', str(campaign_id)).execute()
        
        return bool(result.data)
    
    async def list_campaigns(
        self,
        filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List campaigns with filters"""
        query = self.supabase.table('feedback_campaigns').select('*')
        
        if filters.get('status'):
            query = query.eq('status', filters['status'])
        
        if filters.get('restaurant_id'):
            query = query.eq('restaurant_id', str(filters['restaurant_id']))
        
        if filters.get('date_range'):
            date_from, date_to = filters['date_range']
            query = query.gte('created_at', date_from.isoformat())
            query = query.lte('created_at', date_to.isoformat())
        
        result = query.order('created_at', desc=True).range(
            offset, offset + limit - 1
        ).execute()
        
        return result.data if result.data else []
    
    async def soft_delete_campaign(self, campaign_id: UUID) -> bool:
        """Soft delete a campaign"""
        return await self.update_campaign(
            campaign_id,
            {
                'status': 'deleted',
                'deleted_at': datetime.now().isoformat()
            }
        )
    
    async def bulk_create_recipients(
        self,
        campaign_id: str,
        recipients: List[Dict[str, Any]]
    ) -> int:
        """Bulk create campaign recipients"""
        # Add campaign_id and generate IDs
        for recipient in recipients:
            recipient['id'] = str(uuid4())
            recipient['campaign_id'] = campaign_id
            recipient['status'] = 'pending'
            recipient['created_at'] = datetime.now().isoformat()
        
        # Batch insert (Supabase handles up to 1000 at once)
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            result = self.supabase.table('campaign_recipients').insert(batch).execute()
            total_inserted += len(result.data) if result.data else 0
        
        return total_inserted
    
    async def get_campaign_recipients(
        self,
        campaign_id: UUID,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get recipients for a campaign"""
        query = self.supabase.table('campaign_recipients').select('*').eq(
            'campaign_id', str(campaign_id)
        )
        
        if status:
            query = query.eq('status', status)
        
        if limit:
            query = query.limit(limit)
        
        result = query.order('visit_timestamp').execute()
        
        return result.data if result.data else []
    
    async def update_recipient_status(
        self,
        recipient_id: UUID,
        status: str,
        conversation_id: Optional[UUID] = None
    ) -> bool:
        """Update recipient status"""
        update_data = {
            'status': status,
            'updated_at': datetime.now().isoformat()
        }
        
        if conversation_id:
            update_data['conversation_id'] = str(conversation_id)
        
        result = self.supabase.table('campaign_recipients').update(
            update_data
        ).eq('id', str(recipient_id)).execute()
        
        return bool(result.data)
    
    async def create_campaign_message(
        self,
        message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a campaign message record"""
        message_data['id'] = str(uuid4())
        message_data['created_at'] = datetime.now().isoformat()
        
        result = self.supabase.table('campaign_messages').insert(
            message_data
        ).execute()
        
        return result.data[0] if result.data else None
    
    async def get_campaign_messages(
        self,
        campaign_id: UUID,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages for a campaign"""
        query = self.supabase.table('campaign_messages').select('*').eq(
            'campaign_id', str(campaign_id)
        )
        
        if status:
            query = query.eq('status', status)
        
        result = query.order('scheduled_send_time').execute()
        
        return result.data if result.data else []
    
    async def get_message(self, message_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a specific message"""
        result = self.supabase.table('campaign_messages').select('*').eq(
            'id', str(message_id)
        ).single().execute()
        
        return result.data if result.data else None
    
    async def update_message(
        self,
        message_id: UUID,
        update_data: Dict[str, Any]
    ) -> bool:
        """Update a message record"""
        result = self.supabase.table('campaign_messages').update(
            update_data
        ).eq('id', str(message_id)).execute()
        
        return bool(result.data)
    
    async def update_message_status(
        self,
        message_id: UUID,
        status: str
    ) -> bool:
        """Update message status"""
        status_field_map = {
            'sent': 'sent_at',
            'delivered': 'delivered_at',
            'read': 'read_at',
            'responded': 'response_received_at'
        }
        
        update_data = {'status': status}
        
        if status in status_field_map:
            update_data[status_field_map[status]] = datetime.now().isoformat()
        
        return await self.update_message(message_id, update_data)
    
    async def get_campaign_metrics(self, campaign_id: UUID) -> Dict[str, Any]:
        """Calculate campaign metrics"""
        # Get all recipients
        recipients = await self.get_campaign_recipients(campaign_id)
        total_recipients = len(recipients)
        
        if total_recipients == 0:
            return {
                'campaign_id': str(campaign_id),
                'total_recipients': 0,
                'messages_sent': 0,
                'response_rate': 0,
                'average_rating': 0,
                'sentiment_distribution': {},
                'completion_rate': 0
            }
        
        # Count by status
        status_counts = {}
        for recipient in recipients:
            status = recipient.get('status', 'pending')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Get feedback data
        feedback_query = self.supabase.table('feedback').select(
            'rating, sentiment_score'
        ).eq('campaign_id', str(campaign_id)).execute()
        
        feedback_data = feedback_query.data if feedback_query.data else []
        
        # Calculate metrics
        ratings = [f['rating'] for f in feedback_data if f.get('rating')]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        sentiment_dist = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        
        for feedback in feedback_data:
            score = feedback.get('sentiment_score', 0)
            if score > 0.3:
                sentiment_dist['positive'] += 1
            elif score < -0.3:
                sentiment_dist['negative'] += 1
            else:
                sentiment_dist['neutral'] += 1
        
        return {
            'campaign_id': str(campaign_id),
            'total_recipients': total_recipients,
            'messages_sent': status_counts.get('sent', 0) + status_counts.get('responded', 0),
            'responses_received': status_counts.get('responded', 0),
            'response_rate': (status_counts.get('responded', 0) / total_recipients * 100) 
                           if total_recipients > 0 else 0,
            'average_rating': round(avg_rating, 2),
            'sentiment_distribution': sentiment_dist,
            'completion_rate': (len(feedback_data) / total_recipients * 100) 
                             if total_recipients > 0 else 0,
            'status_breakdown': status_counts
        }
    
    async def create_experiment(
        self,
        campaign_id: UUID,
        experiment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an A/B test experiment"""
        experiment_data['id'] = str(uuid4())
        experiment_data['campaign_id'] = str(campaign_id)
        experiment_data['status'] = 'running'
        experiment_data['created_at'] = datetime.now().isoformat()
        
        result = self.supabase.table('feedback_experiments').insert(
            experiment_data
        ).execute()
        
        return result.data[0] if result.data else None
    
    async def get_experiment(
        self,
        experiment_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get an experiment by ID"""
        result = self.supabase.table('feedback_experiments').select('*').eq(
            'id', str(experiment_id)
        ).single().execute()
        
        return result.data if result.data else None
    
    async def update_experiment_metrics(
        self,
        experiment_id: UUID,
        metrics: Dict[str, Any]
    ) -> bool:
        """Update experiment metrics"""
        result = self.supabase.table('feedback_experiments').update({
            'metrics': metrics,
            'updated_at': datetime.now().isoformat()
        }).eq('id', str(experiment_id)).execute()
        
        return bool(result.data)