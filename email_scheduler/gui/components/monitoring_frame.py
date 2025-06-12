# gui/components/monitoring_frame.py
"""
Monitoring Frame - Real-time Monitoring Component
Displays real-time statistics, progress, and system health
"""

import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime
from ..utils.gui_utils import GuiUtils

logger = logging.getLogger(__name__)

class MonitoringFrame:
    """Real-time monitoring and statistics component"""
    
    def __init__(self, parent, app_manager, config_manager):
        self.parent = parent
        self.app_manager = app_manager
        self.config_manager = config_manager
        
        # Create main frame
        self.frame = tk.Frame(parent, bg='#f5f6fa')
        
        # Monitoring elements
        self.metric_widgets = {}
        self.chart_widgets = {}
        self.log_viewer = None
        
        # Create monitoring interface
        self._create_interface()
    
    def _create_interface(self):
        """Create monitoring interface"""
        try:
            # Statistics section
            stats_section = GuiUtils.create_label_frame(self.frame, "📊 Real-time Statistics")
            stats_section.pack(fill='x', padx=20, pady=10)
            
            stats_grid = tk.Frame(stats_section, bg='white')
            stats_grid.pack(fill='x', padx=20, pady=15)
            
            # Create metric displays
            metrics = [
                ('total_emails', 'Total Emails', 0),
                ('valid_emails', 'Valid Emails', 0),
                ('sent_emails', 'Sent', 0),
                ('failed_emails', 'Failed', 0),
                ('pending_emails', 'Pending', 0),
                ('success_rate', 'Success Rate', '0%')
            ]
            
            for i, (key, title, default_value) in enumerate(metrics):
                row, col = i // 3, i % 3
                
                metric_frame = GuiUtils.create_metric_display(
                    stats_grid, title, default_value
                )
                metric_frame.grid(row=row, column=col, sticky='ew', padx=10, pady=10)
                
                self.metric_widgets[key] = metric_frame
                
                # Configure column weights
                stats_grid.columnconfigure(col, weight=1)
            
            # Progress section
            progress_section = GuiUtils.create_label_frame(self.frame, "📈 Progress Tracking")
            progress_section.pack(fill='x', padx=20, pady=10)
            
            progress_frame = tk.Frame(progress_section, bg='white')
            progress_frame.pack(fill='x', padx=20, pady=15)
            
            # Overall progress
            tk.Label(
                progress_frame,
                text="Overall Progress:",
                font=('Segoe UI', 10, 'bold'),
                bg='white'
            ).pack(anchor='w')
            
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(
                progress_frame,
                variable=self.progress_var,
                maximum=100,
                length=500
            )
            self.progress_bar.pack(fill='x', pady=5)
            
            self.progress_label = tk.Label(
                progress_frame,
                text="0%",
                font=('Segoe UI', 10),
                bg='white'
            )
            self.progress_label.pack(anchor='w')
            
            # Current batch progress
            tk.Label(
                progress_frame,
                text="Current Batch:",
                font=('Segoe UI', 10, 'bold'),
                bg='white'
            ).pack(anchor='w', pady=(10, 0))
            
            self.batch_progress_var = tk.DoubleVar()
            self.batch_progress_bar = ttk.Progressbar(
                progress_frame,
                variable=self.batch_progress_var,
                maximum=100,
                length=500
            )
            self.batch_progress_bar.pack(fill='x', pady=5)
            
            self.batch_progress_label = tk.Label(
                progress_frame,
                text="No batch active",
                font=('Segoe UI', 10),
                bg='white'
            )
            self.batch_progress_label.pack(anchor='w')
            
            # Activity log section
            log_section = GuiUtils.create_label_frame(self.frame, "📝 Activity Log")
            log_section.pack(fill='both', expand=True, padx=20, pady=10)
            
            # Create log viewer
            self.log_viewer = GuiUtils.create_log_viewer(log_section, max_lines=500)
            
            # Add initial log entry
            self.log_viewer.add_log_entry("Monitoring system initialized", "INFO")
            
        except Exception as e:
            logger.error(f"Error creating monitoring interface: {e}")
    
    def update_display(self):
        """Update monitoring display with current data"""
        try:
            # Update email statistics
            self._update_email_statistics()
            
            # Update progress tracking
            self._update_progress()
            
            # Update system status logs
            self._update_activity_log()
            
        except Exception as e:
            logger.error(f"Error updating monitoring display: {e}")
    
    def _update_email_statistics(self):
        """Update email statistics metrics"""
        try:
            if not self.app_manager:
                return
            
            # Get email processor statistics
            email_processor = self.app_manager.get_email_processor()
            if email_processor:
                stats = email_processor.get_statistics()
                
                # Update metric displays
                self.metric_widgets['total_emails'].update_value(
                    stats.get('total_emails', 0)
                )
                
                valid_emails = stats.get('processing_stats', {}).get('valid_emails', 0)
                self.metric_widgets['valid_emails'].update_value(valid_emails)
                
                sent_emails = stats.get('processing_stats', {}).get('sent_emails', 0)
                self.metric_widgets['sent_emails'].update_value(sent_emails)
                
                failed_emails = stats.get('processing_stats', {}).get('failed_emails', 0)
                self.metric_widgets['failed_emails'].update_value(failed_emails)
                
                pending_emails = max(0, valid_emails - sent_emails - failed_emails)
                self.metric_widgets['pending_emails'].update_value(pending_emails)
                
                # Calculate success rate
                total_processed = sent_emails + failed_emails
                if total_processed > 0:
                    success_rate = (sent_emails / total_processed) * 100
                    self.metric_widgets['success_rate'].update_value(f"{success_rate:.1f}%")
                else:
                    self.metric_widgets['success_rate'].update_value("0%")
            
        except Exception as e:
            logger.error(f"Error updating email statistics: {e}")
    
    def _update_progress(self):
        """Update progress tracking"""
        try:
            if not self.app_manager:
                return
            
            # Get scheduler status
            scheduler_manager = self.app_manager.get_scheduler_manager()
            if scheduler_manager:
                current_status = scheduler_manager.get_current_schedule_status()
                
                if current_status.get('status') != 'no_schedule':
                    # Update overall progress
                    progress_percentage = current_status.get('progress_percentage', 0)
                    self.progress_var.set(progress_percentage)
                    self.progress_label.config(text=f"{progress_percentage:.1f}%")
                    
                    # Update batch information
                    next_batch = current_status.get('next_batch')
                    if next_batch and current_status.get('is_running', False):
                        batch_text = f"Next batch: {next_batch.get('email_count', 0)} emails at {next_batch.get('scheduled_time', 'Unknown')}"
                        self.batch_progress_label.config(text=batch_text)
                        self.batch_progress_var.set(50)  # Arbitrary progress for next batch
                    else:
                        if current_status.get('is_running', False):
                            self.batch_progress_label.config(text="Waiting for next batch...")
                            self.batch_progress_var.set(0)
                        else:
                            self.batch_progress_label.config(text="Scheduler not running")
                            self.batch_progress_var.set(0)
                else:
                    # No schedule
                    self.progress_var.set(0)
                    self.progress_label.config(text="No schedule created")
                    self.batch_progress_var.set(0)
                    self.batch_progress_label.config(text="No batch active")
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
    
    def _update_activity_log(self):
        """Update activity log with recent events"""
        try:
            # This would be called less frequently to avoid spam
            # Add significant events to the log
            current_time = datetime.now()
            
            # Check for system status changes
            if self.app_manager:
                system_status = self.app_manager.get_system_status()
                
                # Log Outlook connection status changes
                outlook_connected = system_status.get('outlook_connected', False)
                if hasattr(self, '_last_outlook_status') and self._last_outlook_status != outlook_connected:
                    if outlook_connected:
                        self.log_viewer.add_log_entry("Outlook connection established", "SUCCESS")
                    else:
                        self.log_viewer.add_log_entry("Outlook connection lost", "ERROR")
                
                self._last_outlook_status = outlook_connected
                
                # Log scheduler status changes
                scheduler_manager = self.app_manager.get_scheduler_manager()
                if scheduler_manager:
                    current_status = scheduler_manager.get_current_schedule_status()
                    is_running = current_status.get('is_running', False)
                    
                    if hasattr(self, '_last_scheduler_status') and self._last_scheduler_status != is_running:
                        if is_running:
                            self.log_viewer.add_log_entry("Email scheduler started", "SUCCESS")
                        else:
                            self.log_viewer.add_log_entry("Email scheduler stopped", "WARNING")
                    
                    self._last_scheduler_status = is_running
            
        except Exception as e:
            logger.error(f"Error updating activity log: {e}")
    
    def add_log_entry(self, message, level="INFO"):
        """Add entry to activity log"""
        try:
            if self.log_viewer:
                self.log_viewer.add_log_entry(message, level)
        except Exception as e:
            logger.error(f"Error adding log entry: {e}")
    
    def show_performance_details(self):
        """Show detailed performance information"""
        try:
            # Create performance dialog
            perf_dialog = tk.Toplevel(self.parent)
            perf_dialog.title("Performance Monitor")
            perf_dialog.geometry("700x500")
            perf_dialog.transient(self.parent)
            perf_dialog.grab_set()
            
            GuiUtils.center_window(perf_dialog, 700, 500)
            
            # Create notebook for different performance aspects
            notebook = ttk.Notebook(perf_dialog)
            notebook.pack(fill='both', expand=True, padx=20, pady=20)
            
            # System Performance tab
            system_tab = tk.Frame(notebook, bg='white')
            notebook.add(system_tab, text="System Performance")
            
            system_text = tk.Text(system_tab, font=('Consolas', 10), wrap='word')
            system_text.pack(fill='both', expand=True, padx=15, pady=15)
            
            # Generate system performance report
            performance_info = self._generate_performance_report()
            system_text.insert('1.0', performance_info)
            system_text.config(state='disabled')
            
            # Email Performance tab
            email_tab = tk.Frame(notebook, bg='white')
            notebook.add(email_tab, text="Email Performance")
            
            email_text = tk.Text(email_tab, font=('Consolas', 10), wrap='word')
            email_text.pack(fill='both', expand=True, padx=15, pady=15)
            
            # Generate email performance report
            email_performance = self._generate_email_performance_report()
            email_text.insert('1.0', email_performance)
            email_text.config(state='disabled')
            
            # Close button
            GuiUtils.create_styled_button(
                perf_dialog,
                "Close",
                command=perf_dialog.destroy,
                style="secondary"
            ).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error showing performance details: {e}")
    
    def _generate_performance_report(self):
        """Generate system performance report"""
        try:
            report_lines = [
                "SYSTEM PERFORMANCE REPORT",
                "=" * 40,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "APPLICATION STATUS:",
                "-" * 20
            ]
            
            if self.app_manager:
                system_status = self.app_manager.get_system_status()
                
                report_lines.extend([
                    f"Initialized: {'Yes' if system_status.get('initialized', False) else 'No'}",
                    f"Running: {'Yes' if system_status.get('running', False) else 'No'}",
                    f"Components: {len(system_status.get('components', []))}",
                    f"Uptime: {system_status.get('uptime', 0):.1f} seconds",
                    ""
                ])
                
                # Component health
                health_status = system_status.get('health_status', {})
                if health_status:
                    report_lines.extend([
                        "COMPONENT HEALTH:",
                        "-" * 20
                    ])
                    
                    for component, health in health_status.items():
                        status = health.get('status', 'unknown')
                        report_lines.append(f"{component}: {status}")
                    
                    report_lines.append("")
            
            # System resources (if available)
            try:
                import psutil
                
                report_lines.extend([
                    "SYSTEM RESOURCES:",
                    "-" * 20,
                    f"CPU Usage: {psutil.cpu_percent()}%",
                    f"Memory Usage: {psutil.virtual_memory().percent}%",
                    f"Available Memory: {psutil.virtual_memory().available / (1024**3):.2f} GB",
                    ""
                ])
                
            except ImportError:
                report_lines.extend([
                    "SYSTEM RESOURCES:",
                    "-" * 20,
                    "Resource information not available (psutil not installed)",
                    ""
                ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return f"Error generating performance report: {e}"
    
    def _generate_email_performance_report(self):
        """Generate email performance report"""
        try:
            report_lines = [
                "EMAIL PERFORMANCE REPORT",
                "=" * 40,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ""
            ]
            
            if self.app_manager:
                # Email processor statistics
                email_processor = self.app_manager.get_email_processor()
                if email_processor:
                    stats = email_processor.get_statistics()
                    
                    report_lines.extend([
                        "EMAIL PROCESSING:",
                        "-" * 20,
                        f"Total Emails: {stats.get('total_emails', 0):,}",
                        f"Valid Emails: {stats.get('processing_stats', {}).get('valid_emails', 0):,}",
                        f"Invalid Emails: {stats.get('processing_stats', {}).get('invalid_emails', 0):,}",
                        f"Sent Emails: {stats.get('processing_stats', {}).get('sent_emails', 0):,}",
                        f"Failed Emails: {stats.get('processing_stats', {}).get('failed_emails', 0):,}",
                        ""
                    ])
                
                # Scheduler statistics
                scheduler_manager = self.app_manager.get_scheduler_manager()
                if scheduler_manager:
                    scheduler_stats = scheduler_manager.get_statistics()
                    
                    report_lines.extend([
                        "SCHEDULER PERFORMANCE:",
                        "-" * 20,
                        f"Active Batches: {scheduler_stats.get('batch_summary', {}).get('active_batches', 0)}",
                        f"Completed Batches: {scheduler_stats.get('batch_summary', {}).get('completed_batches', 0)}",
                        f"Failed Batches: {scheduler_stats.get('batch_summary', {}).get('failed_batches', 0)}",
                        ""
                    ])
                
                # Outlook statistics
                outlook_manager = self.app_manager.get_outlook_manager()
                if outlook_manager:
                    outlook_stats = outlook_manager.get_statistics()
                    
                    report_lines.extend([
                        "OUTLOOK INTEGRATION:",
                        "-" * 20,
                        f"Connection Status: {'Connected' if outlook_manager.is_connected() else 'Disconnected'}",
                        f"Emails Sent: {outlook_stats.get('email_statistics', {}).get('emails_sent', 0)}",
                        f"Send Failures: {outlook_stats.get('email_statistics', {}).get('emails_failed', 0)}",
                        f"Success Rate: {outlook_stats.get('email_statistics', {}).get('success_rate', 0):.1f}%",
                        ""
                    ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error generating email performance report: {e}")
            return f"Error generating email performance report: {e}"
    
    def refresh(self):
        """Refresh monitoring data"""
        self.update_display()
    
    def cleanup(self):
        """Cleanup monitoring resources"""
        pass