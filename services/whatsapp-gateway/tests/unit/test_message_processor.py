import pytest
from unittest.mock import patch, MagicMock
from src.services.queue import process_incoming_message, process_status_update, get_queue_health

def test_process_text_message():
    message_data = {
        'id': 'msg_123',
        'from': '1234567890',
        'type': 'text',
        'text': {'body': 'Hello, world!'},
        'timestamp': '1234567890'
    }
    
    with patch('src.services.queue.logger') as mock_logger:
        task = MagicMock()
        task.request.retries = 0
        result = process_incoming_message.run(message_data)
        
        assert result['status'] == 'processed'
        assert result['message_id'] == 'msg_123'
        assert result['from'] == '1234567890'
        assert result['type'] == 'text'

def test_process_media_message():
    message_data = {
        'id': 'msg_456',
        'from': '0987654321',
        'type': 'image',
        'image': {
            'id': 'media_123',
            'mime_type': 'image/jpeg',
            'sha256': 'abc123'
        },
        'timestamp': '1234567890'
    }
    
    with patch('src.services.queue.logger') as mock_logger:
        task = MagicMock()
        task.request.retries = 0
        result = process_incoming_message.run(message_data)
        
        assert result['status'] == 'processed'
        assert result['message_id'] == 'msg_456'
        assert result['from'] == '0987654321'
        assert result['type'] == 'image'

def test_process_interactive_message():
    message_data = {
        'id': 'msg_789',
        'from': '5555555555',
        'type': 'interactive',
        'interactive': {
            'type': 'button_reply',
            'button_reply': {
                'id': 'btn_1',
                'title': 'Yes'
            }
        },
        'timestamp': '1234567890'
    }
    
    with patch('src.services.queue.logger') as mock_logger:
        task = MagicMock()
        task.request.retries = 0
        result = process_incoming_message.run(message_data)
        
        assert result['status'] == 'processed'
        assert result['message_id'] == 'msg_789'
        assert result['type'] == 'interactive'

def test_process_status_update():
    status_data = {
        'id': 'msg_123',
        'status': 'delivered',
        'timestamp': '1234567890',
        'recipient_id': '1234567890'
    }
    
    with patch('src.services.queue.logger') as mock_logger:
        task = MagicMock()
        task.request.retries = 0
        result = process_status_update.run(status_data)
        
        assert result['status'] == 'processed'
        assert result['message_id'] == 'msg_123'
        assert result['delivery_status'] == 'delivered'

def test_message_processing_with_retry():
    message_data = {
        'id': 'msg_error',
        'from': '1111111111',
        'type': 'unknown'
    }
    
    task = MagicMock()
    task.request.retries = 1
    task.retry = MagicMock(side_effect=Exception("Retry triggered"))
    
    with patch('src.services.queue.logger') as mock_logger:
        with patch.object(process_incoming_message, 'retry', task.retry):
            try:
                process_incoming_message.run(message_data)
            except Exception:
                pass

def test_get_queue_health():
    with patch('src.services.queue.celery_app.control.inspect') as mock_inspect:
        mock_instance = MagicMock()
        mock_instance.stats.return_value = {'worker1': {'status': 'ok'}}
        mock_instance.active.return_value = {'worker1': []}
        mock_instance.reserved.return_value = {'worker1': []}
        mock_inspect.return_value = mock_instance
        
        health = get_queue_health()
        
        assert health['status'] == 'healthy'
        assert 'stats' in health
        assert 'active_tasks' in health
        assert 'reserved_tasks' in health

def test_get_queue_health_error():
    with patch('src.services.queue.celery_app.control.inspect', side_effect=Exception("Connection error")):
        health = get_queue_health()
        
        assert health['status'] == 'error'
        assert 'error' in health