"""
Unit tests for CSV processor
"""

import pytest
import pandas as pd
import io
from datetime import datetime, timedelta

from src.services.csv_processor import CSVProcessor


class TestCSVProcessor:
    
    def setup_method(self):
        self.processor = CSVProcessor()
    
    def test_validate_csv_success(self):
        """Test successful CSV validation"""
        df = pd.DataFrame({
            'phone_number': ['0501234567', '0502345678'],
            'visit_timestamp': ['2025-01-08 14:30:00', '2025-01-08 15:45:00']
        })
        
        result = self.processor.validate_csv(df)
        
        assert result['valid'] is True
        assert result['row_count'] == 2
        assert 'warnings' in result
    
    def test_validate_csv_missing_columns(self):
        """Test validation fails with missing columns"""
        df = pd.DataFrame({
            'phone_number': ['0501234567']
        })
        
        result = self.processor.validate_csv(df)
        
        assert result['valid'] is False
        assert 'Missing required columns' in result['errors'][0]
    
    def test_validate_csv_empty_file(self):
        """Test validation fails with empty file"""
        df = pd.DataFrame({
            'phone_number': [],
            'visit_timestamp': []
        })
        
        result = self.processor.validate_csv(df)
        
        assert result['valid'] is False
        assert 'no data rows' in result['errors'][0]
    
    def test_validate_csv_too_many_rows(self):
        """Test validation fails with too many rows"""
        large_data = {
            'phone_number': [f'05012345{i:02d}' for i in range(10001)],
            'visit_timestamp': ['2025-01-08 14:30:00'] * 10001
        }
        df = pd.DataFrame(large_data)
        
        result = self.processor.validate_csv(df)
        
        assert result['valid'] is False
        assert 'exceeds maximum row limit' in result['errors'][0]
    
    def test_validate_phone_number_saudi_local(self):
        """Test Saudi local number formatting"""
        phone = '0501234567'
        result = self.processor.validate_phone_number(phone)
        
        assert result == '+966501234567'
    
    def test_validate_phone_number_saudi_without_leading_zero(self):
        """Test Saudi number without leading zero"""
        phone = '501234567'
        result = self.processor.validate_phone_number(phone)
        
        assert result == '+966501234567'
    
    def test_validate_phone_number_international(self):
        """Test international format"""
        phone = '+966501234567'
        result = self.processor.validate_phone_number(phone)
        
        assert result == '+966501234567'
    
    def test_validate_phone_number_country_code_only(self):
        """Test number with country code but no +"""
        phone = '966501234567'
        result = self.processor.validate_phone_number(phone)
        
        assert result == '+966501234567'
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone number"""
        phone = '123'
        result = self.processor.validate_phone_number(phone)
        
        assert result is None
    
    def test_validate_phone_number_empty(self):
        """Test empty phone number"""
        result = self.processor.validate_phone_number('')
        
        assert result is None
    
    def test_process_recipients_success(self):
        """Test successful recipient processing"""
        df = pd.DataFrame({
            'phone_number': ['0501234567', '0502345678', '966503456789'],
            'visit_timestamp': [
                '2025-01-08 14:30:00',
                '2025-01-08 15:45:00',
                '2025-01-08 19:20:00'
            ],
            'customer_name': ['Ahmad Ali', 'Fatima Hassan', 'Mohammed Salem'],
            'table_number': ['5', '12', '8']
        })
        
        result = self.processor.process_recipients(df)
        
        assert result['valid_count'] == 3
        assert result['duplicates_count'] == 0
        assert result['invalid_count'] == 0
        assert len(result['recipients']) == 3
        
        # Check first recipient
        recipient = result['recipients'][0]
        assert recipient['phone_number'] == '+966501234567'
        assert 'customer_name' in recipient['metadata']
        assert recipient['metadata']['customer_name'] == 'Ahmad Ali'
    
    def test_process_recipients_with_duplicates(self):
        """Test processing with duplicate phone numbers"""
        df = pd.DataFrame({
            'phone_number': ['0501234567', '0501234567', '0502345678'],
            'visit_timestamp': [
                '2025-01-08 14:30:00',
                '2025-01-08 15:45:00',
                '2025-01-08 19:20:00'
            ]
        })
        
        result = self.processor.process_recipients(df)
        
        assert result['valid_count'] == 2
        assert result['duplicates_count'] == 1
        assert result['invalid_count'] == 0
        assert len(result['recipients']) == 2
    
    def test_process_recipients_with_invalid_numbers(self):
        """Test processing with invalid phone numbers"""
        df = pd.DataFrame({
            'phone_number': ['0501234567', 'invalid', '123'],
            'visit_timestamp': [
                '2025-01-08 14:30:00',
                '2025-01-08 15:45:00',
                '2025-01-08 19:20:00'
            ]
        })
        
        result = self.processor.process_recipients(df)
        
        assert result['valid_count'] == 1
        assert result['duplicates_count'] == 0
        assert result['invalid_count'] == 2
        assert len(result['recipients']) == 1
    
    def test_generate_warnings_future_timestamps(self):
        """Test warning generation for future timestamps"""
        future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        df = pd.DataFrame({
            'phone_number': ['0501234567'],
            'visit_timestamp': [future_date]
        })
        
        result = self.processor.process_recipients(df)
        
        assert any('future timestamps' in warning for warning in result.get('warnings', []))
    
    def test_generate_warnings_old_timestamps(self):
        """Test warning generation for old timestamps"""
        old_date = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d %H:%M:%S')
        df = pd.DataFrame({
            'phone_number': ['0501234567'],
            'visit_timestamp': [old_date]
        })
        
        result = self.processor.process_recipients(df)
        
        assert any('older than 30 days' in warning for warning in result.get('warnings', []))
    
    def test_generate_warnings_low_success_rate(self):
        """Test warning generation for low success rate"""
        df = pd.DataFrame({
            'phone_number': ['invalid1', 'invalid2', 'invalid3', '0501234567'],
            'visit_timestamp': [
                '2025-01-08 14:30:00',
                '2025-01-08 15:45:00',
                '2025-01-08 19:20:00',
                '2025-01-08 20:30:00'
            ]
        })
        
        result = self.processor.process_recipients(df)
        
        # Only 1 out of 4 is valid (25% success rate < 80%)
        assert any('Low success rate' in warning for warning in result.get('warnings', []))
    
    def test_generate_sample_csv(self):
        """Test sample CSV generation"""
        sample_csv = self.processor.generate_sample_csv()
        
        assert 'phone_number' in sample_csv
        assert 'visit_timestamp' in sample_csv
        assert '0501234567' in sample_csv
        assert '2025-01-08' in sample_csv
    
    @pytest.mark.parametrize("phone,expected", [
        ('0501234567', '+966501234567'),
        ('+966501234567', '+966501234567'),
        ('966501234567', '+966501234567'),
        ('501234567', '+966501234567'),
        ('1234567890', None),  # US number should be invalid for Saudi
        ('', None),
        (None, None),
        ('invalid', None),
        # Additional edge cases
        ('+1555123456', None),  # US number with country code
        ('+44201234567', None),  # UK number
        ('00966501234567', None),  # International prefix (not supported)
        ('966-50-123-4567', '+966501234567'),  # With dashes
        ('966 50 123 4567', '+966501234567'),  # With spaces
        ('(966) 501234567', '+966501234567'),  # With parentheses
        ('966.501.234.567', '+966501234567'),  # With dots
        ('+966 50 123 4567', '+966501234567'),  # International format with spaces
        ('966123456789', None),  # Saudi country code but invalid mobile format
        ('966501234', None),  # Too short
        ('9665012345678', None),  # Too long
        ('966401234567', None),  # Invalid Saudi mobile prefix (40 instead of 50-59)
        ('966601234567', None),  # Invalid Saudi mobile prefix (60 instead of 50-59)
        ('+966051234567', '+966501234567'),  # Saudi landline converted to mobile format (not ideal but handled)
    ])
    def test_validate_phone_number_parametrized(self, phone, expected):
        """Parametrized test for phone number validation including edge cases"""
        result = self.processor.validate_phone_number(phone)
        assert result == expected