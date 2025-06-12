# gui/components/dashboard_frame.py
"""
Dashboard Frame - Main Dashboard Component
Overview and quick access to system functionality
"""

import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime
from ..utils.gui_utils import GuiUtils

logger = logging.getLogger(__name__)

class DashboardFrame:
    """Main dashboard component with system overview"""
    
    def __init__(self, parent, app_manager, config_manager):
        self.parent = parent
        self.app_manager = app_manager
        self.config_manager = config_manager
        
        # Create main frame
        self.frame = tk.Frame(parent, bg='#f5f6fa')
        
        # Dashboard elements
        self.status_indicators = {}
        self.metric_displays = {}
        
        # Create dashboard content
        self._create_dashboard()
        
    def _create_dashboard(self):
        """Create dashboard content"""
        try:
            # Welcome section
            welcome_frame = GuiUtils.create_label_frame(self.frame, "Welcome to Professional Email Scheduler")
            welcome_frame.pack(fill='x', padx=20, pady=10)
            
            welcome_text = tk.Label(
                welcome_frame,
                text="Professional Email Scheduler v4.0 - Advanced Email Management System",
                font=('Segoe UI', 12, 'bold'),
                bg='white',
                fg='#2c3e50'
            )
            welcome_text.pack(pady=20)
            
            # System Status section
            status_frame = GuiUtils.create_label_frame(self.frame, "System Status")
            status_frame.pack(fill='x', padx=20, pady=10)
            
            status_grid = tk.Frame(status_frame, bg='white')
            status_grid.pack(fill='x', padx=20, pady=15)
            
            # Status indicators
            self.status_indicators['outlook'] = GuiUtils.create_status_indicator(status_grid, "checking")
            self.status_indicators['outlook'].pack(side='left', padx=20)
            
            tk.Label(status_grid, text="Outlook Connection", bg='white', font=('Segoe UI', 10)).pack(side='left')
            
            # Quick metrics
            metrics_frame = GuiUtils.create_label_frame(self.frame, "Quick Metrics")
            metrics_frame.pack(fill='both', expand=True, padx=20, pady=10)
            
            metrics_grid = tk.Frame(metrics_frame, bg='white')
            metrics_grid.pack(fill='both', expand=True, padx=20, pady=15)
            
            # Create metric displays
            self.metric_displays['emails'] = GuiUtils.create_metric_display(
                metrics_grid, "Total Emails", 0
            )
            self.metric_displays['emails'].pack(side='left', fill='both', expand=True, padx=10)
            
            self.metric_displays['sent'] = GuiUtils.create_metric_display(
                metrics_grid, "Emails Sent", 0
            )
            self.metric_displays['sent'].pack(side='left', fill='both', expand=True, padx=10)
            
            self.metric_displays['pending'] = GuiUtils.create_metric_display(
                metrics_grid, "Pending", 0
            )
            self.metric_displays['pending'].pack(side='left', fill='both', expand=True, padx=10)
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
    
    def update_display(self):
        """Update dashboard display"""
        try:
            # Update system status
            if self.app_manager:
                outlook_manager = self.app_manager.get_outlook_manager()
                if outlook_manager and outlook_manager.is_connected():
                    self.status_indicators['outlook'].update_status("healthy", "Outlook Connected")
                else:
                    self.status_indicators['outlook'].update_status("error", "Outlook Disconnected")
                
                # Update metrics
                email_processor = self.app_manager.get_email_processor()
                if email_processor:
                    stats = email_processor.get_statistics()
                    self.metric_displays['emails'].update_value(stats.get('total_emails', 0))
                    self.metric_displays['sent'].update_value(stats.get('processing_stats', {}).get('sent_emails', 0))
                    self.metric_displays['pending'].update_value(stats.get('total_emails', 0) - stats.get('processing_stats', {}).get('sent_emails', 0))
                    
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def refresh(self):
        """Refresh dashboard data"""
        self.update_display()
    
    def cleanup(self):
        """Cleanup dashboard resources"""
        pass