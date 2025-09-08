"""
Feedback Aggregation Processor
Collects and processes feedback data for analytics
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from uuid import UUID
import pandas as pd
from supabase import create_client, Client
import os
import json

from ..schemas import AnalyticsMetrics


class FeedbackAggregator:
    """Process and aggregate feedback data for analytics"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
    
    async def aggregate_daily_metrics(
        self,
        restaurant_id: UUID,
        target_date: date
    ) -> AnalyticsMetrics:
        """
        Aggregate all feedback metrics for a single day
        """
        date_start = datetime.combine(target_date, datetime.min.time())
        date_end = datetime.combine(target_date, datetime.max.time())
        
        # Get campaign data for the day
        campaigns_data = await self._get_campaigns_data(
            restaurant_id, date_start, date_end
        )
        
        # Get feedback responses
        feedback_data = await self._get_feedback_data(
            restaurant_id, date_start, date_end
        )
        
        # Get message statistics
        message_stats = await self._get_message_stats(
            restaurant_id, date_start, date_end
        )
        
        # Calculate metrics
        metrics = self._calculate_metrics(campaigns_data, feedback_data, message_stats)
        
        return AnalyticsMetrics(**metrics)
    
    async def aggregate_period_metrics(
        self,
        restaurant_id: UUID,
        start_date: date,
        end_date: date
    ) -> AnalyticsMetrics:
        """
        Aggregate metrics for a date range
        """
        date_start = datetime.combine(start_date, datetime.min.time())
        date_end = datetime.combine(end_date, datetime.max.time())
        
        campaigns_data = await self._get_campaigns_data(
            restaurant_id, date_start, date_end
        )
        feedback_data = await self._get_feedback_data(
            restaurant_id, date_start, date_end
        )
        message_stats = await self._get_message_stats(
            restaurant_id, date_start, date_end
        )
        
        metrics = self._calculate_metrics(campaigns_data, feedback_data, message_stats)
        
        return AnalyticsMetrics(**metrics)
    
    async def get_trends(
        self,
        restaurant_id: UUID,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Get daily trends for the specified period
        """
        trends = {
            "daily_metrics": [],
            "rating_trends": [],
            "sentiment_trends": [],
            "topic_trends": {},
            "campaign_performance": []
        }
        
        current_date = start_date
        while current_date <= end_date:
            daily_metrics = await self.aggregate_daily_metrics(restaurant_id, current_date)
            
            trends["daily_metrics"].append({
                "date": current_date.isoformat(),
                "campaigns_sent": daily_metrics.campaigns_sent,
                "response_rate": daily_metrics.response_rate,
                "average_rating": daily_metrics.average_rating,
                "positive_count": daily_metrics.positive_count,
                "negative_count": daily_metrics.negative_count
            })
            
            current_date += timedelta(days=1)
        
        # Get rating trends
        rating_trends = await self._get_rating_trends(restaurant_id, start_date, end_date)
        trends["rating_trends"] = rating_trends
        
        # Get sentiment trends
        sentiment_trends = await self._get_sentiment_trends(restaurant_id, start_date, end_date)
        trends["sentiment_trends"] = sentiment_trends
        
        # Get topic trends
        topic_trends = await self._get_topic_trends(restaurant_id, start_date, end_date)
        trends["topic_trends"] = topic_trends
        
        return trends
    
    async def _get_campaigns_data(
        self,
        restaurant_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get campaign data for the time period"""
        result = self.supabase.table('feedback_campaigns').select('*').eq(
            'restaurant_id', str(restaurant_id)
        ).gte('created_at', start_time.isoformat()).lte(
            'created_at', end_time.isoformat()
        ).execute()
        
        return result.data if result.data else []
    
    async def _get_feedback_data(
        self,
        restaurant_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get feedback responses for the time period"""
        result = self.supabase.table('feedback').select('*').eq(
            'restaurant_id', str(restaurant_id)
        ).gte('created_at', start_time.isoformat()).lte(
            'created_at', end_time.isoformat()
        ).execute()
        
        return result.data if result.data else []
    
    async def _get_message_stats(
        self,
        restaurant_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, int]:
        """Get message sending statistics"""
        # Get messages sent via campaigns
        campaigns = await self._get_campaigns_data(restaurant_id, start_time, end_time)
        campaign_ids = [c['id'] for c in campaigns]
        
        if not campaign_ids:
            return {
                'messages_sent': 0,
                'messages_delivered': 0,
                'messages_read': 0,
                'responses_received': 0
            }
        
        # Query campaign messages
        message_query = self.supabase.table('campaign_messages').select(
            'status'
        ).in_('campaign_id', campaign_ids).execute()
        
        messages = message_query.data if message_query.data else []
        
        stats = {
            'messages_sent': 0,
            'messages_delivered': 0,
            'messages_read': 0,
            'responses_received': 0
        }
        
        for message in messages:
            status = message.get('status', '')
            if status in ['sent', 'delivered', 'read', 'responded']:
                stats['messages_sent'] += 1
            if status in ['delivered', 'read', 'responded']:
                stats['messages_delivered'] += 1
            if status in ['read', 'responded']:
                stats['messages_read'] += 1
            if status == 'responded':
                stats['responses_received'] += 1
        
        return stats
    
    def _calculate_metrics(
        self,
        campaigns_data: List[Dict[str, Any]],
        feedback_data: List[Dict[str, Any]],
        message_stats: Dict[str, int]
    ) -> Dict[str, Any]:
        """Calculate aggregated metrics from raw data"""
        
        # Basic counts
        campaigns_count = len(campaigns_data)
        feedback_count = len(feedback_data)
        messages_sent = message_stats.get('messages_sent', 0)
        responses_received = message_stats.get('responses_received', 0)
        
        # Response rate
        response_rate = (responses_received / messages_sent * 100) if messages_sent > 0 else 0
        
        # Rating analysis
        ratings = [f.get('rating') for f in feedback_data if f.get('rating')]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Sentiment analysis
        sentiments = [f.get('sentiment_score', 0) for f in feedback_data]
        average_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # Rating distribution
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[str(i)] = len([r for r in ratings if r == i])
        
        # Positive/negative counts
        positive_count = len([f for f in feedback_data if f.get('sentiment_score', 0) > 0.3])
        negative_count = len([f for f in feedback_data if f.get('sentiment_score', 0) < -0.3])
        neutral_count = feedback_count - positive_count - negative_count
        
        # Topic analysis
        all_topics = []
        for feedback in feedback_data:
            topics = feedback.get('topics', [])
            if isinstance(topics, list):
                all_topics.extend(topics)
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Top issues (negative feedback topics)
        negative_feedback = [f for f in feedback_data if f.get('sentiment_score', 0) < -0.3]
        issue_topics = []
        for feedback in negative_feedback:
            topics = feedback.get('topics', [])
            if isinstance(topics, list):
                issue_topics.extend(topics)
        
        top_issues = {}
        for topic in issue_topics:
            top_issues[topic] = top_issues.get(topic, 0) + 1
        
        return {
            "date": datetime.now().date(),
            "campaigns_created": campaigns_count,
            "campaigns_sent": len([c for c in campaigns_data if c.get('status') in ['active', 'completed']]),
            "messages_sent": messages_sent,
            "messages_delivered": message_stats.get('messages_delivered', 0),
            "responses_received": responses_received,
            "response_rate": round(response_rate, 2),
            "feedback_collected": feedback_count,
            "average_rating": round(average_rating, 2),
            "average_sentiment": round(average_sentiment, 3),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "rating_distribution": rating_distribution,
            "topic_counts": dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_issues": dict(sorted(top_issues.items(), key=lambda x: x[1], reverse=True)[:5]),
            "completion_rate": round((feedback_count / messages_sent * 100) if messages_sent > 0 else 0, 2)
        }
    
    async def _get_rating_trends(
        self,
        restaurant_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get daily rating trends"""
        query = f"""
        SELECT 
            DATE(created_at) as date,
            AVG(rating) as avg_rating,
            COUNT(*) as total_ratings,
            COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_ratings,
            COUNT(CASE WHEN rating <= 2 THEN 1 END) as negative_ratings
        FROM feedback 
        WHERE restaurant_id = '{restaurant_id}' 
        AND DATE(created_at) BETWEEN '{start_date}' AND '{end_date}'
        AND rating IS NOT NULL
        GROUP BY DATE(created_at)
        ORDER BY date
        """
        
        # This would need to be implemented with proper SQL execution
        # For now, return empty list
        return []
    
    async def _get_sentiment_trends(
        self,
        restaurant_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get daily sentiment trends"""
        # Similar implementation to rating trends
        return []
    
    async def _get_topic_trends(
        self,
        restaurant_id: UUID,
        start_date: date,
        end_date: date
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get trending topics over time"""
        date_start = datetime.combine(start_date, datetime.min.time())
        date_end = datetime.combine(end_date, datetime.max.time())
        
        # Get all feedback with topics
        result = self.supabase.table('feedback').select(
            'created_at, topics, sentiment_score'
        ).eq('restaurant_id', str(restaurant_id)).gte(
            'created_at', date_start.isoformat()
        ).lte('created_at', date_end.isoformat()).execute()
        
        feedback_data = result.data if result.data else []
        
        # Process by day
        daily_topics = {}
        for feedback in feedback_data:
            feedback_date = datetime.fromisoformat(feedback['created_at']).date()
            date_key = feedback_date.isoformat()
            
            if date_key not in daily_topics:
                daily_topics[date_key] = {}
            
            topics = feedback.get('topics', [])
            if isinstance(topics, list):
                for topic in topics:
                    if topic not in daily_topics[date_key]:
                        daily_topics[date_key][topic] = {
                            'count': 0,
                            'sentiment_sum': 0,
                            'sentiment_count': 0
                        }
                    
                    daily_topics[date_key][topic]['count'] += 1
                    
                    sentiment = feedback.get('sentiment_score')
                    if sentiment is not None:
                        daily_topics[date_key][topic]['sentiment_sum'] += sentiment
                        daily_topics[date_key][topic]['sentiment_count'] += 1
        
        # Format for output
        topic_trends = {}
        for date_key, topics_data in daily_topics.items():
            for topic, data in topics_data.items():
                if topic not in topic_trends:
                    topic_trends[topic] = []
                
                avg_sentiment = (
                    data['sentiment_sum'] / data['sentiment_count']
                    if data['sentiment_count'] > 0 else 0
                )
                
                topic_trends[topic].append({
                    'date': date_key,
                    'count': data['count'],
                    'average_sentiment': round(avg_sentiment, 3)
                })
        
        # Sort each topic's data by date
        for topic in topic_trends:
            topic_trends[topic].sort(key=lambda x: x['date'])
        
        return topic_trends
    
    async def store_report(
        self,
        restaurant_id: UUID,
        report_date: date,
        report_data: Dict[str, Any]
    ) -> bool:
        """Store generated report in database"""
        try:
            report_record = {
                'restaurant_id': str(restaurant_id),
                'report_date': report_date.isoformat(),
                'report_type': 'daily_summary',
                'data': report_data,
                'created_at': datetime.now().isoformat()
            }
            
            # Upsert report (update if exists, insert if not)
            result = self.supabase.table('analytics_reports').upsert(
                report_record,
                on_conflict=['restaurant_id', 'report_date', 'report_type']
            ).execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error storing report: {e}")
            return False
    
    async def get_stored_report(
        self,
        restaurant_id: UUID,
        report_date: date,
        report_type: str = 'daily_summary'
    ) -> Optional[Dict[str, Any]]:
        """Get previously stored report"""
        result = self.supabase.table('analytics_reports').select('*').eq(
            'restaurant_id', str(restaurant_id)
        ).eq('report_date', report_date.isoformat()).eq(
            'report_type', report_type
        ).single().execute()
        
        return result.data if result.data else None