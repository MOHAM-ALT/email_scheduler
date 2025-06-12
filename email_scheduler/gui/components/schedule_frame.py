# gui/components/schedule_frame.py
"""
Schedule Frame - Email Scheduling Component
Handles schedule creation, management, and execution
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import logging
from datetime import datetime
from ..utils.gui_utils import GuiUtils

logger = logging.getLogger(__name__)

class ScheduleFrame:
    """Email scheduling and management component"""
    
    def __init__(self, parent, app_manager, config_manager):
        self.parent = parent
        self.app_manager = app_manager
        self.config_manager = config_manager
        
        # Create main frame
        self.frame = tk.Frame(parent, bg='#f5f6fa')
        
        # Schedule settings variables
        self.emails_per_day_var = tk.IntVar(value=499)
        self.emails_per_batch_var = tk.IntVar(value=10)
        self.start_time_var = tk.StringVar(value="06:00")
        self.working_days_var = tk.BooleanVar(value=True)
        
        # UI elements
        self.schedule_preview = None
        
        # Create scheduling interface
        self._create_interface()
        
        # Load configuration
        self._load_config()
    
    def _create_interface(self):
        """Create scheduling interface"""
        try:
            # Settings section
            settings_section = GuiUtils.create_label_frame(self.frame, "⚙️ Schedule Settings")
            settings_section.pack(fill='x', padx=20, pady=10)
            
            settings_grid = tk.Frame(settings_section, bg='white')
            settings_grid.pack(padx=20, pady=15)
            
            # Emails per day
            tk.Label(
                settings_grid,
                text="Emails per day:",
                font=('Segoe UI', 10),
                bg='white'
            ).grid(row=0, column=0, sticky='w', padx=10, pady=8)
            
            emails_per_day_entry = tk.Entry(
                settings_grid,
                textvariable=self.emails_per_day_var,
                font=('Segoe UI', 10),
                width=10
            )
            emails_per_day_entry.grid(row=0, column=1, padx=10, pady=8)
            
            # Emails per batch
            tk.Label(
                settings_grid,
                text="Emails per batch:",
                font=('Segoe UI', 10),
                bg='white'
            ).grid(row=0, column=2, sticky='w', padx=10, pady=8)
            
            emails_per_batch_entry = tk.Entry(
                settings_grid,
                textvariable=self.emails_per_batch_var,
                font=('Segoe UI', 10),
                width=10
            )
            emails_per_batch_entry.grid(row=0, column=3, padx=10, pady=8)
            
            # Start time
            tk.Label(
                settings_grid,
                text="Start time:",
                font=('Segoe UI', 10),
                bg='white'
            ).grid(row=1, column=0, sticky='w', padx=10, pady=8)
            
            start_time_entry = tk.Entry(
                settings_grid,
                textvariable=self.start_time_var,
                font=('Segoe UI', 10),
                width=10
            )
            start_time_entry.grid(row=1, column=1, padx=10, pady=8)
            
            # Working days only
            working_days_cb = tk.Checkbutton(
                settings_grid,
                text="Working days only",
                variable=self.working_days_var,
                font=('Segoe UI', 10),
                bg='white'
            )
            working_days_cb.grid(row=1, column=2, columnspan=2, sticky='w', padx=10, pady=8)
            
            # Control buttons
            control_section = GuiUtils.create_label_frame(self.frame, "🎯 Schedule Control")
            control_section.pack(fill='x', padx=20, pady=10)
            
            control_frame = tk.Frame(control_section, bg='white')
            control_frame.pack(pady=15)
            
            # Control buttons
            GuiUtils.create_styled_button(
                control_frame,
                "📅 Create Schedule",
                command=self._create_schedule,
                style="success"
            ).pack(side='left', padx=5)
            
            GuiUtils.create_styled_button(
                control_frame,
                "🚀 Start Sending",
                command=self._start_sending,
                style="default"
            ).pack(side='left', padx=5)
            
            GuiUtils.create_styled_button(
                control_frame,
                "⏹️ Stop Sending",
                command=self._stop_sending,
                style="danger"
            ).pack(side='left', padx=5)
            
            GuiUtils.create_styled_button(
                control_frame,
                "💾 Save Schedule",
                command=self._save_schedule,
                style="secondary"
            ).pack(side='left', padx=5)
            
            # Schedule preview section
            preview_section = GuiUtils.create_label_frame(self.frame, "📋 Schedule Preview")
            preview_section.pack(fill='both', expand=True, padx=20, pady=10)
            
            self.schedule_preview = scrolledtext.ScrolledText(
                preview_section,
                font=('Consolas', 9),
                bg='#2c3e50',
                fg='#ecf0f1',
                wrap='word'
            )
            self.schedule_preview.pack(fill='both', expand=True, padx=20, pady=15)
            
            # Initial preview text
            self._update_preview("No schedule created yet. Create a schedule to see the preview.")
            
        except Exception as e:
            logger.error(f"Error creating schedule interface: {e}")
    
    def _load_config(self):
        """Load configuration settings"""
        try:
            if self.config_manager:
                schedule_settings = self.config_manager.get_schedule_settings()
                
                self.emails_per_day_var.set(schedule_settings.emails_per_day)
                self.emails_per_batch_var.set(schedule_settings.emails_per_batch)
                self.start_time_var.set(schedule_settings.start_time)
                self.working_days_var.set(schedule_settings.working_days_only)
                
        except Exception as e:
            logger.error(f"Error loading schedule config: {e}")
    
    def _create_schedule(self):
        """Create email schedule"""
        try:
            # Validate inputs
            if not self._validate_settings():
                return
            
            # Get email processor
            email_processor = self.app_manager.get_email_processor()
            if not email_processor:
                messagebox.showerror("Error", "Email processor not available")
                return
            
            # Check if emails are loaded
            stats = email_processor.get_statistics()
            if stats.get('total_emails', 0) == 0:
                messagebox.showwarning("Warning", "No emails loaded. Please load an email list first.")
                return
            
            # Get email data from setup frame (if available)
            email_data = self._get_email_data()
            if not email_data['subject'].strip():
                messagebox.showwarning("Warning", "Please enter an email subject")
                return
            
            if not email_data['body'].strip():
                messagebox.showwarning("Warning", "Please enter an email message")
                return
            
            # Get valid emails
            valid_emails = [email.address for email in email_processor.get_valid_emails()]
            
            if not valid_emails:
                messagebox.showerror("Error", "No valid emails found")
                return
            
            # Create schedule
            scheduler_manager = self.app_manager.get_scheduler_manager()
            if not scheduler_manager:
                messagebox.showerror("Error", "Scheduler manager not available")
                return
            
            # Create schedule settings
            from core.scheduler_manager import ScheduleSettings
            schedule_settings = ScheduleSettings(
                emails_per_day=self.emails_per_day_var.get(),
                emails_per_batch=self.emails_per_batch_var.get(),
                start_time=self.start_time_var.get(),
                working_days_only=self.working_days_var.get()
            )
            
            # Create schedule
            result = scheduler_manager.create_schedule(
                emails=valid_emails,
                subject=email_data['subject'],
                body=email_data['body'],
                attachments=email_data.get('attachments', []),
                schedule_settings=schedule_settings
            )
            
            if result.success:
                messagebox.showinfo(
                    "Success", 
                    f"Schedule created successfully!\n\n"
                    f"Total Batches: {result.total_batches}\n"
                    f"Total Days: {result.total_days}\n"
                    f"Start Date: {result.start_date.strftime('%Y-%m-%d') if result.start_date else 'N/A'}\n"
                    f"End Date: {result.end_date.strftime('%Y-%m-%d') if result.end_date else 'N/A'}"
                )
                
                # Update preview
                self._update_schedule_preview()
                
            else:
                messagebox.showerror("Error", f"Failed to create schedule: {result.message}")
                
        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            messagebox.showerror("Error", f"Failed to create schedule: {e}")
    
    def _validate_settings(self):
        """Validate schedule settings"""
        try:
            emails_per_day = self.emails_per_day_var.get()
            emails_per_batch = self.emails_per_batch_var.get()
            start_time = self.start_time_var.get()
            
            # Validate emails per day
            if emails_per_day < 1 or emails_per_day > 1000:
                messagebox.showerror("Error", "Emails per day must be between 1 and 1000")
                return False
            
            # Validate emails per batch
            if emails_per_batch < 1 or emails_per_batch > 50:
                messagebox.showerror("Error", "Emails per batch must be between 1 and 50")
                return False
            
            if emails_per_batch > emails_per_day:
                messagebox.showerror("Error", "Emails per batch cannot exceed emails per day")
                return False
            
            # Validate time format
            try:
                time_parts = start_time.split(':')
                if len(time_parts) != 2:
                    raise ValueError("Invalid format")
                hour, minute = int(time_parts[0]), int(time_parts[1])
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("Invalid time range")
            except ValueError:
                messagebox.showerror("Error", "Start time must be in HH:MM format (00:00 to 23:59)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating settings: {e}")
            return False
    
    def _get_email_data(self):
        """Get email data from the application"""
        try:
            # Try to get data from parent window frames
            if hasattr(self.parent, 'master') and hasattr(self.parent.master, 'frames'):
                frames = self.parent.master.frames
                if 'email_setup' in frames:
                    return frames['email_setup'].get_email_data()
            
            # Default values if not available
            return {
                'subject': 'Important Email with Attachments',
                'body': 'Dear Recipient,\n\nPlease find the attached important information.\n\nBest regards',
                'attachments': []
            }
            
        except Exception as e:
            logger.error(f"Error getting email data: {e}")
            return {
                'subject': 'Important Email',
                'body': 'Default message',
                'attachments': []
            }
    
    def _start_sending(self):
        """Start email sending"""
        try:
            scheduler_manager = self.app_manager.get_scheduler_manager()
            if not scheduler_manager:
                messagebox.showerror("Error", "Scheduler manager not available")
                return
            
            # Check if schedule exists
            current_status = scheduler_manager.get_current_schedule_status()
            if current_status.get('status') == 'no_schedule':
                messagebox.showwarning("Warning", "No schedule created. Please create a schedule first.")
                return
            
            # Check Outlook connection
            outlook_manager = self.app_manager.get_outlook_manager()
            if not outlook_manager or not outlook_manager.is_connected():
                messagebox.showerror("Error", "Outlook not connected. Please check Outlook connection.")
                return
            
            # Confirm start
            pending_batches = current_status.get('pending_batches', 0)
            if not messagebox.askyesno(
                "Confirm Start",
                f"Are you sure you want to start sending {pending_batches} email batches?\n\n"
                f"This will begin the automated email sending process."
            ):
                return
            
            # Start sending
            success = scheduler_manager.start_schedule()
            
            if success:
                messagebox.showinfo("Success", "Email sending started successfully!")
                self._update_schedule_preview()
            else:
                messagebox.showerror("Error", "Failed to start email sending")
                
        except Exception as e:
            logger.error(f"Error starting email sending: {e}")
            messagebox.showerror("Error", f"Failed to start sending: {e}")
    
    def _stop_sending(self):
        """Stop email sending"""
        try:
            scheduler_manager = self.app_manager.get_scheduler_manager()
            if not scheduler_manager:
                messagebox.showerror("Error", "Scheduler manager not available")
                return
            
            # Check if sending is active
            current_status = scheduler_manager.get_current_schedule_status()
            if not current_status.get('is_running', False):
                messagebox.showinfo("Info", "No email sending is currently active")
                return
            
            # Confirm stop
            if not messagebox.askyesno(
                "Confirm Stop",
                "Are you sure you want to stop the email sending process?\n\n"
                f"This will halt all pending email batches."
            ):
                return
            
            # Stop sending
            success = scheduler_manager.stop_schedule()
            
            if success:
                messagebox.showinfo("Success", "Email sending stopped successfully!")
                self._update_schedule_preview()
            else:
                messagebox.showerror("Error", "Failed to stop email sending")
                
        except Exception as e:
            logger.error(f"Error stopping email sending: {e}")
            messagebox.showerror("Error", f"Failed to stop sending: {e}")
    
    def _save_schedule(self):
        """Save current schedule"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save Schedule",
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel files", "*.xlsx"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                scheduler_manager = self.app_manager.get_scheduler_manager()
                if scheduler_manager:
                    success = scheduler_manager.export_schedule_report(file_path)
                    
                    if success:
                        messagebox.showinfo("Success", f"Schedule saved successfully to:\n{file_path}")
                    else:
                        messagebox.showerror("Error", "Failed to save schedule")
                else:
                    messagebox.showerror("Error", "Scheduler manager not available")
                    
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")
            messagebox.showerror("Error", f"Failed to save schedule: {e}")
    
    def _update_schedule_preview(self):
        """Update schedule preview display"""
        try:
            scheduler_manager = self.app_manager.get_scheduler_manager()
            if not scheduler_manager:
                self._update_preview("Scheduler manager not available")
                return
            
            # Get current schedule status
            current_status = scheduler_manager.get_current_schedule_status()
            
            if current_status.get('status') == 'no_schedule':
                self._update_preview("No schedule created yet. Create a schedule to see the preview.")
                return
            
            # Generate preview text
            preview_lines = [
                "PROFESSIONAL EMAIL SCHEDULER v4.0",
                "=" * 60,
                "",
                f"Schedule Status: {current_status.get('status', 'Unknown').upper()}",
                f"Created: {current_status.get('created_time', 'Unknown')}",
                f"Total Emails: {current_status.get('total_emails', 0):,}",
                "",
                "BATCH INFORMATION:",
                "-" * 30,
                f"Total Batches: {current_status.get('total_batches', 0)}",
                f"Completed Batches: {current_status.get('completed_batches', 0)}",
                f"Failed Batches: {current_status.get('failed_batches', 0)}",
                f"Pending Batches: {current_status.get('pending_batches', 0)}",
                "",
                f"Progress: {current_status.get('progress_percentage', 0):.1f}%",
                ""
            ]
            
            # Add next batch information
            next_batch = current_status.get('next_batch')
            if next_batch:
                preview_lines.extend([
                    "NEXT BATCH:",
                    "-" * 15,
                    f"Batch ID: {next_batch.get('batch_id', 'Unknown')}",
                    f"Scheduled Time: {next_batch.get('scheduled_time', 'Unknown')}",
                    f"Email Count: {next_batch.get('email_count', 0)}",
                    ""
                ])
            
            # Add running status
            if current_status.get('is_running', False):
                preview_lines.extend([
                    "STATUS: 🟢 ACTIVE - Email sending is running",
                    "Keep Outlook running and monitor progress",
                    ""
                ])
            else:
                preview_lines.extend([
                    "STATUS: 🔴 INACTIVE - Email sending is stopped",
                    "Click 'Start Sending' to begin",
                    ""
                ])
            
            # Add schedule settings
            preview_lines.extend([
                "SCHEDULE SETTINGS:",
                "-" * 20,
                f"Emails per Day: {self.emails_per_day_var.get()}",
                f"Emails per Batch: {self.emails_per_batch_var.get()}",
                f"Start Time: {self.start_time_var.get()}",
                f"Working Days Only: {'Yes' if self.working_days_var.get() else 'No'}",
                "",
                "=" * 60,
                "Ready for professional email management!"
            ])
            
            preview_text = "\n".join(preview_lines)
            self._update_preview(preview_text)
            
        except Exception as e:
            logger.error(f"Error updating schedule preview: {e}")
            self._update_preview(f"Error updating preview: {e}")
    
    def _update_preview(self, text):
        """Update preview text widget"""
        try:
            if self.schedule_preview:
                self.schedule_preview.delete('1.0', tk.END)
                self.schedule_preview.insert('1.0', text)
        except Exception as e:
            logger.error(f"Error updating preview text: {e}")
    
    def new_schedule(self):
        """Create new schedule (public method)"""
        self._create_schedule()
    
    def load_schedule(self, file_path):
        """Load schedule from file (public method)"""
        try:
            # Implementation for loading schedule from file
            messagebox.showinfo("Info", f"Loading schedule from: {file_path}")
        except Exception as e:
            logger.error(f"Error loading schedule: {e}")
            messagebox.showerror("Error", f"Failed to load schedule: {e}")
    
    def save_schedule(self):
        """Save current schedule (public method)"""
        self._save_schedule()
    
    def save_schedule_as(self):
        """Save schedule with new name (public method)"""
        self._save_schedule()
    
    def refresh(self):
        """Refresh schedule display"""
        try:
            self._update_schedule_preview()
        except Exception as e:
            logger.error(f"Error refreshing schedule: {e}")
    
    def cleanup(self):
        """Cleanup schedule resources"""
        pass