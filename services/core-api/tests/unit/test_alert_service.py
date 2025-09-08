"""
Unit tests for alert service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4

from src.services.alert_service import AlertService, AlertPriority


class TestAlertService:
    
    @pytest.fixture
    def mock_supabase(self):
        supabase = Mock()
        
        # Mock table method chain
        table_mock = Mock()
        insert_mock = Mock()
        execute_mock = Mock()
        
        # Chain the mocks
        supabase.table.return_value = table_mock
        table_mock.insert.return_value = insert_mock
        insert_mock.execute.return_value = execute_mock
        
        return supabase
    
    @pytest.fixture
    def alert_service(self, mock_supabase):
        service = AlertService("test_url", "test_key")
        service.supabase = mock_supabase
        return service
    
    @pytest.fixture
    def negative_feedback(self):
        return {
            'id': str(uuid4()),
            'restaurant_id': str(uuid4()),
            'conversation_id': str(uuid4()),
            'customer_phone': '+966501234567',
            'rating': 1,
            'sentiment_score': -0.8,
            'message': 'الطعام كان سيء جداً والخدمة بطيئة',
            'topics': ['طعام', 'خدمة']
        }
    
    @pytest.fixture
    def positive_feedback(self):
        return {
            'id': str(uuid4()),
            'restaurant_id': str(uuid4()),
            'conversation_id': str(uuid4()),
            'customer_phone': '+966501234567',
            'rating': 5,
            'sentiment_score': 0.9,
            'message': 'تجربة رائعة! الطعام ممتاز',
            'topics': ['طعام', 'تجربة']
        }
    
    @pytest.fixture
    def food_quality_issue_feedback(self):
        return {
            'id': str(uuid4()),
            'restaurant_id': str(uuid4()),
            'conversation_id': str(uuid4()),
            'customer_phone': '+966502345678',
            'rating': 2,
            'sentiment_score': -0.6,
            'message': 'البرجر كان نيء من الداخل',
            'topics': ['food quality', 'برجر']
        }
    
    def test_alert_rules_initialization(self, alert_service):
        """Test that alert rules are properly initialized"""
        rules = alert_service.alert_rules
        
        assert len(rules) > 0
        
        # Check for expected rule types
        rule_ids = [rule['id'] for rule in rules]
        expected_rules = [
            'low_rating_immediate',
            'medium_rating', 
            'negative_sentiment',
            'food_quality_issue',
            'service_complaint'
        ]
        
        for expected_rule in expected_rules:
            assert expected_rule in rule_ids
        
        # Verify rule structure
        for rule in rules:
            assert 'id' in rule
            assert 'condition' in rule
            assert 'priority' in rule
            assert 'description' in rule
            assert callable(rule['condition'])
    
    def test_low_rating_immediate_rule(self, alert_service, negative_feedback):
        """Test immediate alert rule for very low ratings"""
        rules = alert_service.alert_rules
        low_rating_rule = next(r for r in rules if r['id'] == 'low_rating_immediate')
        
        # Test with 1-star rating
        assert low_rating_rule['condition'](negative_feedback) is True
        assert low_rating_rule['priority'] == AlertPriority.IMMEDIATE
        
        # Test with higher rating
        feedback_3_stars = {**negative_feedback, 'rating': 3}
        assert low_rating_rule['condition'](feedback_3_stars) is False
    
    def test_negative_sentiment_rule(self, alert_service, negative_feedback):
        """Test negative sentiment alert rule"""
        rules = alert_service.alert_rules
        sentiment_rule = next(r for r in rules if r['id'] == 'negative_sentiment')
        
        # Test with strong negative sentiment
        assert sentiment_rule['condition'](negative_feedback) is True
        assert sentiment_rule['priority'] == AlertPriority.HIGH
        
        # Test with neutral sentiment
        neutral_feedback = {**negative_feedback, 'sentiment_score': 0.1}
        assert sentiment_rule['condition'](neutral_feedback) is False
    
    def test_food_quality_issue_rule(self, alert_service, food_quality_issue_feedback):
        """Test food quality issue detection rule"""
        rules = alert_service.alert_rules
        food_rule = next(r for r in rules if r['id'] == 'food_quality_issue')
        
        # Test with food quality issue
        assert food_rule['condition'](food_quality_issue_feedback) is True
        assert food_rule['priority'] == AlertPriority.HIGH
        
        # Test without food quality topic
        no_food_feedback = {
            **food_quality_issue_feedback, 
            'topics': ['service', 'staff']
        }
        assert food_rule['condition'](no_food_feedback) is False
        
        # Test with food quality but positive sentiment
        positive_food_feedback = {
            **food_quality_issue_feedback,
            'sentiment_score': 0.5
        }
        assert food_rule['condition'](positive_food_feedback) is False
    
    @pytest.mark.asyncio
    async def test_process_feedback_for_alerts_negative(
        self, 
        alert_service, 
        negative_feedback,
        mock_supabase
    ):
        """Test alert processing for negative feedback"""
        # Mock database response for alert creation
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {'id': str(uuid4()), **negative_feedback}
        ]
        
        with patch.object(alert_service, '_send_notifications') as mock_send:
            alerts = await alert_service.process_feedback_for_alerts(negative_feedback)
            
            # Should generate multiple alerts for very negative feedback
            assert len(alerts) >= 2  # Low rating + negative sentiment
            
            # Verify alert properties
            for alert in alerts:
                assert alert['restaurant_id'] == negative_feedback['restaurant_id']
                assert alert['feedback_id'] == negative_feedback['id']
                assert alert['status'] == 'pending'
                assert 'priority' in alert
                assert 'title' in alert
                assert 'details' in alert
            
            # Should send notifications for high priority alerts
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_feedback_for_alerts_positive(
        self, 
        alert_service, 
        positive_feedback,
        mock_supabase
    ):
        """Test alert processing for positive feedback"""
        with patch.object(alert_service, '_send_notifications') as mock_send:
            alerts = await alert_service.process_feedback_for_alerts(positive_feedback)
            
            # Should generate no alerts for positive feedback
            assert len(alerts) == 0
            
            # Should not send notifications
            mock_send.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_alert(self, alert_service, negative_feedback, mock_supabase):
        """Test alert creation"""
        rules = alert_service.alert_rules
        low_rating_rule = next(r for r in rules if r['id'] == 'low_rating_immediate')
        
        # Mock successful database insertion
        alert_id = str(uuid4())
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {'id': alert_id}
        ]
        
        alert = await alert_service._create_alert(negative_feedback, low_rating_rule)
        
        assert alert['id'] == alert_id
        
        # Verify database call
        mock_supabase.table.assert_called_with('feedback_alerts')
        
        # Verify alert data structure
        insert_call = mock_supabase.table.return_value.insert.call_args[0][0]
        assert insert_call['restaurant_id'] == negative_feedback['restaurant_id']
        assert insert_call['feedback_id'] == negative_feedback['id']
        assert insert_call['rule_id'] == low_rating_rule['id']
        assert insert_call['priority'] == low_rating_rule['priority'].value
        assert insert_call['status'] == 'pending'
    
    @pytest.mark.asyncio
    async def test_broadcast_realtime_alert(self, alert_service, mock_supabase):
        """Test real-time alert broadcasting"""
        alert = {
            'id': str(uuid4()),
            'restaurant_id': str(uuid4()),
            'priority': 'immediate',
            'title': 'Test Alert'
        }
        
        # Mock realtime table insertion
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()
        
        await alert_service._broadcast_realtime_alert(alert)
        
        # Verify realtime table was called
        mock_supabase.table.assert_called_with('realtime_alerts')
        
        # Verify inserted data structure
        insert_call = mock_supabase.table.return_value.insert.call_args[0][0]
        assert insert_call['channel'] == f"alerts:{alert['restaurant_id']}"
        assert insert_call['type'] == 'feedback_alert'
        assert insert_call['data'] == alert
    
    @pytest.mark.asyncio
    async def test_send_push_notification(self, alert_service, mock_supabase):
        """Test push notification sending"""
        alert = {
            'id': str(uuid4()),
            'restaurant_id': str(uuid4()),
            'priority': 'immediate',
            'title': 'Test Alert'
        }
        
        feedback = {
            'rating': 1,
            'customer_phone': '+966501234567'
        }
        
        # Mock restaurant owner data
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                'device_tokens': ['device_token_1', 'device_token_2']
            }
        ]
        
        with patch.object(alert_service, '_send_fcm_notification') as mock_fcm:
            await alert_service._send_push_notification(alert, feedback)
            
            # Should send notification to all device tokens
            assert mock_fcm.call_count == 2
            
            # Verify notification structure
            call_args = mock_fcm.call_args_list[0][0][0]
            assert call_args['token'] == 'device_token_1'
            assert 'Customer rated' in call_args['body']
            assert call_args['data']['alert_id'] == alert['id']
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, alert_service, mock_supabase):
        """Test alert acknowledgment"""
        alert_id = uuid4()
        user_id = uuid4()
        notes = "تم التعامل مع المشكلة"
        
        # Mock successful update
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {'id': str(alert_id)}
        ]
        
        result = await alert_service.acknowledge_alert(alert_id, user_id, notes)
        
        assert result is True
        
        # Verify update call
        mock_supabase.table.assert_called_with('feedback_alerts')
        update_data = mock_supabase.table.return_value.update.call_args[0][0]
        
        assert update_data['status'] == 'acknowledged'
        assert update_data['acknowledged_by'] == str(user_id)
        assert update_data['acknowledgment_notes'] == notes
        assert 'acknowledged_at' in update_data
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, alert_service, mock_supabase):
        """Test retrieving active alerts"""
        restaurant_id = uuid4()
        
        # Mock database response
        mock_alerts = [
            {
                'id': str(uuid4()),
                'restaurant_id': str(restaurant_id),
                'priority': 'immediate',
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': str(uuid4()),
                'restaurant_id': str(restaurant_id),
                'priority': 'high',
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = mock_alerts
        
        alerts = await alert_service.get_active_alerts(restaurant_id)
        
        assert len(alerts) == 2
        assert all(alert['status'] == 'pending' for alert in alerts)
        
        # Verify database query
        mock_supabase.table.assert_called_with('feedback_alerts')
    
    @pytest.mark.asyncio
    async def test_get_active_alerts_with_priority_filter(self, alert_service, mock_supabase):
        """Test retrieving active alerts with priority filter"""
        restaurant_id = uuid4()
        
        # Mock database response for immediate priority only
        mock_alerts = [
            {
                'id': str(uuid4()),
                'restaurant_id': str(restaurant_id),
                'priority': 'immediate',
                'status': 'pending'
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = mock_alerts
        
        alerts = await alert_service.get_active_alerts(
            restaurant_id, 
            priority=AlertPriority.IMMEDIATE
        )
        
        assert len(alerts) == 1
        assert alerts[0]['priority'] == 'immediate'
    
    @pytest.mark.asyncio
    async def test_get_alert_statistics(self, alert_service, mock_supabase):
        """Test alert statistics calculation"""
        restaurant_id = uuid4()
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        # Mock alert data
        mock_alerts = [
            {
                'id': str(uuid4()),
                'priority': 'immediate',
                'status': 'pending',
                'rule_id': 'low_rating_immediate',
                'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                'acknowledged_at': None
            },
            {
                'id': str(uuid4()),
                'priority': 'high',
                'status': 'acknowledged',
                'rule_id': 'food_quality_issue',
                'created_at': (datetime.now() - timedelta(hours=4)).isoformat(),
                'acknowledged_at': (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                'id': str(uuid4()),
                'priority': 'medium',
                'status': 'acknowledged',
                'rule_id': 'food_quality_issue',
                'created_at': (datetime.now() - timedelta(days=1)).isoformat(),
                'acknowledged_at': (datetime.now() - timedelta(hours=20)).isoformat()
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value.data = mock_alerts
        
        stats = await alert_service.get_alert_statistics(
            restaurant_id, start_date, end_date
        )
        
        assert stats['total_alerts'] == 3
        assert stats['by_priority']['immediate'] == 1
        assert stats['by_priority']['high'] == 1
        assert stats['by_priority']['medium'] == 1
        assert stats['by_status']['pending'] == 1
        assert stats['by_status']['acknowledged'] == 2
        
        # Check top issues
        assert len(stats['top_issues']) > 0
        assert stats['top_issues'][0] == ('food_quality_issue', 2)  # Most common
        
        # Should calculate average response time
        assert stats['average_response_time'] is not None
        assert stats['average_response_time'] > 0
    
    def test_alert_priority_enum_values(self):
        """Test AlertPriority enum values"""
        assert AlertPriority.IMMEDIATE.value == "immediate"
        assert AlertPriority.HIGH.value == "high"
        assert AlertPriority.MEDIUM.value == "medium"
        assert AlertPriority.LOW.value == "low"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_send_webhook_notification(self, mock_httpx, alert_service):
        """Test webhook notification sending"""
        alert_service.webhook_url = "https://example.com/webhook"
        
        alerts = [{'id': str(uuid4()), 'title': 'Test Alert'}]
        feedback = {'rating': 1, 'message': 'Bad experience'}
        
        # Mock HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client = Mock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        await alert_service._send_webhook_notification(alerts, feedback)
        
        # Verify webhook was called
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        
        assert call_args[0][0] == "https://example.com/webhook"
        webhook_data = call_args[1]['json']
        assert webhook_data['type'] == 'feedback_alert'
        assert webhook_data['alerts'] == alerts
        assert webhook_data['feedback'] == feedback