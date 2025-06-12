# core/outlook_manager.py
"""
Advanced Outlook Manager
Comprehensive Outlook integration with connection management, error recovery, and fallback options
"""

import logging
import threading
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import Outlook libraries
try:
    import win32com.client
    import pythoncom
    OUTLOOK_AVAILABLE = True
except ImportError:
    OUTLOOK_AVAILABLE = False
    logger.warning("Outlook COM libraries not available")

@dataclass
class ConnectionResult:
    """Result of Outlook connection attempt"""
    success: bool
    message: str
    version: str = None
    account_count: int = 0
    warnings: List[str] = None

@dataclass
class EmailResult:
    """Result of email sending operation"""
    success: bool
    message: str
    email_count: int = 0
    failed_emails: List[str] = None
    warnings: List[str] = None

class OutlookManager:
    """Advanced Outlook integration manager with comprehensive error handling"""
    
    def __init__(self, config_manager, fallback_mode=False):
        self.config_manager = config_manager
        self.outlook_app = None
        self.namespace = None
        self.connected = False
        self.fallback_mode = fallback_mode
        
        # Connection management
        self.connection_attempts = 0
        self.max_connection_attempts = 5
        self.last_connection_time = None
        self.connection_lock = threading.Lock()
        
        # Health monitoring
        self.health_check_interval = 60  # seconds
        self.last_health_check = None
        self.health_monitor_thread = None
        self.monitoring_active = False
        
        # Error tracking
        self.error_count = 0
        self.last_error = None
        self.connection_history = []
        
        # Email tracking
        self.emails_sent = 0
        self.emails_failed = 0
        self.last_email_time = None
        
        # Alternative methods
        self.alternative_methods = [
            "Outlook.Application",
            "Outlook.Application.16",
            "Outlook.Application.15",
            "Outlook.Application.14",
            "Outlook.Application.12"
        ]
    
    def initialize(self) -> ConnectionResult:
        """Initialize Outlook connection with comprehensive error handling"""
        if self.fallback_mode:
            logger.info("Outlook manager initialized in fallback mode")
            return ConnectionResult(
                success=True,
                message="Fallback mode - limited functionality",
                warnings=["Outlook integration disabled"]
            )
        
        if not OUTLOOK_AVAILABLE:
            logger.error("Outlook COM libraries not available")
            return ConnectionResult(
                success=False,
                message="Outlook COM libraries not installed",
                warnings=["Install pywin32 package for Outlook integration"]
            )
        
        logger.info("Initializing Outlook connection")
        
        try:
            connection_result = self._establish_connection()
            
            if connection_result.success:
                self._start_health_monitoring()
                logger.info("Outlook manager initialized successfully")
            else:
                logger.error(f"Outlook initialization failed: {connection_result.message}")
            
            return connection_result
            
        except Exception as e:
            logger.error(f"Critical error during Outlook initialization: {e}")
            return ConnectionResult(
                success=False,
                message=f"Initialization error: {e}"
            )
    
    def _establish_connection(self) -> ConnectionResult:
        """Establish connection to Outlook with multiple fallback methods"""
        with self.connection_lock:
            self.connection_attempts += 1
            
            if self.connection_attempts > self.max_connection_attempts:
                return ConnectionResult(
                    success=False,
                    message="Maximum connection attempts exceeded"
                )
            
            warnings = []
            
            try:
                # Initialize COM for this thread
                pythoncom.CoInitialize()
                
                # Try different connection methods
                for method in self.alternative_methods:
                    try:
                        logger.info(f"Attempting connection with method: {method}")
                        
                        self.outlook_app = win32com.client.Dispatch(method)
                        self.namespace = self.outlook_app.GetNamespace("MAPI")
                        
                        # Test the connection
                        folders = self.namespace.Folders
                        folder_count = folders.Count
                        
                        # Get Outlook version
                        version = getattr(self.outlook_app, 'Version', 'Unknown')
                        
                        # Count email accounts
                        account_count = 0
                        try:
                            accounts = self.namespace.Accounts
                            account_count = accounts.Count
                        except Exception:
                            warnings.append("Unable to access email accounts")
                        
                        self.connected = True
                        self.last_connection_time = datetime.now()
                        self.connection_history.append({
                            'timestamp': self.last_connection_time.isoformat(),
                            'method': method,
                            'success': True
                        })
                        
                        logger.info(f"Outlook connection established successfully with {method}")
                        logger.info(f"Version: {version}, Folders: {folder_count}, Accounts: {account_count}")
                        
                        return ConnectionResult(
                            success=True,
                            message=f"Connected successfully using {method}",
                            version=version,
                            account_count=account_count,
                            warnings=warnings
                        )
                        
                    except Exception as e:
                        logger.warning(f"Connection method {method} failed: {e}")
                        self.connection_history.append({
                            'timestamp': datetime.now().isoformat(),
                            'method': method,
                            'success': False,
                            'error': str(e)
                        })
                        continue
                
                # All methods failed
                error_msg = "All Outlook connection methods failed"
                self.last_error = error_msg
                
                return ConnectionResult(
                    success=False,
                    message=error_msg,
                    warnings=warnings
                )
                
            except Exception as e:
                error_msg = f"Critical connection error: {e}"
                self.last_error = error_msg
                logger.error(error_msg)
                
                return ConnectionResult(
                    success=False,
                    message=error_msg
                )
    
    def _start_health_monitoring(self):
        """Start background health monitoring"""
        if self.monitoring_active:
            return
        
        def monitor_health():
            self.monitoring_active = True
            while self.monitoring_active:
                try:
                    self._perform_health_check()
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    time.sleep(self.health_check_interval * 2)  # Wait longer on error
        
        self.health_monitor_thread = threading.Thread(target=monitor_health, daemon=True)
        self.health_monitor_thread.start()
        logger.info("Outlook health monitoring started")
    
    def _perform_health_check(self):
        """Perform health check on Outlook connection"""
        try:
            if not self.connected or not self.outlook_app:
                return False
            
            # Test basic connectivity
            folders = self.namespace.Folders
            folder_count = folders.Count
            
            self.last_health_check = datetime.now()
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self.connected = False
            self.error_count += 1
            
            # Attempt automatic reconnection
            if self.config_manager and hasattr(self.config_manager, 'get_outlook_settings'):
                outlook_settings = self.config_manager.get_outlook_settings()
                if hasattr(outlook_settings, 'auto_reconnect') and outlook_settings.auto_reconnect:
                    logger.info("Attempting automatic reconnection")
                    self._establish_connection()
            
            return False
    
    def send_email_batch(self, email_addresses: List[str], subject: str, 
                        body: str, attachments: List[str] = None,
                        use_bcc: bool = True) -> EmailResult:
        """Send email to batch of recipients with comprehensive error handling"""
        
        if self.fallback_mode:
            return EmailResult(
                success=False,
                message="Email sending not available in fallback mode",
                failed_emails=email_addresses
            )
        
        if not email_addresses:
            return EmailResult(
                success=False,
                message="No email addresses provided"
            )
        
        if not self.connected:
            reconnect_result = self.reconnect()
            if not reconnect_result.success:
                return EmailResult(
                    success=False,
                    message=f"Connection failed: {reconnect_result.message}",
                    failed_emails=email_addresses
                )
        
        logger.info(f"Sending email to {len(email_addresses)} recipients")
        
        try:
            mail_item = self.create_email()
            
            # Set email properties
            mail_item.Subject = subject
            mail_item.Body = body
            
            # Add recipients
            if use_bcc:
                # Use BCC to hide recipients from each other
                bcc_list = "; ".join(email_addresses)
                mail_item.BCC = bcc_list
                logger.info(f"Added {len(email_addresses)} recipients to BCC")
            else:
                # Use TO field (recipients will see each other)
                to_list = "; ".join(email_addresses)
                mail_item.To = to_list
                logger.info(f"Added {len(email_addresses)} recipients to TO")
            
            # Add attachments
            attachment_count = 0
            failed_attachments = []
            
            if attachments:
                for attachment_path in attachments:
                    if attachment_path and Path(attachment_path).exists():
                        try:
                            mail_item.Attachments.Add(str(attachment_path))
                            attachment_count += 1
                            logger.info(f"Added attachment: {Path(attachment_path).name}")
                        except Exception as e:
                            logger.warning(f"Failed to attach {attachment_path}: {e}")
                            failed_attachments.append(attachment_path)
                    else:
                        logger.warning(f"Attachment not found: {attachment_path}")
                        failed_attachments.append(attachment_path)
            
            # Send the email
            mail_item.Send()
            
            # Update statistics
            self.emails_sent += len(email_addresses)
            self.last_email_time = datetime.now()
            
            warnings = []
            if failed_attachments:
                warnings.append(f"Failed to attach {len(failed_attachments)} files")
            
            logger.info(f"Email sent successfully to {len(email_addresses)} recipients")
            
            return EmailResult(
                success=True,
                message=f"Email sent to {len(email_addresses)} recipients",
                email_count=len(email_addresses),
                warnings=warnings
            )
            
        except Exception as e:
            error_msg = f"Failed to send email: {e}"
            logger.error(error_msg)
            
            self.emails_failed += len(email_addresses)
            self.error_count += 1
            self.last_error = error_msg
            
            return EmailResult(
                success=False,
                message=error_msg,
                failed_emails=email_addresses
            )
    
    def create_email(self) -> Any:
        """Create new email item with error handling"""
        if self.fallback_mode:
            raise Exception("Email creation not available in fallback mode")
        
        if not self.connected:
            raise Exception("Outlook not connected")
        
        try:
            # Ensure COM is initialized for this thread
            pythoncom.CoInitialize()
            
            # Create mail item (0 = olMailItem)
            mail_item = self.outlook_app.CreateItem(0)
            
            return mail_item
            
        except Exception as e:
            logger.error(f"Failed to create email: {e}")
            self.error_count += 1
            raise
    
    def reconnect(self) -> ConnectionResult:
        """Manually reconnect to Outlook"""
        logger.info("Manual reconnection requested")
        
        # Cleanup existing connection
        self.cleanup_connection()
        
        # Reset connection counter for manual reconnection
        self.connection_attempts = 0
        
        # Attempt new connection
        return self._establish_connection()
    
    def cleanup_connection(self):
        """Cleanup Outlook connection and resources"""
        try:
            self.connected = False
            
            if self.outlook_app:
                self.outlook_app = None
            
            if self.namespace:
                self.namespace = None
            
            # Cleanup COM
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass  # Ignore COM cleanup errors
            
            logger.info("Outlook connection cleaned up")
            
        except Exception as e:
            logger.warning(f"Error during Outlook cleanup: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive Outlook integration statistics"""
        return {
            'connection_status': {
                'connected': self.connected,
                'last_connection': self.last_connection_time.isoformat() if self.last_connection_time else None,
                'connection_attempts': self.connection_attempts,
                'uptime_minutes': (datetime.now() - self.last_connection_time).total_seconds() / 60 if self.last_connection_time else 0
            },
            'email_statistics': {
                'emails_sent': self.emails_sent,
                'emails_failed': self.emails_failed,
                'success_rate': (self.emails_sent / (self.emails_sent + self.emails_failed) * 100) if (self.emails_sent + self.emails_failed) > 0 else 0,
                'last_email_time': self.last_email_time.isoformat() if self.last_email_time else None
            },
            'error_statistics': {
                'total_errors': self.error_count,
                'last_error': self.last_error,
                'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
            },
            'configuration': {
                'fallback_mode': self.fallback_mode,
                'health_monitoring': self.monitoring_active,
                'auto_reconnect': True
            }
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Perform comprehensive connection test"""
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'connected': self.connected,
            'tests': {}
        }
        
        if not self.connected:
            test_results['tests']['connection'] = {
                'passed': False,
                'message': 'Not connected to Outlook'
            }
            return test_results
        
        # Test basic connectivity
        try:
            folders = self.namespace.Folders
            test_results['tests']['basic_connectivity'] = {
                'passed': True,
                'message': f'Access to {folders.Count} folders'
            }
        except Exception as e:
            test_results['tests']['basic_connectivity'] = {
                'passed': False,
                'message': f'Basic connectivity failed: {e}'
            }
        
        # Test email creation
        try:
            test_mail = self.create_email()
            test_mail = None  # Release reference
            test_results['tests']['email_creation'] = {
                'passed': True,
                'message': 'Email creation successful'
            }
        except Exception as e:
            test_results['tests']['email_creation'] = {
                'passed': False,
                'message': f'Email creation failed: {e}'
            }
        
        # Overall test result
        all_tests_passed = all(test['passed'] for test in test_results['tests'].values())
        test_results['overall_result'] = {
            'passed': all_tests_passed,
            'message': 'All tests passed' if all_tests_passed else 'Some tests failed'
        }
        
        return test_results
    
    def is_connected(self) -> bool:
        """Check if Outlook is connected"""
        return self.connected and not self.fallback_mode
    
    def is_available(self) -> bool:
        """Check if Outlook integration is available"""
        return OUTLOOK_AVAILABLE and not self.fallback_mode
    
    def health_check(self) -> bool:
        """Perform health check for application manager"""
        try:
            if self.fallback_mode:
                return True  # Fallback mode is always "healthy"
            
            if not OUTLOOK_AVAILABLE:
                return False
            
            if not self.connected:
                return False
            
            # Test basic functionality
            return self._perform_health_check()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def cleanup(self):
        """Full cleanup of Outlook manager"""
        try:
            # Stop health monitoring
            self.monitoring_active = False
            
            if self.health_monitor_thread and self.health_monitor_thread.is_alive():
                self.health_monitor_thread.join(timeout=5)
            
            # Cleanup connection
            self.cleanup_connection()
            
            logger.info("Outlook manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during Outlook manager cleanup: {e}")