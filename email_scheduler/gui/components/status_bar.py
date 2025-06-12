# gui/components/status_bar.py
"""
Status Bar Component - Application Status Display
Comprehensive status bar with system information, progress, and health indicators
"""

import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime
import threading
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StatusBar:
    """Professional status bar with comprehensive status information"""
    
    def __init__(self, parent, app_manager):
        self.parent = parent
        self.app_manager = app_manager
        
        # Status bar frame
        self.frame = tk.Frame(parent, bg='#34495e', height=30)
        self.frame.pack(fill='x', side='bottom')
        self.frame.pack_propagate(False)
        
        # Status elements
        self.status_elements = {}
        self.progress_elements = {}
        
        # Update thread control
        self.update_active = True
        self.update_thread = None
        
        # Create status bar elements
        self._create_status_elements()
        
        # Start update thread
        self._start_update_thread()
        
    def _create_status_elements(self):
        """Create all status bar elements"""
        try:
            # Left section - Main status message
            left_frame = tk.Frame(self.frame, bg='#34495e')
            left_frame.pack(side='left', fill='x', expand=True)
            
            # Status message
            self.status_elements['message'] = tk.Label(
                left_frame,
                text="Professional Email Scheduler Ready",
                font=('Segoe UI', 9),
                bg='#34495e',
                fg='white',
                anchor='w'
            )
            self.status_elements['message'].pack(side='left', padx=10, pady=5)
            
            # Progress bar (initially hidden)
            self.progress_elements['bar'] = ttk.Progressbar(
                left_frame,
                length=200,
                mode='determinate'
            )
            
            self.progress_elements['label'] = tk.Label(
                left_frame,
                text="",
                font=('Segoe UI', 8),
                bg='#34495e',
                fg='#bdc3c7'
            )
            
            # Center section - System status indicators
            center_frame = tk.Frame(self.frame, bg='#34495e')
            center_frame.pack(side='left', padx=20)
            
            # Outlook status
            self.status_elements['outlook'] = self._create_status_indicator(
                center_frame, "Outlook", "checking"
            )
            self.status_elements['outlook'].pack(side='left', padx=5)
            
            # Email processor status
            self.status_elements['processor'] = self._create_status_indicator(
                center_frame, "Processor", "ready"
            )
            self.status_elements['processor'].pack(side='left', padx=5)
            
            # Scheduler status
            self.status_elements['scheduler'] = self._create_status_indicator(
                center_frame, "Scheduler", "idle"
            )
            self.status_elements['scheduler'].pack(side='left', padx=5)
            
            # Right section - System information
            right_frame = tk.Frame(self.frame, bg='#34495e')
            right_frame.pack(side='right', padx=10)
            
            # Email statistics
            self.status_elements['stats'] = tk.Label(
                right_frame,
                text="Emails: 0 | Sent: 0",
                font=('Segoe UI', 8),
                bg='#34495e',
                fg='#bdc3c7'
            )
            self.status_elements['stats'].pack(side='left', padx=5)
            
            # Time display
            self.status_elements['time'] = tk.Label(
                right_frame,
                text="",
                font=('Segoe UI', 8),
                bg='#34495e',
                fg='#bdc3c7'
            )
            self.status_elements['time'].pack(side='left', padx=5)
            
            # Version info
            self.status_elements['version'] = tk.Label(
                right_frame,
                text="v4.0",
                font=('Segoe UI', 8),
                bg='#34495e',
                fg='#95a5a6'
            )
            self.status_elements['version'].pack(side='right', padx=5)
            
            logger.debug("Status bar elements created")
            
        except Exception as e:
            logger.error(f"Error creating status bar elements: {e}")
    
    def _create_status_indicator(self, parent, label, initial_status):
        """Create a status indicator with colored dot"""
        try:
            frame = tk.Frame(parent, bg='#34495e')
            
            # Status colors
            status_colors = {
                'ready': '#2ecc71',
                'active': '#3498db',
                'warning': '#f39c12',
                'error': '#e74c3c',
                'checking': '#f39c12',
                'idle': '#95a5a6',
                'offline': '#7f8c8d'
            }
            
            # Create indicator canvas
            canvas = tk.Canvas(frame, width=10, height=10, bg='#34495e', highlightthickness=0)
            canvas.pack(side='left', padx=(0, 3))
            
            # Create status label
            label_widget = tk.Label(
                frame,
                text=label,
                font=('Segoe UI', 8),
                bg='#34495e',
                fg='#bdc3c7'
            )
            label_widget.pack(side='left')
            
            # Update function
            def update_status(status, tooltip=None):
                try:
                    color = status_colors.get(status, status_colors['offline'])
                    canvas.delete("all")
                    canvas.create_oval(2, 2, 8, 8, fill=color, outline=color)
                    
                    if tooltip:
                        self._add_tooltip(frame, tooltip)
                        
                except Exception as e:
                    logger.error(f"Error updating status indicator: {e}")
            
            frame.update_status = update_status
            frame.canvas = canvas
            frame.label = label_widget
            
            # Set initial status
            update_status(initial_status)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error creating status indicator: {e}")
            return tk.Frame(parent, bg='#34495e')
    
    def _add_tooltip(self, widget, text):
        """Add tooltip to widget"""
        try:
            def show_tooltip(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                label = tk.Label(
                    tooltip,
                    text=text,
                    background='#2c3e50',
                    foreground='white',
                    relief='solid',
                    borderwidth=1,
                    font=('Segoe UI', 8)
                )
                label.pack()
                
                widget.tooltip = tooltip
                tooltip.after(3000, tooltip.destroy)
            
            def hide_tooltip(event):
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
            
            widget.bind('<Enter>', show_tooltip)
            widget.bind('<Leave>', hide_tooltip)
            
        except Exception as e:
            logger.error(f"Error adding tooltip: {e}")
    
    def _start_update_thread(self):
        """Start background update thread"""
        try:
            def update_loop():
                while self.update_active:
                    try:
                        self._update_status_elements()
                        time.sleep(2)  # Update every 2 seconds
                    except Exception as e:
                        logger.error(f"Error in status update loop: {e}")
                        time.sleep(5)  # Wait longer on error
            
            self.update_thread = threading.Thread(target=update_loop, daemon=True)
            self.update_thread.start()
            
            logger.debug("Status bar update thread started")
            
        except Exception as e:
            logger.error(f"Error starting status update thread: {e}")
    
    def _update_status_elements(self):
        """Update all status elements"""
        try:
            # Update time
            current_time = datetime.now().strftime("%H:%M:%S")
            self.parent.after(0, lambda: self.status_elements['time'].config(text=current_time))
            
            # Update system status indicators
            self._update_outlook_status()
            self._update_processor_status()
            self._update_scheduler_status()
            self._update_statistics()
            
        except Exception as e:
            logger.error(f"Error updating status elements: {e}")
    
    def _update_outlook_status(self):
        """Update Outlook connection status"""
        try:
            outlook_manager = self.app_manager.get_outlook_manager()
            
            if outlook_manager:
                if outlook_manager.is_connected():
                    status = "ready"
                    tooltip = "Outlook connected and ready"
                elif outlook_manager.is_available():
                    status = "warning"
                    tooltip = "Outlook available but not connected"
                else:
                    status = "error"
                    tooltip = "Outlook not available"
            else:
                status = "offline"
                tooltip = "Outlook manager not initialized"
            
            def update():
                self.status_elements['outlook'].update_status(status, tooltip)
            
            self.parent.after(0, update)
            
        except Exception as e:
            logger.error(f"Error updating Outlook status: {e}")
    
    def _update_processor_status(self):
        """Update email processor status"""
        try:
            email_processor = self.app_manager.get_email_processor()
            
            if email_processor:
                if hasattr(email_processor, 'is_processing') and email_processor.is_processing:
                    status = "active"
                    tooltip = "Processing emails"
                else:
                    status = "ready"
                    tooltip = "Email processor ready"
            else:
                status = "offline"
                tooltip = "Email processor not available"
            
            def update():
                self.status_elements['processor'].update_status(status, tooltip)
            
            self.parent.after(0, update)
            
        except Exception as e:
            logger.error(f"Error updating processor status: {e}")
    
    def _update_scheduler_status(self):
        """Update scheduler status"""
        try:
            scheduler_manager = self.app_manager.get_scheduler_manager()
            
            if scheduler_manager:
                if hasattr(scheduler_manager, 'is_running') and scheduler_manager.is_running():
                    status = "active"
                    tooltip = "Scheduler running"
                else:
                    status = "idle"
                    tooltip = "Scheduler idle"
            else:
                status = "offline"
                tooltip = "Scheduler not available"
            
            def update():
                self.status_elements['scheduler'].update_status(status, tooltip)
            
            self.parent.after(0, update)
            
        except Exception as e:
            logger.error(f"Error updating scheduler status: {e}")
    
    def _update_statistics(self):
        """Update email statistics display"""
        try:
            email_processor = self.app_manager.get_email_processor()
            
            if email_processor:
                stats = email_processor.get_statistics()
                total_emails = stats.get('total_emails', 0)
                sent_emails = stats.get('processing_stats', {}).get('sent_emails', 0)
                
                stats_text = f"Emails: {total_emails} | Sent: {sent_emails}"
            else:
                stats_text = "Emails: 0 | Sent: 0"
            
            def update():
                self.status_elements['stats'].config(text=stats_text)
            
            self.parent.after(0, update)
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def set_message(self, message):
        """Set main status message"""
        try:
            def update():
                self.status_elements['message'].config(text=message)
            
            self.parent.after(0, update)
            
        except Exception as e:
            logger.error(f"Error setting status message: {e}")
    
    def show_progress(self, percentage, message=""):
        """Show progress bar with percentage and message"""
        try:
            def update():
                # Show progress elements
                if not self.progress_elements['bar'].winfo_viewable():
                    self.progress_elements['bar'].pack(side='left', padx=10)
                
                if message and not self.progress_elements['label'].winfo_viewable():
                    self.progress_elements['label'].pack(side='left', padx=5)
                
                # Update values
                self.progress_elements['bar']['value'] = percentage
                
                if message:
                    self.progress_elements['label'].config(text=message)
            
            self.parent.after(0, update)
            
        except Exception as e:
            logger.error(f"Error showing progress: {e}")
    
    def hide_progress(self):
        """Hide progress bar"""
        try:
            def update():
                self.progress_elements['bar'].pack_forget()
                self.progress_elements['label'].pack_forget()
            
            self.parent.after(0, update)
            
        except Exception as e:
            logger.error(f"Error hiding progress: {e}")
    
    def set_progress(self, percentage, message=""):
        """Set progress percentage and optional message"""
        try:
            if percentage < 0:
                self.hide_progress()
            else:
                self.show_progress(min(percentage, 100), message)
                
        except Exception as e:
            logger.error(f"Error setting progress: {e}")
    
    def flash_message(self, message, duration=3000, color="#f39c12"):
        """Flash a temporary message"""
        try:
            original_message = self.status_elements['message'].cget('text')
            original_color = self.status_elements['message'].cget('fg')
            
            def show_flash():
                self.status_elements['message'].config(