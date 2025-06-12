# core/email_processor.py
"""
Email Processor - Advanced Email Processing Engine
Handles email loading, validation, processing, and sending operations
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class EmailData:
    """Email data structure"""
    address: str
    status: str = "pending"  # pending, sent, failed, invalid
    validation_score: float = 0.0
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class ProcessingResult:
    """Result of email processing operation"""
    success: bool
    message: str
    processed_count: int = 0
    valid_emails: int = 0
    invalid_emails: int = 0
    duplicates_removed: int = 0
    details: Dict[str, Any] = None

@dataclass
class SendingResult:
    """Result of email sending operation"""
    success: bool
    message: str
    sent_count: int = 0
    failed_count: int = 0
    failed_emails: List[str] = None
    warnings: List[str] = None

class EmailProcessor:
    """Advanced email processing engine with comprehensive functionality"""
    
    def __init__(self, outlook_manager, validation_engine, file_manager, config_manager):
        self.outlook_manager = outlook_manager
        self.validation_engine = validation_engine
        self.file_manager = file_manager
        self.config_manager = config_manager
        
        # Email data storage
        self.email_list = []
        self.processing_stats = {
            'total_loaded': 0,
            'valid_emails': 0,
            'invalid_emails': 0,
            'duplicates_removed': 0,
            'sent_emails': 0,
            'failed_emails': 0,
            'last_processed': None
        }
        
        # Processing state
        self.is_processing = False
        self.processing_progress = 0.0
        self.processing_message = ""
        
        # Cache management
        self.email_cache = {}
        self.validation_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Thread management
        self.processing_lock = threading.Lock()
        self.background_tasks = []
        
        # Batch processing settings
        self.batch_size = 1000
        self.validation_timeout = 30
        
    def initialize(self):
        """Initialize email processor"""
        try:
            logger.info("Initializing email processor")
            
            # Load cached data if available
            self._load_cache()
            
            # Setup background validation if enabled
            if self.config_manager.get_validation_settings().check_mx_records:
                self._start_background_validation()
            
            logger.info("Email processor initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize email processor: {e}")
            return False
    
    def load_emails_from_file(self, file_path: str, column_name: str = None) -> ProcessingResult:
        """Load emails from various file formats with advanced processing"""
        
        if not Path(file_path).exists():
            return ProcessingResult(
                success=False,
                message=f"File not found: {file_path}"
            )
        
        logger.info(f"Loading emails from: {file_path}")
        
        try:
            with self.processing_lock:
                self.is_processing = True
                self.processing_progress = 0.0
                self.processing_message = "Loading file..."
            
            # Determine file type and load accordingly
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension in ['.xlsx', '.xls']:
                raw_emails = self._load_from_excel(file_path, column_name)
            elif file_extension == '.csv':
                raw_emails = self._load_from_csv(file_path, column_name)
            elif file_extension == '.txt':
                raw_emails = self._load_from_text(file_path)
            elif file_extension == '.json':
                raw_emails = self._load_from_json(file_path)
            else:
                return ProcessingResult(
                    success=False,
                    message=f"Unsupported file format: {file_extension}"
                )
            
            self.processing_progress = 30.0
            self.processing_message = "Processing emails..."
            
            # Process and validate emails
            processing_result = self._process_email_list(raw_emails)
            
            self.processing_progress = 100.0
            self.processing_message = "Processing complete"
            
            # Update statistics
            self.processing_stats.update({
                'total_loaded': processing_result.processed_count,
                'valid_emails': processing_result.valid_emails,
                'invalid_emails': processing_result.invalid_emails,
                'duplicates_removed': processing_result.duplicates_removed,
                'last_processed': datetime.now()
            })
            
            logger.info(f"Email loading completed: {processing_result.valid_emails} valid emails")
            
            return processing_result
            
        except Exception as e:
            error_msg = f"Error loading emails: {e}"
            logger.error(error_msg)
            return ProcessingResult(
                success=False,
                message=error_msg
            )
        finally:
            self.is_processing = False
    
    def _load_from_excel(self, file_path: str, column_name: str = None) -> List[str]:
        """Load emails from Excel file"""
        try:
            # Try multiple engines for compatibility
            engines = ['openpyxl', 'xlrd']
            df = None
            
            for engine in engines:
                try:
                    df = pd.read_excel(file_path, engine=engine)
                    break
                except Exception:
                    continue
            
            if df is None:
                df = pd.read_excel(file_path)  # Use default engine
            
            # Determine email column
            if column_name and column_name in df.columns:
                email_column = df[column_name]
            else:
                # Use first column or auto-detect
                email_column = df.iloc[:, 0]
                
                # Try to find email column by name
                email_columns = [col for col in df.columns if 'email' in col.lower() or 'mail' in col.lower()]
                if email_columns:
                    email_column = df[email_columns[0]]
            
            # Extract email addresses
            emails = []
            for value in email_column.dropna():
                if pd.notna(value):
                    email_str = str(value).strip()
                    if email_str and '@' in email_str:
                        emails.append(email_str)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            raise
    
    def _load_from_csv(self, file_path: str, column_name: str = None) -> List[str]:
        """Load emails from CSV file"""
        try:
            # Try different encodings and delimiters
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            delimiters = [',', ';', '\t', '|']
            
            df = None
            for encoding in encodings:
                for delimiter in delimiters:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
                        if len(df.columns) > 1 or (len(df.columns) == 1 and df.shape[0] > 1):
                            break
                    except Exception:
                        continue
                if df is not None:
                    break
            
            if df is None:
                df = pd.read_csv(file_path)  # Use default settings
            
            # Extract emails similar to Excel method
            if column_name and column_name in df.columns:
                email_column = df[column_name]
            else:
                email_column = df.iloc[:, 0]
            
            emails = []
            for value in email_column.dropna():
                if pd.notna(value):
                    email_str = str(value).strip()
                    if email_str and '@' in email_str:
                        emails.append(email_str)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            raise
    
    def _load_from_text(self, file_path: str) -> List[str]:
        """Load emails from text file"""
        try:
            emails = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '@' in line:
                        # Extract email from line (handles various formats)
                        import re
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        found_emails = re.findall(email_pattern, line)
                        emails.extend(found_emails)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error loading text file: {e}")
            raise
    
    def _load_from_json(self, file_path: str) -> List[str]:
        """Load emails from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            emails = []
            
            if isinstance(data, list):
                # List of emails or objects
                for item in data:
                    if isinstance(item, str) and '@' in item:
                        emails.append(item)
                    elif isinstance(item, dict):
                        # Look for email fields
                        for key, value in item.items():
                            if 'email' in key.lower() and isinstance(value, str) and '@' in value:
                                emails.append(value)
            elif isinstance(data, dict):
                # Dictionary with email list
                for key, value in data.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and '@' in item:
                                emails.append(item)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            raise
    
    def _process_email_list(self, raw_emails: List[str]) -> ProcessingResult:
        """Process and validate email list"""
        try:
            processed_count = len(raw_emails)
            valid_emails = []
            invalid_emails = []
            
            # Remove duplicates while preserving order
            seen = set()
            unique_emails = []
            for email in raw_emails:
                email_lower = email.lower().strip()
                if email_lower not in seen:
                    seen.add(email_lower)
                    unique_emails.append(email_lower)
            
            duplicates_removed = processed_count - len(unique_emails)
            
            self.processing_progress = 50.0
            self.processing_message = "Validating emails..."
            
            # Validate emails in batches
            batch_size = min(self.batch_size, 100)
            for i in range(0, len(unique_emails), batch_size):
                batch = unique_emails[i:i + batch_size]
                
                for email in batch:
                    validation_result = self.validation_engine.validate_email(email)
                    
                    email_data = EmailData(
                        address=email,
                        status="valid" if validation_result.is_valid else "invalid",
                        validation_score=validation_result.score,
                        metadata=validation_result.details
                    )
                    
                    if validation_result.is_valid:
                        valid_emails.append(email_data)
                    else:
                        invalid_emails.append(email_data)
                
                # Update progress
                progress = 50.0 + (i / len(unique_emails)) * 40.0
                self.processing_progress = progress
                self.processing_message = f"Validated {i + len(batch)}/{len(unique_emails)} emails"
            
            # Store processed emails
            self.email_list = valid_emails + invalid_emails
            
            # Save to cache
            self._save_cache()
            
            return ProcessingResult(
                success=True,
                message=f"Processed {processed_count} emails successfully",
                processed_count=processed_count,
                valid_emails=len(valid_emails),
                invalid_emails=len(invalid_emails),
                duplicates_removed=duplicates_removed,
                details={
                    'unique_emails': len(unique_emails),
                    'validation_method': 'comprehensive'
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing email list: {e}")
            raise
    
    def send_email_batch(self, batch_emails: List[str], subject: str, body: str, 
                        attachments: List[str] = None, use_bcc: bool = True) -> SendingResult:
        """Send email to a batch of recipients"""
        
        if not batch_emails:
            return SendingResult(
                success=False,
                message="No email addresses provided"
            )
        
        if not self.outlook_manager.is_connected():
            return SendingResult(
                success=False,
                message="Outlook not connected",
                failed_emails=batch_emails
            )
        
        logger.info(f"Sending email batch to {len(batch_emails)} recipients")
        
        try:
            # Send email using Outlook manager
            email_result = self.outlook_manager.send_email_batch(
                email_addresses=batch_emails,
                subject=subject,
                body=body,
                attachments=attachments or [],
                use_bcc=use_bcc
            )
            
            if email_result.success:
                # Update email status
                for email_addr in batch_emails:
                    self._update_email_status(email_addr, "sent")
                
                self.processing_stats['sent_emails'] += len(batch_emails)
                
                logger.info(f"Batch sent successfully to {len(batch_emails)} recipients")
                
                return SendingResult(
                    success=True,
                    message=f"Email sent to {len(batch_emails)} recipients",
                    sent_count=len(batch_emails),
                    warnings=email_result.warnings
                )
            else:
                # Update email status as failed
                for email_addr in batch_emails:
                    self._update_email_status(email_addr, "failed", email_result.message)
                
                self.processing_stats['failed_emails'] += len(batch_emails)
                
                return SendingResult(
                    success=False,
                    message=email_result.message,
                    failed_count=len(batch_emails),
                    failed_emails=batch_emails
                )
            
        except Exception as e:
            error_msg = f"Error sending email batch: {e}"
            logger.error(error_msg)
            
            # Update email status as failed
            for email_addr in batch_emails:
                self._update_email_status(email_addr, "failed", str(e))
            
            self.processing_stats['failed_emails'] += len(batch_emails)
            
            return SendingResult(
                success=False,
                message=error_msg,
                failed_count=len(batch_emails),
                failed_emails=batch_emails
            )
    
    def _update_email_status(self, email_address: str, status: str, error_message: str = None):
        """Update email status in the list"""
        for email_data in self.email_list:
            if email_data.address == email_address:
                email_data.status = status
                email_data.attempts += 1
                email_data.last_attempt = datetime.now()
                if error_message:
                    email_data.error_message = error_message
                break
    
    def get_valid_emails(self) -> List[EmailData]:
        """Get list of valid emails"""
        return [email for email in self.email_list if email.status == "valid"]
    
    def get_pending_emails(self) -> List[EmailData]:
        """Get list of pending emails"""
        return [email for email in self.email_list if email.status in ["valid", "pending"]]
    
    def get_failed_emails(self) -> List[EmailData]:
        """Get list of failed emails"""
        return [email for email in self.email_list if email.status == "failed"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive email processing statistics"""
        total_emails = len(self.email_list)
        
        status_counts = {}
        for email in self.email_list:
            status_counts[email.status] = status_counts.get(email.status, 0) + 1
        
        return {
            'total_emails': total_emails,
            'status_breakdown': status_counts,
            'processing_stats': self.processing_stats.copy(),
            'validation_cache_size': len(self.validation_cache),
            'email_cache_size': len(self.email_cache),
            'last_processed': self.processing_stats.get('last_processed'),
            'processing_progress': self.processing_progress,
            'is_processing': self.is_processing
        }
    
    def export_email_list(self, file_path: str, include_status: bool = True) -> bool:
        """Export email list to file"""
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.xlsx':
                return self._export_to_excel(file_path, include_status)
            elif file_extension == '.csv':
                return self._export_to_csv(file_path, include_status)
            elif file_extension == '.json':
                return self._export_to_json(file_path, include_status)
            else:
                logger.error(f"Unsupported export format: {file_extension}")
                return False
                
        except Exception as e:
            logger.error(f"Error exporting email list: {e}")
            return False
    
    def _export_to_excel(self, file_path: str, include_status: bool) -> bool:
        """Export to Excel format"""
        try:
            data = []
            for email in self.email_list:
                row = {'email': email.address}
                
                if include_status:
                    row.update({
                        'status': email.status,
                        'validation_score': email.validation_score,
                        'attempts': email.attempts,
                        'last_attempt': email.last_attempt.isoformat() if email.last_attempt else None,
                        'error_message': email.error_message
                    })
                
                data.append(row)
            
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            
            logger.info(f"Email list exported to Excel: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
    
    def _export_to_csv(self, file_path: str, include_status: bool) -> bool:
        """Export to CSV format"""
        try:
            data = []
            for email in self.email_list:
                row = {'email': email.address}
                
                if include_status:
                    row.update({
                        'status': email.status,
                        'validation_score': email.validation_score,
                        'attempts': email.attempts,
                        'last_attempt': email.last_attempt.isoformat() if email.last_attempt else None,
                        'error_message': email.error_message
                    })
                
                data.append(row)
            
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            logger.info(f"Email list exported to CSV: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def _export_to_json(self, file_path: str, include_status: bool) -> bool:
        """Export to JSON format"""
        try:
            data = []
            for email in self.email_list:
                item = {'email': email.address}
                
                if include_status:
                    item.update({
                        'status': email.status,
                        'validation_score': email.validation_score,
                        'attempts': email.attempts,
                        'last_attempt': email.last_attempt.isoformat() if email.last_attempt else None,
                        'error_message': email.error_message,
                        'metadata': email.metadata
                    })
                
                data.append(item)
            
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_emails': len(data),
                    'include_status': include_status
                },
                'emails': data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Email list exported to JSON: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False
    
    def _load_cache(self):
        """Load cached data"""
        try:
            cache_dir = Path("cache")
            cache_file = cache_dir / "email_processor_cache.json"
            
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                self.email_cache = cache_data.get('email_cache', {})
                self.validation_cache = cache_data.get('validation_cache', {})
                
                logger.info("Email processor cache loaded")
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    
    def _save_cache(self):
        """Save data to cache"""
        try:
            cache_dir = Path("cache")
            cache_dir.mkdir(exist_ok=True)
            cache_file = cache_dir / "email_processor_cache.json"
            
            cache_data = {
                'email_cache': self.email_cache,
                'validation_cache': self.validation_cache,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug("Email processor cache saved")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def clear_cache(self):
        """Clear all caches"""
        try:
            self.email_cache.clear()
            self.validation_cache.clear()
            
            # Remove cache file
            cache_file = Path("cache") / "email_processor_cache.json"
            if cache_file.exists():
                cache_file.unlink()
            
            logger.info("Email processor cache cleared")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
    
    def _start_background_validation(self):
        """Start background email validation"""
        def validate_background():
            while True:
                try:
                    # Validate emails that need revalidation
                    for email in self.email_list:
                        if email.status == "pending" or (
                            email.last_attempt and 
                            (datetime.now() - email.last_attempt).total_seconds() > self.cache_ttl
                        ):
                            validation_result = self.validation_engine.validate_email(email.address)
                            email.validation_score = validation_result.score
                            email.status = "valid" if validation_result.is_valid else "invalid"
                    
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Background validation error: {e}")
                    time.sleep(600)  # Wait longer on error
        
        background_thread = threading.Thread(target=validate_background, daemon=True)
        background_thread.start()
        self.background_tasks.append(background_thread)
        
        logger.info("Background email validation started")
    
    def health_check(self) -> bool:
        """Perform health check"""
        try:
            # Check if we can access email list
            if not hasattr(self, 'email_list'):
                return False
            
            # Check if validation engine is working
            if not self.validation_engine:
                return False
            
            # Test validation with a sample email
            test_result = self.validation_engine.validate_email("test@example.com")
            if not hasattr(test_result, 'is_valid'):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Email processor health check failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup email processor resources"""
        try:
            # Save cache before cleanup
            self._save_cache()
            
            # Stop background tasks
            for task in self.background_tasks:
                if hasattr(task, 'stop'):
                    task.stop()
            
            # Clear data
            self.email_list.clear()
            self.email_cache.clear()
            self.validation_cache.clear()
            
            logger.info("Email processor cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during email processor cleanup: {e}")