"""
Integration tests for feedback campaign flow
Tests the complete end-to-end campaign process
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import pandas as pd
import io

from src.services.csv_processor import CSVProcessor
from src.services.feedback_scheduler import FeedbackScheduler
from src.repositories.campaign_repository import CampaignRepository
from src.services.alert_service import AlertService


class TestCampaignFlow:
    """Test the complete feedback campaign workflow"""
    
    @pytest.fixture
    def csv_processor(self):
        return CSVProcessor()
    
    @pytest.fixture
    def feedback_scheduler(self):
        return FeedbackScheduler()
    
    @pytest.fixture
    def campaign_repo(self):
        return CampaignRepository()
    
    @pytest.fixture
    def alert_service(self):
        return AlertService(
            supabase_url="test_url",
            supabase_key="test_key"
        )
    
    @pytest.fixture
    def sample_csv_data(self):
        """Generate sample CSV data for testing"""
        return pd.DataFrame({
            'phone_number': [
                '0501234567',
                '0502345678', 
                '0503456789',
                '+966504567890',
                '966505678901'
            ],
            'visit_timestamp': [
                '2025-01-08 14:30:00',
                '2025-01-08 15:45:00',
                '2025-01-08 19:20:00',
                '2025-01-08 20:15:00',
                '2025-01-08 21:30:00'
            ],
            'customer_name': [
                'أحمد علي',
                'فاطمة حسن',
                'محمد سالم',
                'نورا أحمد',
                'خالد محمد'
            ],
            'table_number': ['5', '12', '8', '3', '15']
        })
    
    @pytest.mark.asyncio
    async def test_complete_campaign_creation_flow(
        self,
        csv_processor,
        campaign_repo,
        sample_csv_data
    ):
        """Test complete campaign creation from CSV upload"""
        
        # Step 1: Validate CSV
        validation_result = csv_processor.validate_csv(sample_csv_data)
        assert validation_result['valid'] is True
        assert validation_result['row_count'] == 5
        
        # Step 2: Process recipients
        processed_data = csv_processor.process_recipients(sample_csv_data)
        assert processed_data['valid_count'] == 5
        assert processed_data['duplicates_count'] == 0
        assert processed_data['invalid_count'] == 0
        
        # Step 3: Create campaign
        restaurant_id = uuid4()
        campaign_data = {
            'name': 'Test Campaign',
            'restaurant_id': restaurant_id,
            'status': 'draft',
            'recipient_count': len(processed_data['recipients'])
        }
        
        campaign = await campaign_repo.create_campaign(campaign_data)
        assert campaign is not None
        assert campaign['name'] == 'Test Campaign'
        assert campaign['status'] == 'draft'
        
        # Step 4: Store recipients
        recipients_created = await campaign_repo.bulk_create_recipients(
            campaign['id'],
            processed_data['recipients']
        )
        assert recipients_created == 5
        
        # Step 5: Verify recipients are stored correctly
        stored_recipients = await campaign_repo.get_campaign_recipients(
            UUID(campaign['id'])
        )
        assert len(stored_recipients) == 5
        
        # Verify phone number formatting
        stored_phones = {r['phone_number'] for r in stored_recipients}
        expected_phones = {
            '+966501234567',
            '+966502345678',
            '+966503456789',
            '+966504567890',
            '+966505678901'
        }
        assert stored_phones == expected_phones
    
    @pytest.mark.asyncio
    async def test_campaign_scheduling_flow(
        self,
        feedback_scheduler,
        campaign_repo,
        sample_csv_data,
        csv_processor
    ):
        """Test campaign scheduling with prayer time awareness"""
        
        # Setup campaign with recipients
        restaurant_id = uuid4()
        campaign_data = {
            'name': 'Scheduling Test Campaign',
            'restaurant_id': restaurant_id,
            'status': 'draft'
        }
        
        campaign = await campaign_repo.create_campaign(campaign_data)
        processed_data = csv_processor.process_recipients(sample_csv_data)
        
        await campaign_repo.bulk_create_recipients(
            campaign['id'],
            processed_data['recipients']
        )
        
        # Schedule campaign
        schedule_params = {
            'start_time': datetime.now() + timedelta(hours=1),
            'end_time': datetime.now() + timedelta(days=7),
            'template': 'default'
        }
        
        scheduled_jobs = await feedback_scheduler.schedule_campaign(
            UUID(campaign['id']),
            schedule_params
        )
        
        assert len(scheduled_jobs) == 5  # One job per recipient
        
        for job in scheduled_jobs:
            assert 'message_id' in job
            assert 'task_id' in job
            assert 'scheduled_time' in job
            assert 'phone_number' in job
        
        # Verify messages are created with correct status
        messages = await campaign_repo.get_campaign_messages(
            UUID(campaign['id'])
        )
        assert len(messages) == 5
        
        for message in messages:
            assert message['status'] == 'scheduled'
            assert message['message_template'] == 'default'
    
    @pytest.mark.asyncio
    async def test_feedback_processing_with_alerts(
        self,
        alert_service,
        campaign_repo
    ):
        """Test feedback processing and alert generation"""
        
        # Create test feedback scenarios
        feedback_scenarios = [
            {
                'rating': 1,
                'sentiment_score': -0.8,
                'message': 'الطعام كان سيء جداً والخدمة بطيئة',
                'topics': ['طعام', 'خدمة'],
                'expected_alerts': 2  # Low rating + negative sentiment
            },
            {
                'rating': 5,
                'sentiment_score': 0.9,
                'message': 'تجربة رائعة! الطعام ممتاز والخدمة سريعة',
                'topics': ['طعام', 'خدمة'],
                'expected_alerts': 0  # Positive feedback
            },
            {
                'rating': 2,
                'sentiment_score': -0.6,
                'message': 'مشكلة في جودة الطعام، البرجر نيء',
                'topics': ['food quality'],
                'expected_alerts': 2  # Low rating + food quality issue
            }
        ]
        
        for i, scenario in enumerate(feedback_scenarios):
            feedback_data = {
                'id': str(uuid4()),
                'restaurant_id': str(uuid4()),
                'conversation_id': str(uuid4()),
                'customer_phone': f'+96650123456{i}',
                **scenario
            }
            
            # Process feedback for alerts
            alerts = await alert_service.process_feedback_for_alerts(feedback_data)
            
            assert len(alerts) == scenario['expected_alerts']
            
            if scenario['expected_alerts'] > 0:
                # Verify alert properties
                for alert in alerts:
                    assert alert['restaurant_id'] == feedback_data['restaurant_id']
                    assert alert['priority'] in ['immediate', 'high', 'medium', 'low']
                    assert alert['status'] == 'pending'
                    assert 'title' in alert
                    assert 'details' in alert
    
    @pytest.mark.asyncio
    async def test_campaign_metrics_calculation(
        self,
        campaign_repo,
        csv_processor,
        sample_csv_data
    ):
        """Test campaign metrics calculation"""
        
        # Setup campaign
        restaurant_id = uuid4()
        campaign_data = {
            'name': 'Metrics Test Campaign',
            'restaurant_id': restaurant_id,
            'status': 'active'
        }
        
        campaign = await campaign_repo.create_campaign(campaign_data)
        processed_data = csv_processor.process_recipients(sample_csv_data)
        
        await campaign_repo.bulk_create_recipients(
            campaign['id'],
            processed_data['recipients']
        )
        
        # Create some campaign messages
        campaign_id = UUID(campaign['id'])
        
        for i in range(3):  # 3 out of 5 messages sent
            message_data = {
                'campaign_id': campaign['id'],
                'recipient_id': str(uuid4()),
                'phone_number': f'+96650123456{i}',
                'status': 'sent',
                'message_template': 'default'
            }
            await campaign_repo.create_campaign_message(message_data)
        
        # Simulate some responses
        for i in range(2):  # 2 out of 3 responded
            recipient_id = uuid4()
            await campaign_repo.update_recipient_status(
                recipient_id,
                'responded',
                uuid4()
            )
        
        # Calculate metrics
        metrics = await campaign_repo.get_campaign_metrics(campaign_id)
        
        assert metrics['campaign_id'] == str(campaign_id)
        assert metrics['total_recipients'] == 5
        assert metrics['messages_sent'] >= 2  # At least 2 responses
        assert metrics['response_rate'] >= 0  # Should be calculated
        assert 'completion_rate' in metrics
        assert 'sentiment_distribution' in metrics
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_csv(self, csv_processor):
        """Test error handling for invalid CSV data"""
        
        # Test missing required columns
        invalid_csv = pd.DataFrame({
            'phone_number': ['0501234567'],
            # Missing visit_timestamp
        })
        
        result = csv_processor.validate_csv(invalid_csv)
        assert result['valid'] is False
        assert 'Missing required columns' in result['errors'][0]
        
        # Test empty CSV
        empty_csv = pd.DataFrame({
            'phone_number': [],
            'visit_timestamp': []
        })
        
        result = csv_processor.validate_csv(empty_csv)
        assert result['valid'] is False
        assert 'no data rows' in result['errors'][0]
        
        # Test CSV too large
        large_data = {
            'phone_number': [f'05012345{i:02d}' for i in range(10001)],
            'visit_timestamp': ['2025-01-08 14:30:00'] * 10001
        }
        large_csv = pd.DataFrame(large_data)
        
        result = csv_processor.validate_csv(large_csv)
        assert result['valid'] is False
        assert 'exceeds maximum row limit' in result['errors'][0]
    
    @pytest.mark.asyncio
    async def test_phone_number_validation_edge_cases(self, csv_processor):
        """Test phone number validation edge cases"""
        
        test_cases = [
            # Valid Saudi numbers
            ('0501234567', '+966501234567'),
            ('+966501234567', '+966501234567'),
            ('966501234567', '+966501234567'),
            ('501234567', '+966501234567'),
            
            # Invalid numbers
            ('123', None),
            ('', None),
            ('invalid', None),
            ('+1234567890', None),  # US number
            
            # Edge cases
            ('05 0123 4567', '+966501234567'),  # With spaces
            ('050-123-4567', '+966501234567'),  # With dashes
        ]
        
        for input_phone, expected in test_cases:
            result = csv_processor.validate_phone_number(input_phone)
            assert result == expected, f"Failed for {input_phone}: got {result}, expected {expected}"
    
    @pytest.mark.asyncio
    async def test_concurrent_campaign_processing(
        self,
        csv_processor,
        campaign_repo
    ):
        """Test handling multiple campaigns concurrently"""
        
        restaurant_id = uuid4()
        campaigns = []
        
        # Create multiple campaigns concurrently
        tasks = []
        for i in range(3):
            campaign_data = {
                'name': f'Concurrent Campaign {i+1}',
                'restaurant_id': restaurant_id,
                'status': 'draft'
            }
            task = campaign_repo.create_campaign(campaign_data)
            tasks.append(task)
        
        campaigns = await asyncio.gather(*tasks)
        
        # Verify all campaigns were created
        assert len(campaigns) == 3
        for i, campaign in enumerate(campaigns):
            assert campaign['name'] == f'Concurrent Campaign {i+1}'
            assert campaign['restaurant_id'] == restaurant_id
        
        # Verify campaigns can be retrieved
        all_campaigns = await campaign_repo.list_campaigns(
            filters={'restaurant_id': restaurant_id},
            limit=10
        )
        
        assert len(all_campaigns) >= 3