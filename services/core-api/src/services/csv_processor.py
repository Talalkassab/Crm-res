"""
CSV Processing Service
Handles validation and processing of customer data uploads
Optimized for large files with streaming processing
"""

import pandas as pd
import re
from typing import Dict, List, Any, Optional, Iterator, AsyncIterator
from datetime import datetime
import phonenumbers
from phonenumbers import NumberParseException
import asyncio
import io
import csv
from functools import lru_cache


class CSVProcessor:
    """Process and validate CSV uploads for feedback campaigns"""
    
    REQUIRED_COLUMNS = ['phone_number', 'visit_timestamp']
    MAX_ROWS = 10000
    SAUDI_COUNTRY_CODE = 'SA'
    CHUNK_SIZE = 1000  # Process in chunks for large files
    LARGE_FILE_THRESHOLD = 1024 * 1024  # 1MB threshold for streaming
    
    def __init__(self):
        # Cache for phone number validation to improve performance
        self._phone_cache = {}
        self._validation_pattern = re.compile(r'[^\d+]')
    
    def validate_csv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate CSV structure and content
        Returns validation result with any errors found
        """
        errors = []
        warnings = []
        
        # Check for required columns
        missing_columns = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            return {'valid': False, 'errors': errors}
        
        # Check row count
        if len(df) > self.MAX_ROWS:
            errors.append(f"CSV exceeds maximum row limit of {self.MAX_ROWS}")
            return {'valid': False, 'errors': errors}
        
        if len(df) == 0:
            errors.append("CSV file contains no data rows")
            return {'valid': False, 'errors': errors}
        
        # Check for empty values in required columns
        for col in self.REQUIRED_COLUMNS:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                warnings.append(f"Column '{col}' has {null_count} empty values")
        
        # Validate timestamp format
        try:
            pd.to_datetime(df['visit_timestamp'])
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid timestamp format in 'visit_timestamp' column: {str(e)}")
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        return {
            'valid': True,
            'warnings': warnings,
            'row_count': len(df)
        }
    
    @lru_cache(maxsize=10000)
    def validate_phone_number(self, phone: str) -> Optional[str]:
        """
        Validate and format phone number for WhatsApp
        Returns formatted number or None if invalid
        Uses LRU cache to improve performance for duplicate numbers
        """
        if not phone:
            return None
        
        # Fast pre-validation using compiled regex
        phone_str = str(phone).strip()
        
        # Remove common separators and formatting
        phone_str = re.sub(r'[\s\-\.\(\)]+', '', phone_str)
        
        # Handle international prefix format (00 instead of +)
        if phone_str.startswith('00'):
            phone_str = '+' + phone_str[2:]
        
        # Extract only digits and plus sign
        cleaned_phone = self._validation_pattern.sub('', phone_str)
        
        # Handle Saudi numbers
        if cleaned_phone.startswith('05'):  # Local Saudi format
            cleaned_phone = '+966' + cleaned_phone[1:]
        elif cleaned_phone.startswith('5') and len(cleaned_phone) == 9:  # Missing leading 0
            cleaned_phone = '+966' + cleaned_phone
        elif cleaned_phone.startswith('966'):  # Country code without +
            cleaned_phone = '+' + cleaned_phone
        elif not cleaned_phone.startswith('+'):  # Assume Saudi if no country code
            if len(cleaned_phone) == 10 and cleaned_phone[0] == '0':
                cleaned_phone = '+966' + cleaned_phone[1:]
            elif len(cleaned_phone) == 9:
                cleaned_phone = '+966' + cleaned_phone
        
        # Additional validation: Saudi numbers should be +966 followed by 9 digits
        if not (cleaned_phone.startswith('+966') and len(cleaned_phone) == 13):
            return None
            
        # Validate Saudi mobile number prefixes (should start with 5)
        if not cleaned_phone[4] == '5':  # Position after +966
            return None
        
        # Valid Saudi mobile prefixes: 50, 51, 52, 53, 54, 55, 56, 57, 58, 59
        mobile_prefix = cleaned_phone[4:6]  # Extract the two digits after +966
        valid_prefixes = ['50', '51', '52', '53', '54', '55', '56', '57', '58', '59']
        
        if mobile_prefix not in valid_prefixes:
            return None
        
        # Validate using phonenumbers library (cached result)
        try:
            parsed = phonenumbers.parse(cleaned_phone, None)
            if not phonenumbers.is_valid_number(parsed):
                return None
            
            # Ensure it's a Saudi number
            if parsed.country_code != 966:
                return None
            
            # Format in international format for WhatsApp
            formatted = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
            return formatted
            
        except NumberParseException:
            return None
    
    def process_recipients(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process CSV data and prepare recipient list
        Returns processed data with statistics
        """
        recipients = []
        seen_numbers = set()
        duplicates_count = 0
        invalid_count = 0
        
        # Convert timestamps
        df['visit_timestamp'] = pd.to_datetime(df['visit_timestamp'])
        
        for _, row in df.iterrows():
            # Validate and format phone number
            formatted_number = self.validate_phone_number(row['phone_number'])
            
            if not formatted_number:
                invalid_count += 1
                continue
            
            # Check for duplicates within campaign
            if formatted_number in seen_numbers:
                duplicates_count += 1
                continue
            
            seen_numbers.add(formatted_number)
            
            # Prepare recipient data
            recipient = {
                'phone_number': formatted_number,
                'visit_timestamp': row['visit_timestamp'].isoformat(),
                'metadata': {}
            }
            
            # Add any additional columns as metadata
            extra_columns = set(df.columns) - set(self.REQUIRED_COLUMNS)
            for col in extra_columns:
                if pd.notna(row[col]):
                    recipient['metadata'][col] = str(row[col])
            
            recipients.append(recipient)
        
        return {
            'recipients': recipients,
            'total_rows': len(df),
            'valid_count': len(recipients),
            'duplicates_count': duplicates_count,
            'invalid_count': invalid_count,
            'warnings': self._generate_warnings(df, recipients)
        }
    
    def _generate_warnings(self, df: pd.DataFrame, recipients: List[Dict]) -> List[str]:
        """Generate processing warnings"""
        warnings = []
        
        # Check for future timestamps
        now = datetime.now()
        future_visits = df[pd.to_datetime(df['visit_timestamp']) > now]
        if not future_visits.empty:
            warnings.append(f"{len(future_visits)} visits have future timestamps")
        
        # Check for very old timestamps (> 30 days)
        old_threshold = pd.Timestamp.now() - pd.Timedelta(days=30)
        old_visits = df[pd.to_datetime(df['visit_timestamp']) < old_threshold]
        if not old_visits.empty:
            warnings.append(f"{len(old_visits)} visits are older than 30 days")
        
        # Check success rate
        success_rate = len(recipients) / len(df) * 100 if len(df) > 0 else 0
        if success_rate < 80:
            warnings.append(f"Low success rate: {success_rate:.1f}% of rows were valid")
        
        return warnings
    
    def generate_sample_csv(self) -> str:
        """Generate a sample CSV template"""
        sample_data = {
            'phone_number': [
                '0501234567',
                '+966502345678',
                '966503456789'
            ],
            'visit_timestamp': [
                '2025-01-08 14:30:00',
                '2025-01-08 15:45:00',
                '2025-01-08 19:20:00'
            ],
            'customer_name': [
                'Ahmad Ali',
                'Fatima Hassan',
                'Mohammed Salem'
            ],
            'table_number': [
                '5',
                '12',
                '8'
            ]
        }
        
        df = pd.DataFrame(sample_data)
        return df.to_csv(index=False)
    
    async def validate_csv_streaming(self, file_content: bytes) -> Dict[str, Any]:
        """
        Validate CSV structure without loading entire file into memory
        Returns validation result for streaming processing decision
        """
        try:
            # Read just the first few lines to validate structure
            text_content = file_content[:4096].decode('utf-8', errors='ignore')
            lines = text_content.split('\n')
            
            if len(lines) < 2:
                return {'valid': False, 'errors': ['File appears to be empty']}
            
            # Parse header
            header = lines[0].strip()
            if not header:
                return {'valid': False, 'errors': ['Missing header row']}
            
            # Check for required columns
            header_cols = [col.strip().lower() for col in header.split(',')]
            required_cols = [col.lower() for col in self.REQUIRED_COLUMNS]
            missing_columns = set(required_cols) - set(header_cols)
            
            if missing_columns:
                return {
                    'valid': False, 
                    'errors': [f"Missing required columns: {', '.join(missing_columns)}"]
                }
            
            # Estimate row count (rough approximation)
            avg_line_length = len(file_content) / max(len(lines), 1)
            estimated_rows = len(file_content) / max(avg_line_length, 50) - 1  # -1 for header
            
            if estimated_rows > self.MAX_ROWS:
                return {
                    'valid': False,
                    'errors': [f'File appears to exceed maximum row limit of {self.MAX_ROWS}']
                }
            
            return {
                'valid': True,
                'estimated_rows': int(estimated_rows),
                'requires_streaming': len(file_content) > self.LARGE_FILE_THRESHOLD,
                'columns': header_cols
            }
            
        except UnicodeDecodeError:
            return {'valid': False, 'errors': ['File encoding not supported. Please use UTF-8']}
        except Exception as e:
            return {'valid': False, 'errors': [f'File validation error: {str(e)}']}
    
    async def process_recipients_streaming(
        self, 
        file_content: bytes,
        progress_callback: Optional[callable] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process CSV data using streaming approach for large files
        Yields progress updates and final results
        """
        recipients = []
        seen_numbers = set()
        duplicates_count = 0
        invalid_count = 0
        total_processed = 0
        
        try:
            # Decode content and create CSV reader
            text_content = file_content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(text_content))
            
            # Get column names and validate
            fieldnames = csv_reader.fieldnames
            if not fieldnames:
                yield {
                    'type': 'error',
                    'message': 'No columns found in CSV file'
                }
                return
            
            # Convert to lowercase for matching
            fieldnames_lower = [name.lower().strip() for name in fieldnames]
            required_lower = [col.lower() for col in self.REQUIRED_COLUMNS]
            
            # Find column indices
            try:
                phone_idx = fieldnames_lower.index('phone_number')
                timestamp_idx = fieldnames_lower.index('visit_timestamp')
                phone_col = fieldnames[phone_idx]
                timestamp_col = fieldnames[timestamp_idx]
            except ValueError as e:
                yield {
                    'type': 'error',
                    'message': f'Required column not found: {str(e)}'
                }
                return
            
            # Process rows in chunks
            current_chunk = []
            
            for row in csv_reader:
                total_processed += 1
                
                # Add to current chunk
                current_chunk.append(row)
                
                # Process chunk when it reaches CHUNK_SIZE
                if len(current_chunk) >= self.CHUNK_SIZE:
                    chunk_results = await self._process_chunk(
                        current_chunk, 
                        phone_col, 
                        timestamp_col, 
                        seen_numbers
                    )
                    
                    # Update counters
                    recipients.extend(chunk_results['recipients'])
                    duplicates_count += chunk_results['duplicates']
                    invalid_count += chunk_results['invalid']
                    
                    # Send progress update
                    if progress_callback:
                        progress_info = {
                            'type': 'progress',
                            'processed': total_processed,
                            'valid': len(recipients),
                            'duplicates': duplicates_count,
                            'invalid': invalid_count,
                            'percentage': min(95, (total_processed / max(1, len(text_content.split('\n')) - 1)) * 100)
                        }
                        yield progress_info
                    
                    # Clear chunk
                    current_chunk = []
                    
                    # Allow other tasks to run
                    await asyncio.sleep(0.001)
            
            # Process remaining chunk
            if current_chunk:
                chunk_results = await self._process_chunk(
                    current_chunk, 
                    phone_col, 
                    timestamp_col, 
                    seen_numbers
                )
                recipients.extend(chunk_results['recipients'])
                duplicates_count += chunk_results['duplicates']
                invalid_count += chunk_results['invalid']
            
            # Generate warnings
            warnings = self._generate_warnings_from_recipients(recipients, total_processed)
            
            # Final result
            yield {
                'type': 'completed',
                'recipients': recipients,
                'total_rows': total_processed,
                'valid_count': len(recipients),
                'duplicates_count': duplicates_count,
                'invalid_count': invalid_count,
                'warnings': warnings
            }
            
        except UnicodeDecodeError:
            yield {
                'type': 'error',
                'message': 'File encoding not supported. Please use UTF-8 encoding.'
            }
        except Exception as e:
            yield {
                'type': 'error',
                'message': f'Processing error: {str(e)}'
            }
    
    async def _process_chunk(
        self, 
        chunk: List[Dict], 
        phone_col: str, 
        timestamp_col: str,
        seen_numbers: set
    ) -> Dict[str, Any]:
        """Process a chunk of CSV rows"""
        chunk_recipients = []
        chunk_duplicates = 0
        chunk_invalid = 0
        
        for row in chunk:
            try:
                # Validate and format phone number
                raw_phone = row.get(phone_col, '').strip()
                if not raw_phone:
                    chunk_invalid += 1
                    continue
                
                formatted_number = self.validate_phone_number(raw_phone)
                
                if not formatted_number:
                    chunk_invalid += 1
                    continue
                
                # Check for duplicates within campaign
                if formatted_number in seen_numbers:
                    chunk_duplicates += 1
                    continue
                
                seen_numbers.add(formatted_number)
                
                # Validate timestamp
                raw_timestamp = row.get(timestamp_col, '').strip()
                if not raw_timestamp:
                    chunk_invalid += 1
                    continue
                
                try:
                    # Parse timestamp
                    visit_timestamp = pd.to_datetime(raw_timestamp)
                except (ValueError, pd.errors.ParserError):
                    chunk_invalid += 1
                    continue
                
                # Prepare recipient data
                recipient = {
                    'phone_number': formatted_number,
                    'visit_timestamp': visit_timestamp.isoformat(),
                    'metadata': {}
                }
                
                # Add any additional columns as metadata
                extra_columns = set(row.keys()) - {phone_col, timestamp_col}
                for col in extra_columns:
                    value = row.get(col, '').strip()
                    if value:
                        recipient['metadata'][col] = value
                
                chunk_recipients.append(recipient)
                
            except Exception as e:
                # Skip problematic rows but continue processing
                chunk_invalid += 1
                continue
        
        return {
            'recipients': chunk_recipients,
            'duplicates': chunk_duplicates,
            'invalid': chunk_invalid
        }
    
    def _generate_warnings_from_recipients(self, recipients: List[Dict], total_rows: int) -> List[str]:
        """Generate warnings from processed recipients"""
        warnings = []
        
        if not recipients:
            return warnings
        
        # Check for future timestamps
        now = datetime.now()
        future_count = 0
        old_count = 0
        old_threshold = now - pd.Timedelta(days=30)
        
        for recipient in recipients:
            try:
                visit_time = pd.to_datetime(recipient['visit_timestamp'])
                if visit_time > now:
                    future_count += 1
                elif visit_time < old_threshold:
                    old_count += 1
            except:
                continue
        
        if future_count > 0:
            warnings.append(f"{future_count} visits have future timestamps")
        
        if old_count > 0:
            warnings.append(f"{old_count} visits are older than 30 days")
        
        # Check success rate
        if total_rows > 0:
            success_rate = len(recipients) / total_rows * 100
            if success_rate < 80:
                warnings.append(f"Low success rate: {success_rate:.1f}% of rows were valid")
        
        return warnings
    
    async def should_use_streaming(self, file_size: int) -> bool:
        """Determine if streaming processing should be used"""
        return file_size > self.LARGE_FILE_THRESHOLD