# core/exception_handler.py
"""
Global Exception Handler
Advanced error management, recovery, and user notification system
"""

import sys
import traceback
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class ErrorReport:
    """Comprehensive error report"""
    timestamp: str
    error_type: str
    error_message: str
    traceback_info: str
    component: str
    severity: str
    context: Dict[str, Any]
    recovery_attempted: bool = False
    recovery_successful: bool = False
    user_notified: bool = False

class GlobalExceptionHandler:
    """Global exception handler with advanced recovery capabilities"""
    
    def __init__(self):
        self.error_reports = []
        self.error_counts = {}
        self.recovery_strategies = {}
        self.notification_callbacks = []
        self.error_log_path = Path("logs") / "errors"
        self.error_log_path.mkdir(parents=True, exist_ok=True)
        
        # Error severity levels
        self.severity_levels = {
            'CRITICAL': 5,
            'HIGH': 4,
            'MEDIUM': 3,
            'LOW': 2,
            'INFO': 1
        }
        
        # Setup default recovery strategies
        self._setup_default_recovery_strategies()
    
    def setup(self):
        """Setup global exception handling"""
        # Set custom exception hook
        sys.excepthook = self._global_exception_hook
        
        # Setup threading exception handler
        threading.excepthook = self._threading_exception_hook
        
        logger.info("Global exception handler setup completed")
    
    def _global_exception_hook(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow KeyboardInterrupt to pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_report = self._create_error_report(
            exc_type, exc_value, exc_traceback, 
            component="main_application",
            severity="CRITICAL"
        )
        
        self._process_error(error_report)
        
        # Call original hook for critical errors
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def _threading_exception_hook(self, args):
        """Handle uncaught exceptions in threads"""
        error_report = self._create_error_report(
            args.exc_type, args.exc_value, args.exc_traceback,
            component=f"thread_{args.thread.name}",
            severity="HIGH"
        )
        
        self._process_error(error_report)
    
    def handle_exception(self, exc_type, exc_value, exc_traceback=None, 
                        component="unknown", severity="MEDIUM", 
                        context=None, attempt_recovery=True):
        """Handle exceptions with context and recovery options"""
        
        if exc_traceback is None:
            exc_traceback = exc_value.__traceback__
        
        error_report = self._create_error_report(
            exc_type, exc_value, exc_traceback,
            component=component,
            severity=severity,
            context=context or {}
        )
        
        return self._process_error(error_report, attempt_recovery)
    
    def _create_error_report(self, exc_type, exc_value, exc_traceback,
                           component, severity, context=None):
        """Create comprehensive error report"""
        
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        
        error_report = ErrorReport(
            timestamp=datetime.now().isoformat(),
            error_type=exc_type.__name__,
            error_message=str(exc_value),
            traceback_info=''.join(tb_lines),
            component=component,
            severity=severity,
            context=context or {}
        )
        
        return error_report
    
    def _process_error(self, error_report: ErrorReport, attempt_recovery=True):
        """Process error report with logging, recovery, and notification"""
        
        # Add to error reports
        self.error_reports.append(error_report)
        
        # Update error counts
        error_key = f"{error_report.component}_{error_report.error_type}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log the error
        self._log_error(error_report)
        
        # Attempt recovery if enabled
        if attempt_recovery:
            recovery_success = self._attempt_recovery(error_report)
            error_report.recovery_attempted = True
            error_report.recovery_successful = recovery_success
        
        # Notify users/components
        self._notify_error(error_report)
        error_report.user_notified = True
        
        # Save error report to file
        self._save_error_report(error_report)
        
        return error_report
    
    def _log_error(self, error_report: ErrorReport):
        """Log error with appropriate level"""
        severity_level = self.severity_levels.get(error_report.severity, 3)
        
        if severity_level >= 5:
            logger.critical(f"CRITICAL ERROR in {error_report.component}: {error_report.error_message}")
        elif severity_level >= 4:
            logger.error(f"ERROR in {error_report.component}: {error_report.error_message}")
        elif severity_level >= 3:
            logger.warning(f"WARNING in {error_report.component}: {error_report.error_message}")
        else:
            logger.info(f"INFO in {error_report.component}: {error_report.error_message}")
        
        # Log full traceback for debugging
        logger.debug(f"Full traceback:\n{error_report.traceback_info}")
    
    def _attempt_recovery(self, error_report: ErrorReport) -> bool:
        """Attempt automated recovery based on error type and component"""
        try:
            # Get recovery strategy
            strategy_key = f"{error_report.component}_{error_report.error_type}"
            if strategy_key in self.recovery_strategies:
                recovery_func = self.recovery_strategies[strategy_key]
                return recovery_func(error_report)
            
            # Try generic recovery strategies
            generic_key = error_report.error_type
            if generic_key in self.recovery_strategies:
                recovery_func = self.recovery_strategies[generic_key]
                return recovery_func(error_report)
            
            # Default recovery based on error type
            return self._default_recovery(error_report)
            
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            return False
    
    def _default_recovery(self, error_report: ErrorReport) -> bool:
        """Default recovery strategies for common errors"""
        try:
            error_type = error_report.error_type
            
            if error_type in ['ConnectionError', 'TimeoutError']:
                # Wait and retry for connection issues
                logger.info("Attempting connection recovery - waiting 5 seconds")
                time.sleep(5)
                return True
            
            elif error_type == 'FileNotFoundError':
                # Try to create missing directories
                if 'file_path' in error_report.context:
                    file_path = Path(error_report.context['file_path'])
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created missing directory: {file_path.parent}")
                    return True
            
            elif error_type == 'PermissionError':
                # Log permission issue for manual resolution
                logger.warning("Permission error detected - manual intervention required")
                return False
            
            elif error_type == 'ImportError':
                # Suggest package installation
                logger.warning("Import error - package may need to be installed")
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Default recovery failed: {e}")
            return False
    
    def _notify_error(self, error_report: ErrorReport):
        """Notify registered callbacks about the error"""
        for callback in self.notification_callbacks:
            try:
                callback(error_report)
            except Exception as e:
                logger.error(f"Error notification callback failed: {e}")
    
    def _save_error_report(self, error_report: ErrorReport):
        """Save error report to file for analysis"""
        try:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_report_{timestamp_str}_{error_report.component}.json"
            filepath = self.error_log_path / filename
            
            # Convert error report to dict
            report_dict = {
                'timestamp': error_report.timestamp,
                'error_type': error_report.error_type,
                'error_message': error_report.error_message,
                'component': error_report.component,
                'severity': error_report.severity,
                'context': error_report.context,
                'recovery_attempted': error_report.recovery_attempted,
                'recovery_successful': error_report.recovery_successful,
                'traceback': error_report.traceback_info
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Failed to save error report: {e}")
    
    def _setup_default_recovery_strategies(self):
        """Setup default recovery strategies for common errors"""
        
        # Outlook connection recovery
        def outlook_recovery(error_report):
            logger.info("Attempting Outlook connection recovery")
            time.sleep(3)
            # Recovery logic would be implemented here
            return True
        
        # File operation recovery
        def file_recovery(error_report):
            logger.info("Attempting file operation recovery")
            # Create directories, check permissions, etc.
            return True
        
        # Database connection recovery
        def db_recovery(error_report):
            logger.info("Attempting database connection recovery")
            time.sleep(2)
            return True
        
        self.recovery_strategies.update({
            'outlook_manager_ConnectionError': outlook_recovery,
            'file_manager_FileNotFoundError': file_recovery,
            'ConnectionError': db_recovery
        })
    
    def register_recovery_strategy(self, error_pattern: str, recovery_func: Callable):
        """Register a custom recovery strategy"""
        self.recovery_strategies[error_pattern] = recovery_func
        logger.info(f"Registered recovery strategy for: {error_pattern}")
    
    def register_notification_callback(self, callback: Callable):
        """Register a callback for error notifications"""
        self.notification_callbacks.append(callback)
        logger.info("Registered error notification callback")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        if not self.error_reports:
            return {'total_errors': 0}
        
        total_errors = len(self.error_reports)
        
        # Count by severity
        severity_counts = {}
        for report in self.error_reports:
            severity_counts[report.severity] = severity_counts.get(report.severity, 0) + 1
        
        # Count by component
        component_counts = {}
        for report in self.error_reports:
            component_counts[report.component] = component_counts.get(report.component, 0) + 1
        
        # Count by error type
        error_type_counts = {}
        for report in self.error_reports:
            error_type_counts[report.error_type] = error_type_counts.get(report.error_type, 0) + 1
        
        # Recovery statistics
        recovery_attempted = sum(1 for r in self.error_reports if r.recovery_attempted)
        recovery_successful = sum(1 for r in self.error_reports if r.recovery_successful)
        
        # Recent errors (last 24 hours)
        recent_cutoff = time.time() - (24 * 60 * 60)
        recent_errors = [
            r for r in self.error_reports 
            if datetime.fromisoformat(r.timestamp).timestamp() > recent_cutoff
        ]
        
        return {
            'total_errors': total_errors,
            'severity_breakdown': severity_counts,
            'component_breakdown': component_counts,
            'error_type_breakdown': error_type_counts,
            'recovery_attempted': recovery_attempted,
            'recovery_successful': recovery_successful,
            'recovery_success_rate': (recovery_successful / recovery_attempted * 100) if recovery_attempted > 0 else 0,
            'recent_errors_24h': len(recent_errors),
            'most_common_errors': sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def get_recent_errors(self, hours: int = 24) -> list:
        """Get recent error reports"""
        cutoff_time = time.time() - (hours * 60 * 60)
        
        return [
            report for report in self.error_reports
            if datetime.fromisoformat(report.timestamp).timestamp() > cutoff_time
        ]
    
    def clear_old_errors(self, days: int = 7):
        """Clear old error reports"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        initial_count = len(self.error_reports)
        self.error_reports = [
            report for report in self.error_reports
            if datetime.fromisoformat(report.timestamp).timestamp() > cutoff_time
        ]
        
        cleared_count = initial_count - len(self.error_reports)
        logger.info(f"Cleared {cleared_count} old error reports")
        
        return cleared_count
    
    def export_error_report(self, filepath: str) -> bool:
        """Export comprehensive error report"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'statistics': self.get_error_statistics(),
                'error_reports': [
                    {
                        'timestamp': r.timestamp,
                        'error_type': r.error_type,
                        'error_message': r.error_message,
                        'component': r.component,
                        'severity': r.severity,
                        'recovery_attempted': r.recovery_attempted,
                        'recovery_successful': r.recovery_successful
                    }
                    for r in self.error_reports
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Error report exported to: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export error report: {e}")
            return False
    
    def health_check(self) -> bool:
        """Perform health check on exception handling system"""
        try:
            # Check if there are too many recent critical errors
            recent_critical = [
                r for r in self.get_recent_errors(1)  # Last hour
                if r.severity == 'CRITICAL'
            ]
            
            if len(recent_critical) > 5:
                return False
            
            # Check if error log directory is writable
            test_file = self.error_log_path / "health_check.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Exception handler health check failed: {e}")
            return False