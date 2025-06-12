# core/scheduler_manager.py
"""
Scheduler Manager - Advanced Email Scheduling System
Handles email scheduling, batch management, and automated sending
"""

import logging
import threading
import time
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

@dataclass
class EmailBatch:
    """Email batch data structure"""
    batch_id: str
    emails: List[str]
    subject: str
    body: str
    attachments: List[str]
    scheduled_time: datetime
    status: str = "pending"  # pending, sent, failed, cancelled
    created_time: datetime = None
    sent_time: Optional[datetime] = None
    attempts: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class ScheduleSettings:
    """Schedule configuration"""
    emails_per_day: int = 499
    emails_per_batch: int = 10
    start_time: str = "06:00"
    end_time: str = "18:00"
    working_days_only: bool = True
    batch_interval_minutes: int = 5
    retry_failed_batches: bool = True
    max_retry_attempts: int = 3
    retry_delay_hours: int = 1

@dataclass
class ScheduleResult:
    """Result of schedule creation"""
    success: bool
    message: str
    total_batches: int = 0
    total_days: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    schedule_id: str = None

class SchedulerManager:
    """Advanced email scheduling manager with comprehensive functionality"""
    
    def __init__(self, email_processor, config_manager):
        self.email_processor = email_processor
        self.config_manager = config_manager
        
        # Schedule data
        self.current_schedule = None
        self.schedule_history = []
        self.active_batches = []
        self.completed_batches = []
        self.failed_batches = []
        
        # Scheduler state
        self.is_running = False
        self.scheduler_thread = None
        self.schedule_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total_schedules_created': 0,
            'total_batches_sent': 0,
            'total_emails_sent': 0,
            'total_failures': 0,
            'average_success_rate': 0.0,
            'last_schedule_date': None
        }
        
        # Persistence
        self.schedules_dir = Path("schedules")
        self.schedules_dir.mkdir(exist_ok=True)
        
    def initialize(self):
        """Initialize scheduler manager"""
        try:
            logger.info("Initializing scheduler manager")
            
            # Load saved schedules
            self._load_saved_schedules()
            
            # Clear any existing schedule jobs
            schedule.clear()
            
            logger.info("Scheduler manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler manager: {e}")
            return False
    
    def create_schedule(self, emails: List[str], subject: str, body: str, 
                       attachments: List[str] = None, 
                       schedule_settings: ScheduleSettings = None) -> ScheduleResult:
        """Create comprehensive email schedule"""
        
        if not emails:
            return ScheduleResult(
                success=False,
                message="No emails provided for scheduling"
            )
        
        if not subject.strip():
            return ScheduleResult(
                success=False,
                message="Email subject cannot be empty"
            )
        
        logger.info(f"Creating schedule for {len(emails)} emails")
        
        try:
            with self.schedule_lock:
                # Use provided settings or get from config
                if schedule_settings is None:
                    config_schedule = self.config_manager.get_schedule_settings()
                    schedule_settings = ScheduleSettings(
                        emails_per_day=config_schedule.emails_per_day,
                        emails_per_batch=config_schedule.emails_per_batch,
                        start_time=config_schedule.start_time,
                        working_days_only=config_schedule.working_days_only,
                        retry_failed_batches=config_schedule.retry_failed_emails,
                        max_retry_attempts=config_schedule.retry_attempts
                    )
                
                # Generate schedule
                batches = self._generate_batches(
                    emails, subject, body, attachments or [], schedule_settings
                )
                
                if not batches:
                    return ScheduleResult(
                        success=False,
                        message="Failed to generate email batches"
                    )
                
                # Create schedule object
                schedule_id = str(uuid.uuid4())
                schedule_data = {
                    'schedule_id': schedule_id,
                    'created_time': datetime.now(),
                    'settings': asdict(schedule_settings),
                    'batches': [asdict(batch) for batch in batches],
                    'subject': subject,
                    'body': body,
                    'attachments': attachments or [],
                    'total_emails': len(emails),
                    'status': 'created'
                }
                
                self.current_schedule = schedule_data
                self.active_batches = batches
                
                # Save schedule
                self._save_schedule(schedule_data)
                
                # Update statistics
                self.stats['total_schedules_created'] += 1
                self.stats['last_schedule_date'] = datetime.now()
                
                # Calculate schedule span
                start_date = min(batch.scheduled_time for batch in batches)
                end_date = max(batch.scheduled_time for batch in batches)
                total_days = (end_date.date() - start_date.date()).days + 1
                
                logger.info(f"Schedule created successfully: {len(batches)} batches over {total_days} days")
                
                return ScheduleResult(
                    success=True,
                    message=f"Schedule created with {len(batches)} batches",
                    total_batches=len(batches),
                    total_days=total_days,
                    start_date=start_date,
                    end_date=end_date,
                    schedule_id=schedule_id
                )
                
        except Exception as e:
            error_msg = f"Error creating schedule: {e}"
            logger.error(error_msg)
            return ScheduleResult(
                success=False,
                message=error_msg
            )
    
    def _generate_batches(self, emails: List[str], subject: str, body: str, 
                         attachments: List[str], settings: ScheduleSettings) -> List[EmailBatch]:
        """Generate email batches based on schedule settings"""
        
        batches = []
        email_index = 0
        current_date = self._get_next_working_day()
        
        # Parse start time
        start_hour, start_minute = map(int, settings.start_time.split(':'))
        
        while email_index < len(emails):
            # Skip weekends if working days only
            if settings.working_days_only and current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            # Calculate batches for current day
            daily_batches = 0
            max_daily_batches = settings.emails_per_day // settings.emails_per_batch
            
            current_time = current_date.replace(hour=start_hour, minute=start_minute)
            
            while (email_index < len(emails) and 
                   daily_batches < max_daily_batches and 
                   len([email for batch in batches if batch.scheduled_time.date() == current_date.date() 
                       for email in batch.emails]) < settings.emails_per_day):
                
                # Create batch
                batch_emails = emails[email_index:email_index + settings.emails_per_batch]
                
                batch = EmailBatch(
                    batch_id=str(uuid.uuid4()),
                    emails=batch_emails,
                    subject=subject,
                    body=body,
                    attachments=attachments.copy(),
                    scheduled_time=current_time,
                    created_time=datetime.now(),
                    metadata={
                        'day_batch_number': daily_batches + 1,
                        'total_day_batches': max_daily_batches,
                        'emails_in_batch': len(batch_emails)
                    }
                )
                
                batches.append(batch)
                
                # Move to next batch
                email_index += len(batch_emails)
                daily_batches += 1
                current_time += timedelta(minutes=settings.batch_interval_minutes)
            
            # Move to next day
            current_date += timedelta(days=1)
        
        return batches
    
    def _get_next_working_day(self) -> datetime:
        """Get next working day for scheduling"""
        next_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Skip weekends
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        
        return next_day
    
    def start_schedule(self) -> bool:
        """Start executing the current schedule"""
        
        if not self.current_schedule:
            logger.error("No schedule to start")
            return False
        
        if self.is_running:
            logger.warning("Schedule is already running")
            return False
        
        logger.info("Starting email schedule execution")
        
        try:
            with self.schedule_lock:
                self.is_running = True
                
                # Clear existing schedule jobs
                schedule.clear()
                
                # Schedule all batches
                for batch in self.active_batches:
                    if batch.status == "pending":
                        self._schedule_batch(batch)
                
                # Start scheduler thread
                self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
                self.scheduler_thread.start()
                
                # Update schedule status
                self.current_schedule['status'] = 'running'
                self.current_schedule['started_time'] = datetime.now()
                
                logger.info(f"Schedule started with {len(self.active_batches)} active batches")
                return True
                
        except Exception as e:
            logger.error(f"Error starting schedule: {e}")
            self.is_running = False
            return False
    
    def _schedule_batch(self, batch: EmailBatch):
        """Schedule a single batch for execution"""
        
        def execute_batch():
            try:
                logger.info(f"Executing batch {batch.batch_id} with {len(batch.emails)} emails")
                
                # Send email batch
                result = self.email_processor.send_email_batch(
                    batch_emails=batch.emails,
                    subject=batch.subject,
                    body=batch.body,
                    attachments=batch.attachments,
                    use_bcc=True
                )
                
                # Update batch status
                if result.success:
                    batch.status = "sent"
                    batch.sent_time = datetime.now()
                    self.completed_batches.append(batch)
                    
                    # Update statistics
                    self.stats['total_batches_sent'] += 1
                    self.stats['total_emails_sent'] += len(batch.emails)
                    
                    logger.info(f"Batch {batch.batch_id} sent successfully")
                else:
                    batch.status = "failed"
                    batch.error_message = result.message
                    batch.attempts += 1
                    self.failed_batches.append(batch)
                    
                    # Update statistics
                    self.stats['total_failures'] += 1
                    
                    logger.error(f"Batch {batch.batch_id} failed: {result.message}")
                    
                    # Schedule retry if enabled
                    if (self.config_manager.get_schedule_settings().retry_failed_emails and 
                        batch.attempts < self.config_manager.get_schedule_settings().retry_attempts):
                        self._schedule_retry(batch)
                
                # Remove from active batches
                if batch in self.active_batches:
                    self.active_batches.remove(batch)
                
                # Update schedule status
                self._update_schedule_status()
                
            except Exception as e:
                logger.error(f"Error executing batch {batch.batch_id}: {e}")
                batch.status = "failed"
                batch.error_message = str(e)
                batch.attempts += 1
                
                if batch in self.active_batches:
                    self.active_batches.remove(batch)
                self.failed_batches.append(batch)
        
        # Schedule the batch
        batch_time = batch.scheduled_time.strftime("%H:%M")
        schedule.every().day.at(batch_time).do(execute_batch).tag(batch.batch_id)
        
        logger.debug(f"Batch {batch.batch_id} scheduled for {batch.scheduled_time}")
    
    def _schedule_retry(self, batch: EmailBatch):
        """Schedule retry for failed batch"""
        
        retry_delay = self.config_manager.get_schedule_settings().retry_delay_minutes
        retry_time = datetime.now() + timedelta(minutes=retry_delay)
        
        # Create retry batch
        retry_batch = EmailBatch(
            batch_id=str(uuid.uuid4()),
            emails=batch.emails.copy(),
            subject=batch.subject,
            body=batch.body,
            attachments=batch.attachments.copy(),
            scheduled_time=retry_time,
            created_time=datetime.now(),
            attempts=batch.attempts,
            metadata={
                'is_retry': True,
                'original_batch_id': batch.batch_id,
                'retry_attempt': batch.attempts
            }
        )
        
        self.active_batches.append(retry_batch)
        self._schedule_batch(retry_batch)
        
        logger.info(f"Retry scheduled for batch {batch.batch_id} at {retry_time}")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Scheduler thread started")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
                
                # Check if all batches are complete
                if not self.active_batches and self.is_running:
                    logger.info("All batches completed, stopping scheduler")
                    self.stop_schedule()
                    break
                    
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait longer on error
        
        logger.info("Scheduler thread ended")
    
    def stop_schedule(self) -> bool:
        """Stop the current schedule execution"""
        
        if not self.is_running:
            logger.warning("No schedule is currently running")
            return False
        
        logger.info("Stopping email schedule execution")
        
        try:
            with self.schedule_lock:
                self.is_running = False
                
                # Clear scheduled jobs
                schedule.clear()
                
                # Wait for scheduler thread to stop
                if self.scheduler_thread and self.scheduler_thread.is_alive():
                    self.scheduler_thread.join(timeout=10)
                
                # Update schedule status
                if self.current_schedule:
                    self.current_schedule['status'] = 'stopped'
                    self.current_schedule['stopped_time'] = datetime.now()
                
                # Move remaining active batches to failed
                for batch in self.active_batches:
                    batch.status = "cancelled"
                    self.failed_batches.append(batch)
                
                self.active_batches.clear()
                
                logger.info("Schedule stopped successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error stopping schedule: {e}")
            return False
    
    def pause_schedule(self) -> bool:
        """Pause the current schedule execution"""
        
        if not self.is_running:
            return False
        
        try:
            with self.schedule_lock:
                # Clear scheduled jobs but keep state
                schedule.clear()
                
                if self.current_schedule:
                    self.current_schedule['status'] = 'paused'
                    self.current_schedule['paused_time'] = datetime.now()
                
                logger.info("Schedule paused")
                return True
                
        except Exception as e:
            logger.error(f"Error pausing schedule: {e}")
            return False
    
    def resume_schedule(self) -> bool:
        """Resume paused schedule execution"""
        
        if not self.current_schedule or self.current_schedule.get('status') != 'paused':
            return False
        
        try:
            with self.schedule_lock:
                # Reschedule pending batches
                for batch in self.active_batches:
                    if batch.status == "pending":
                        # Adjust time if needed
                        if batch.scheduled_time < datetime.now():
                            batch.scheduled_time = datetime.now() + timedelta(minutes=5)
                        self._schedule_batch(batch)
                
                self.current_schedule['status'] = 'running'
                self.current_schedule['resumed_time'] = datetime.now()
                
                logger.info("Schedule resumed")
                return True
                
        except Exception as e:
            logger.error(f"Error resuming schedule: {e}")
            return False
    
    def _update_schedule_status(self):
        """Update overall schedule status"""
        
        if not self.current_schedule:
            return
        
        total_batches = len(self.completed_batches) + len(self.failed_batches) + len(self.active_batches)
        
        if not self.active_batches and total_batches > 0:
            # All batches processed
            success_rate = len(self.completed_batches) / total_batches * 100
            
            self.current_schedule['status'] = 'completed'
            self.current_schedule['completed_time'] = datetime.now()
            self.current_schedule['success_rate'] = success_rate
            
            # Update global statistics
            self._update_global_statistics()
            
            logger.info(f"Schedule completed with {success_rate:.1f}% success rate")
    
    def _update_global_statistics(self):
        """Update global scheduler statistics"""
        
        if not self.current_schedule:
            return
        
        total_schedules = self.stats['total_schedules_created']
        current_success_rate = self.current_schedule.get('success_rate', 0)
        
        # Update average success rate
        if total_schedules > 0:
            old_avg = self.stats['average_success_rate']
            self.stats['average_success_rate'] = (
                (old_avg * (total_schedules - 1) + current_success_rate) / total_schedules
            )
    
    def get_current_schedule_status(self) -> Dict[str, Any]:
        """Get current schedule status and progress"""
        
        if not self.current_schedule:
            return {'status': 'no_schedule'}
        
        total_batches = len(self.completed_batches) + len(self.failed_batches) + len(self.active_batches)
        completed_batches = len(self.completed_batches)
        failed_batches = len(self.failed_batches)
        pending_batches = len(self.active_batches)
        
        progress = (completed_batches + failed_batches) / total_batches * 100 if total_batches > 0 else 0
        
        next_batch = None
        if self.active_batches:
            next_batch_obj = min(self.active_batches, key=lambda b: b.scheduled_time)
            next_batch = {
                'batch_id': next_batch_obj.batch_id,
                'scheduled_time': next_batch_obj.scheduled_time.isoformat(),
                'email_count': len(next_batch_obj.emails)
            }
        
        return {
            'status': self.current_schedule.get('status', 'unknown'),
            'schedule_id': self.current_schedule.get('schedule_id'),
            'created_time': self.current_schedule.get('created_time'),
            'started_time': self.current_schedule.get('started_time'),
            'progress_percentage': progress,
            'total_batches': total_batches,
            'completed_batches': completed_batches,
            'failed_batches': failed_batches,
            'pending_batches': pending_batches,
            'total_emails': self.current_schedule.get('total_emails', 0),
            'next_batch': next_batch,
            'is_running': self.is_running
        }
    
    def get_schedule_history(self) -> List[Dict[str, Any]]:
        """Get history of all schedules"""
        return self.schedule_history.copy()
    
    def get_active_schedule_count(self) -> int:
        """Get number of active schedules"""
        return 1 if self.current_schedule and self.is_running else 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive scheduler statistics"""
        current_status = self.get_current_schedule_status()
        
        return {
            'global_stats': self.stats.copy(),
            'current_schedule': current_status,
            'batch_summary': {
                'active_batches': len(self.active_batches),
                'completed_batches': len(self.completed_batches),
                'failed_batches': len(self.failed_batches)
            },
            'system_status': {
                'is_running': self.is_running,
                'scheduler_thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False
            }
        }
    
    def _save_schedule(self, schedule_data: Dict[str, Any]):
        """Save schedule to file"""
        try:
            schedule_id = schedule_data['schedule_id']
            filename = f"schedule_{schedule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.schedules_dir / filename
            
            # Convert datetime objects to ISO format for JSON serialization
            serializable_data = self._make_json_serializable(schedule_data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Schedule saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")
    
    def _make_json_serializable(self, data: Any) -> Any:
        """Convert data to JSON serializable format"""
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {key: self._make_json_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._make_json_serializable(item) for item in data]
        else:
            return data
    
    def _load_saved_schedules(self):
        """Load previously saved schedules"""
        try:
            schedule_files = list(self.schedules_dir.glob("schedule_*.json"))
            
            for schedule_file in sorted(schedule_files)[-10:]:  # Load last 10 schedules
                try:
                    with open(schedule_file, 'r', encoding='utf-8') as f:
                        schedule_data = json.load(f)
                    
                    self.schedule_history.append(schedule_data)
                    
                except Exception as e:
                    logger.warning(f"Error loading schedule file {schedule_file}: {e}")
            
            if self.schedule_history:
                logger.info(f"Loaded {len(self.schedule_history)} schedule(s) from history")
                
        except Exception as e:
            logger.warning(f"Error loading saved schedules: {e}")
    
    def export_schedule_report(self, filepath: str) -> bool:
        """Export detailed schedule report"""
        try:
            report_data = {
                'report_info': {
                    'generated_time': datetime.now().isoformat(),
                    'report_type': 'schedule_report',
                    'version': '4.0'
                },
                'current_schedule': self.get_current_schedule_status(),
                'statistics': self.get_statistics(),
                'batch_details': [
                    {
                        'batch_id': batch.batch_id,
                        'status': batch.status,
                        'email_count': len(batch.emails),
                        'scheduled_time': batch.scheduled_time.isoformat(),
                        'sent_time': batch.sent_time.isoformat() if batch.sent_time else None,
                        'attempts': batch.attempts,
                        'error_message': batch.error_message
                    }
                    for batch in (self.completed_batches + self.failed_batches + self.active_batches)
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Schedule report exported to: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting schedule report: {e}")
            return False
    
    def health_check(self) -> bool:
        """Perform health check on scheduler"""
        try:
            # Check if scheduler components are accessible
            if not hasattr(self, 'active_batches'):
                return False
            
            # Check if email processor is available
            if not self.email_processor:
                return False
            
            # Check if config manager is available
            if not self.config_manager:
                return False
            
            # Test schedule module
            schedule.clear()
            test_job = schedule.every().day.at("23:59").do(lambda: None)
            schedule.cancel_job(test_job)
            
            return True
            
        except Exception as e:
            logger.error(f"Scheduler health check failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup scheduler resources"""
        try:
            # Stop any running schedule
            if self.is_running:
                self.stop_schedule()
            
            # Clear all scheduled jobs
            schedule.clear()
            
            # Clear data structures
            self.active_batches.clear()
            self.completed_batches.clear()
            self.failed_batches.clear()
            
            logger.info("Scheduler manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during scheduler cleanup: {e}")