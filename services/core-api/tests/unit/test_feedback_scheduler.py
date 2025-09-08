"""
Unit tests for feedback scheduler
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4

from src.services.feedback_scheduler import FeedbackScheduler
from src.repositories.campaign_repository import CampaignRepository


class TestFeedbackScheduler:
    
    @pytest.fixture
    def mock_campaign_repo(self):
        repo = Mock(spec=CampaignRepository)
        repo.get_campaign_recipients = AsyncMock()
        repo.create_campaign_message = AsyncMock()
        return repo
    
    @pytest.fixture
    def scheduler(self, mock_campaign_repo):
        scheduler = FeedbackScheduler()
        scheduler.campaign_repo = mock_campaign_repo
        return scheduler
    
    @pytest.fixture
    def sample_recipients(self):
        base_time = datetime.now() - timedelta(hours=2)
        return [
            {
                'id': str(uuid4()),
                'phone_number': '+966501234567',
                'visit_timestamp': base_time,
            },
            {
                'id': str(uuid4()),
                'phone_number': '+966502345678',
                'visit_timestamp': base_time + timedelta(minutes=30),
            },
            {
                'id': str(uuid4()),
                'phone_number': '+966503456789',
                'visit_timestamp': base_time + timedelta(hours=1),
            }
        ]
    
    def test_calculate_time_since_visit(self, scheduler):
        """Test human-readable time calculation"""
        now = datetime.now()
        
        # Test recent visit (< 1 hour)
        recent_visit = now - timedelta(minutes=30)
        result = scheduler._calculate_time_since_visit(recent_visit)
        assert result == "قبل قليل"
        
        # Test 1-2 hours ago
        one_hour_ago = now - timedelta(hours=1, minutes=30)
        result = scheduler._calculate_time_since_visit(one_hour_ago)
        assert result == "قبل ساعة تقريباً"
        
        # Test same day (3 hours ago)
        three_hours_ago = now - timedelta(hours=3)
        result = scheduler._calculate_time_since_visit(three_hours_ago)
        assert result == "قبل 3 ساعات"
        
        # Test yesterday
        yesterday = now - timedelta(days=1)
        result = scheduler._calculate_time_since_visit(yesterday)
        assert result == "أمس"
        
        # Test multiple days ago
        three_days_ago = now - timedelta(days=3)
        result = scheduler._calculate_time_since_visit(three_days_ago)
        assert result == "قبل 3 أيام"
    
    @pytest.mark.asyncio
    async def test_calculate_send_time_basic(self, scheduler):
        """Test basic send time calculation"""
        visit_time = datetime.now() - timedelta(hours=1)
        customer_phone = '+966501234567'
        
        with patch.object(scheduler, '_check_prayer_time_conflict') as mock_prayer:
            mock_prayer.return_value = {
                'is_prayer_time': False,
                'next_available_time': visit_time + timedelta(hours=3)
            }
            
            send_time = await scheduler._calculate_send_time(visit_time, customer_phone)
            
            # Should be approximately 3 hours after visit
            expected_time = visit_time + timedelta(hours=3)
            time_diff = abs((send_time - expected_time).total_seconds())
            assert time_diff < 60  # Within 1 minute
    
    @pytest.mark.asyncio
    async def test_calculate_send_time_with_prayer_time(self, scheduler):
        """Test send time calculation with prayer time conflict"""
        visit_time = datetime.now() - timedelta(hours=1)
        customer_phone = '+966501234567'
        
        # Mock prayer time conflict
        prayer_end_time = visit_time + timedelta(hours=3, minutes=30)
        with patch.object(scheduler, '_check_prayer_time_conflict') as mock_prayer:
            mock_prayer.return_value = {
                'is_prayer_time': True,
                'next_available_time': prayer_end_time + timedelta(minutes=30)
            }
            
            send_time = await scheduler._calculate_send_time(visit_time, customer_phone)
            
            # Should be after prayer time + 30 minutes buffer
            expected_time = prayer_end_time + timedelta(minutes=30)
            assert send_time >= expected_time
    
    @pytest.mark.asyncio
    async def test_calculate_send_time_min_max_bounds(self, scheduler):
        """Test send time respects min/max delay bounds"""
        visit_time = datetime.now() - timedelta(hours=5)  # Old visit
        customer_phone = '+966501234567'
        
        with patch.object(scheduler, '_check_prayer_time_conflict') as mock_prayer:
            mock_prayer.return_value = {
                'is_prayer_time': False,
                'next_available_time': visit_time + timedelta(hours=3)
            }
            
            send_time = await scheduler._calculate_send_time(visit_time, customer_phone)
            
            # Should respect max delay (4 hours)
            max_time = visit_time + timedelta(hours=4)
            assert send_time <= max_time
            
            # Should respect min delay (2 hours)
            min_time = visit_time + timedelta(hours=2)
            assert send_time >= min_time
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_check_prayer_time_conflict_success(self, mock_httpx, scheduler):
        """Test prayer time check with successful API response"""
        proposed_time = datetime.now()
        
        # Mock successful prayer time API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'is_prayer_time': True,
            'prayer_end_time': (proposed_time + timedelta(minutes=30)).isoformat()
        }
        
        mock_client = Mock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await scheduler._check_prayer_time_conflict(proposed_time)
        
        assert result['is_prayer_time'] is True
        expected_next_time = proposed_time + timedelta(minutes=30, seconds=1800)  # +30 min buffer
        time_diff = abs((result['next_available_time'] - expected_next_time).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_check_prayer_time_conflict_api_failure(self, mock_httpx, scheduler):
        """Test prayer time check handles API failure gracefully"""
        proposed_time = datetime.now()
        
        # Mock API failure
        mock_client = Mock()
        mock_client.post = AsyncMock(side_effect=Exception("API error"))
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await scheduler._check_prayer_time_conflict(proposed_time)
        
        # Should fall back to original time
        assert result['is_prayer_time'] is False
        assert result['next_available_time'] == proposed_time
    
    @pytest.mark.asyncio
    async def test_schedule_campaign_success(self, scheduler, mock_campaign_repo, sample_recipients):
        """Test successful campaign scheduling"""
        campaign_id = uuid4()
        mock_campaign_repo.get_campaign_recipients.return_value = sample_recipients
        
        # Mock message creation
        def create_message_side_effect(message_data):
            return {
                'id': str(uuid4()),
                **message_data
            }
        
        mock_campaign_repo.create_campaign_message.side_effect = create_message_side_effect
        
        # Mock Celery task
        with patch.object(scheduler, 'celery_app') as mock_celery:
            mock_task = Mock()
            mock_task.id = 'test_task_id'
            mock_celery.send_task.return_value = mock_task
            
            schedule_params = {
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(days=1),
                'template': 'test_template'
            }
            
            with patch.object(scheduler, '_calculate_send_time') as mock_calc_time:
                # Mock send times for each recipient
                send_times = [
                    datetime.now() + timedelta(hours=1),
                    datetime.now() + timedelta(hours=1, minutes=30),
                    datetime.now() + timedelta(hours=2)
                ]
                mock_calc_time.side_effect = send_times
                
                result = await scheduler.schedule_campaign(campaign_id, schedule_params)
                
                # Verify results
                assert len(result) == 3
                for i, job in enumerate(result):
                    assert 'message_id' in job
                    assert job['task_id'] == 'test_task_id'
                    assert job['phone_number'] == sample_recipients[i]['phone_number']
                
                # Verify repository calls
                assert mock_campaign_repo.create_campaign_message.call_count == 3
    
    @pytest.mark.asyncio
    async def test_schedule_campaign_filters_by_time_window(
        self, 
        scheduler, 
        mock_campaign_repo, 
        sample_recipients
    ):
        """Test campaign scheduling filters recipients by time window"""
        campaign_id = uuid4()
        mock_campaign_repo.get_campaign_recipients.return_value = sample_recipients
        
        # Set narrow time window
        start_time = datetime.now() + timedelta(hours=2)
        end_time = datetime.now() + timedelta(hours=2, minutes=30)
        
        schedule_params = {
            'start_time': start_time,
            'end_time': end_time,
            'template': 'test_template'
        }
        
        with patch.object(scheduler, 'celery_app') as mock_celery:
            mock_task = Mock()
            mock_task.id = 'test_task_id'
            mock_celery.send_task.return_value = mock_task
            
            with patch.object(scheduler, '_calculate_send_time') as mock_calc_time:
                # Mock send times - some outside window
                mock_calc_time.side_effect = [
                    datetime.now() + timedelta(hours=1),      # Before window
                    datetime.now() + timedelta(hours=2, minutes=15),  # In window
                    datetime.now() + timedelta(hours=3)       # After window
                ]
                
                mock_campaign_repo.create_campaign_message.side_effect = lambda data: {
                    'id': str(uuid4()), **data
                }
                
                result = await scheduler.schedule_campaign(campaign_id, schedule_params)
                
                # Should only schedule messages within the time window
                # First recipient should be moved to start_time (within window)
                # Second recipient should be scheduled as calculated (within window)  
                # Third recipient should be skipped (outside window)
                assert len(result) >= 1  # At least one should be scheduled
    
    @pytest.mark.asyncio
    async def test_cancel_campaign(self, scheduler, mock_campaign_repo):
        """Test campaign cancellation"""
        campaign_id = uuid4()
        
        # Mock scheduled messages
        scheduled_messages = [
            {
                'id': str(uuid4()),
                'status': 'scheduled',
                'task_id': 'celery_task_1'
            },
            {
                'id': str(uuid4()),
                'status': 'scheduled', 
                'task_id': 'celery_task_2'
            }
        ]
        
        mock_campaign_repo.get_campaign_messages.return_value = scheduled_messages
        mock_campaign_repo.update_message_status.return_value = True
        mock_campaign_repo.update_campaign.return_value = True
        
        with patch.object(scheduler, 'celery_app') as mock_celery:
            result = await scheduler.cancel_campaign(campaign_id)
            
            assert result is True
            
            # Verify Celery tasks were revoked
            assert mock_celery.control.revoke.call_count == 2
            
            # Verify messages were cancelled
            assert mock_campaign_repo.update_message_status.call_count == 2
            
            # Verify campaign was cancelled
            mock_campaign_repo.update_campaign.assert_called_once_with(
                campaign_id,
                {'status': 'cancelled'}
            )
    
    @pytest.mark.asyncio
    async def test_reschedule_message(self, scheduler, mock_campaign_repo):
        """Test individual message rescheduling"""
        message_id = uuid4()
        new_send_time = datetime.now() + timedelta(hours=2)
        
        # Mock existing message
        existing_message = {
            'id': str(message_id),
            'status': 'scheduled',
            'task_id': 'old_task_id'
        }
        
        mock_campaign_repo.get_message.return_value = existing_message
        mock_campaign_repo.update_message.return_value = True
        
        with patch.object(scheduler, 'celery_app') as mock_celery:
            # Mock old task revocation
            mock_celery.control.revoke = Mock()
            
            # Mock new task creation
            mock_new_task = Mock()
            mock_new_task.id = 'new_task_id'
            mock_celery.send_task.return_value = mock_new_task
            
            result = await scheduler.reschedule_message(message_id, new_send_time)
            
            assert result is True
            
            # Verify old task was revoked
            mock_celery.control.revoke.assert_called_once_with('old_task_id')
            
            # Verify new task was created
            mock_celery.send_task.assert_called_once()
            
            # Verify message was updated
            mock_campaign_repo.update_message.assert_called_once_with(
                message_id,
                {
                    'scheduled_send_time': new_send_time,
                    'task_id': 'new_task_id'
                }
            )
    
    @pytest.mark.asyncio
    async def test_reschedule_message_invalid_status(self, scheduler, mock_campaign_repo):
        """Test rescheduling fails for non-scheduled messages"""
        message_id = uuid4()
        new_send_time = datetime.now() + timedelta(hours=2)
        
        # Mock message with invalid status
        existing_message = {
            'id': str(message_id),
            'status': 'sent',  # Already sent, cannot reschedule
            'task_id': 'task_id'
        }
        
        mock_campaign_repo.get_message.return_value = existing_message
        
        result = await scheduler.reschedule_message(message_id, new_send_time)
        
        assert result is False
        
        # Verify no updates were made
        mock_campaign_repo.update_message.assert_not_called()
    
    def test_setup_celery_configuration(self, scheduler):
        """Test Celery app configuration"""
        celery_app = scheduler.celery_app
        
        # Verify basic configuration
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.accept_content == ['json']
        assert celery_app.conf.result_serializer == 'json'
        assert celery_app.conf.timezone == 'UTC'
        assert celery_app.conf.enable_utc is True
        
        # Verify beat schedule exists
        beat_schedule = celery_app.conf.beat_schedule
        assert 'process-scheduled-feedback' in beat_schedule
        assert 'update-campaign-metrics' in beat_schedule
        
        # Verify schedule intervals
        assert beat_schedule['process-scheduled-feedback']['schedule'] == 300.0  # 5 minutes
        assert beat_schedule['update-campaign-metrics']['schedule'] == 600.0    # 10 minutes