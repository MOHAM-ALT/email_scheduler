tk.Label(limits_grid, text="Emails per Batch:", bg='white').grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.settings_vars['emails_per_batch'] = tk.IntVar()
        tk.Spinbox(limits_grid, from_=1, to=50, textvariable=self.settings_vars['emails_per_batch'], width=10).grid(row=0, column=3, padx=5, pady=5)
        
        # Timing settings
        timing_frame = GuiUtils.create_label_frame(tab, "Timing Settings")
        timing_frame.pack(fill='x', padx=20, pady=10)
        
        timing_grid = tk.Frame(timing_frame, bg='white')
        timing_grid.pack(padx=20, pady=15)
        
        tk.Label(timing_grid, text="Start Time:", bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.settings_vars['start_time'] = tk.StringVar()
        tk.Entry(timing_grid, textvariable=self.settings_vars['start_time'], width=10).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(timing_grid, text="Batch Interval (min):", bg='white').grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.settings_vars['batch_interval'] = tk.IntVar()
        tk.Spinbox(timing_grid, from_=1, to=60, textvariable=self.settings_vars['batch_interval'], width=10).grid(row=0, column=3, padx=5, pady=5)
        
        # Schedule options
        options_frame = GuiUtils.create_label_frame(tab, "Schedule Options")
        options_frame.pack(fill='x', padx=20, pady=10)
        
        options_grid = tk.Frame(options_frame, bg='white')
        options_grid.pack(padx=20, pady=15)
        
        self.settings_vars['working_days_only'] = tk.BooleanVar()
        tk.Checkbutton(options_grid, text="Working days only", variable=self.settings_vars['working_days_only'], bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        self.settings_vars['retry_failed'] = tk.BooleanVar()
        tk.Checkbutton(options_grid, text="Retry failed emails", variable=self.settings_vars['retry_failed'], bg='white').grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        tk.Label(options_grid, text="Max Retry Attempts:", bg='white').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.settings_vars['max_retries'] = tk.IntVar()
        tk.Spinbox(options_grid, from_=1, to=10, textvariable=self.settings_vars['max_retries'], width=10).grid(row=1, column=1, padx=5, pady=5)
    
    def _create_outlook_settings_tab(self, notebook):
        """Create Outlook settings tab"""
        tab = tk.Frame(notebook, bg='white')
        notebook.add(tab, text="Outlook Settings")
        
        # Connection settings
        connection_frame = GuiUtils.create_label_frame(tab, "Connection Settings")
        connection_frame.pack(fill='x', padx=20, pady=10)
        
        conn_grid = tk.Frame(connection_frame, bg='white')
        conn_grid.pack(padx=20, pady=15)
        
        tk.Label(conn_grid, text="Connection Timeout (sec):", bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.settings_vars['connection_timeout'] = tk.IntVar()
        tk.Spinbox(conn_grid, from_=10, to=120, textvariable=self.settings_vars['connection_timeout'], width=10).grid(row=0, column=1, padx=5, pady=5)
        
        # Outlook options
        options_frame = GuiUtils.create_label_frame(tab, "Outlook Options")
        options_frame.pack(fill='x', padx=20, pady=10)
        
        options_grid = tk.Frame(options_frame, bg='white')
        options_grid.pack(padx=20, pady=15)
        
        self.settings_vars['auto_reconnect'] = tk.BooleanVar()
        tk.Checkbutton(options_grid, text="Auto-reconnect on disconnect", variable=self.settings_vars['auto_reconnect'], bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        self.settings_vars['use_bcc'] = tk.BooleanVar()
        tk.Checkbutton(options_grid, text="Use BCC for bulk emails", variable=self.settings_vars['use_bcc'], bg='white').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        
        self.settings_vars['backup_drafts'] = tk.BooleanVar()
        tk.Checkbutton(options_grid, text="Backup drafts before sending", variable=self.settings_vars['backup_drafts'], bg='white').grid(row=2, column=0, sticky='w', padx=5, pady=5)
    
    def _create_validation_settings_tab(self, notebook):
        """Create validation settings tab"""
        tab = tk.Frame(notebook, bg='white')
        notebook.add(tab, text="Validation Settings")
        
        # Validation options
        validation_frame = GuiUtils.create_label_frame(tab, "Email Validation")
        validation_frame.pack(fill='x', padx=20, pady=10)
        
        val_grid = tk.Frame(validation_frame, bg='white')
        val_grid.pack(padx=20, pady=15)
        
        self.settings_vars['strict_validation'] = tk.BooleanVar()
        tk.Checkbutton(val_grid, text="Strict validation mode", variable=self.settings_vars['strict_validation'], bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        self.settings_vars['check_mx_records'] = tk.BooleanVar()
        tk.Checkbutton(val_grid, text="Check MX records", variable=self.settings_vars['check_mx_records'], bg='white').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        
        self.settings_vars['allow_international'] = tk.BooleanVar()
        tk.Checkbutton(val_grid, text="Allow international domains", variable=self.settings_vars['allow_international'], bg='white').grid(row=2, column=0, sticky='w', padx=5, pady=5)
        
        # Filter settings
        filter_frame = GuiUtils.create_label_frame(tab, "Email Filters")
        filter_frame.pack(fill='x', padx=20, pady=10)
        
        filter_grid = tk.Frame(filter_frame, bg='white')
        filter_grid.pack(padx=20, pady=15)
        
        tk.Label(filter_grid, text="Max Email Length:", bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.settings_vars['max_email_length'] = tk.IntVar()
        tk.Spinbox(filter_grid, from_=50, to=500, textvariable=self.settings_vars['max_email_length'], width=10).grid(row=0, column=1, padx=5, pady=5)
        
        # Blacklist domains
        tk.Label(filter_grid, text="Blacklisted Domains:", bg='white').grid(row=1, column=0, sticky='nw', padx=5, pady=5)
        self.settings_vars['blacklist_domains'] = tk.Text(filter_grid, height=4, width=40)
        self.settings_vars['blacklist_domains'].grid(row=1, column=1, padx=5, pady=5)
    
    def _create_security_settings_tab(self, notebook):
        """Create security settings tab"""
        tab = tk.Frame(notebook, bg='white')
        notebook.add(tab, text="Security Settings")
        
        # Data protection
        data_frame = GuiUtils.create_label_frame(tab, "Data Protection")
        data_frame.pack(fill='x', padx=20, pady=10)
        
        data_grid = tk.Frame(data_frame, bg='white')
        data_grid.pack(padx=20, pady=15)
        
        self.settings_vars['encrypt_sensitive'] = tk.BooleanVar()
        tk.Checkbutton(data_grid, text="Encrypt sensitive data", variable=self.settings_vars['encrypt_sensitive'], bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        self.settings_vars['log_emails'] = tk.BooleanVar()
        tk.Checkbutton(data_grid, text="Log email addresses", variable=self.settings_vars['log_emails'], bg='white').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        
        self.settings_vars['auto_cleanup'] = tk.BooleanVar()
        tk.Checkbutton(data_grid, text="Auto-cleanup old logs", variable=self.settings_vars['auto_cleanup'], bg='white').grid(row=2, column=0, sticky='w', padx=5, pady=5)
        
        # Retention settings
        retention_frame = GuiUtils.create_label_frame(tab, "Data Retention")
        retention_frame.pack(fill='x', padx=20, pady=10)
        
        ret_grid = tk.Frame(retention_frame, bg='white')
        ret_grid.pack(padx=20, pady=15)
        
        tk.Label(ret_grid, text="Log Retention (days):", bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.settings_vars['log_retention'] = tk.IntVar()
        tk.Spinbox(ret_grid, from_=1, to=365, textvariable=self.settings_vars['log_retention'], width=10).grid(row=0, column=1, padx=5, pady=5)
        
        self.settings_vars['backup_schedules'] = tk.BooleanVar()
        tk.Checkbutton(ret_grid, text="Backup schedules automatically", variable=self.settings_vars['backup_schedules'], bg='white').grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=5)
    
    def _create_performance_settings_tab(self, notebook):
        """Create performance settings tab"""
        tab = tk.Frame(notebook, bg='white')
        notebook.add(tab, text="Performance Settings")
        
        # Resource management
        resource_frame = GuiUtils.create_label_frame(tab, "Resource Management")
        resource_frame.pack(fill='x', padx=20, pady=10)
        
        res_grid = tk.Frame(resource_frame, bg='white')
        res_grid.pack(padx=20, pady=15)
        
        tk.Label(res_grid, text="Max Concurrent Operations:", bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.settings_vars['max_concurrent'] = tk.IntVar()
        tk.Spinbox(res_grid, from_=1, to=20, textvariable=self.settings_vars['max_concurrent'], width=10).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(res_grid, text="Cache Size (MB):", bg='white').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.settings_vars['cache_size'] = tk.IntVar()
        tk.Spinbox(res_grid, from_=10, to=1000, textvariable=self.settings_vars['cache_size'], width=10).grid(row=1, column=1, padx=5, pady=5)
        
        # Optimization settings
        opt_frame = GuiUtils.create_label_frame(tab, "Optimization")
        opt_frame.pack(fill='x', padx=20, pady=10)
        
        opt_grid = tk.Frame(opt_frame, bg='white')
        opt_grid.pack(padx=20, pady=15)
        
        self.settings_vars['memory_optimization'] = tk.BooleanVar()
        tk.Checkbutton(opt_grid, text="Enable memory optimization", variable=self.settings_vars['memory_optimization'], bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        self.settings_vars['auto_cleanup_cache'] = tk.BooleanVar()
        tk.Checkbutton(opt_grid, text="Auto-cleanup cache", variable=self.settings_vars['auto_cleanup_cache'], bg='white').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        
        tk.Label(opt_grid, text="Progress Update Interval (sec):", bg='white').grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.settings_vars['progress_interval'] = tk.IntVar()
        tk.Spinbox(opt_grid, from_=1, to=60, textvariable=self.settings_vars['progress_interval'], width=10).grid(row=2, column=1, padx=5, pady=5)
    
    def _create_action_buttons(self):
        """Create action buttons"""
        button_frame = tk.Frame(self.frame, bg='#f5f6fa')
        button_frame.pack(fill='x', padx=20, pady=20)
        
        # Left side buttons
        left_buttons = tk.Frame(button_frame, bg='#f5f6fa')
        left_buttons.pack(side='left')
        
        GuiUtils.create_styled_button(
            left_buttons,
            "📂 Load Profile",
            command=self._load_profile,
            style="secondary"
        ).pack(side='left', padx=5)
        
        GuiUtils.create_styled_button(
            left_buttons,
            "💾 Save Profile",
            command=self._save_profile,
            style="secondary"
        ).pack(side='left', padx=5)
        
        GuiUtils.create_styled_button(
            left_buttons,
            "🔄 Reset to Defaults",
            command=self._reset_defaults,
            style="warning"
        ).pack(side='left', padx=5)
        
        # Right side buttons
        right_buttons = tk.Frame(button_frame, bg='#f5f6fa')
        right_buttons.pack(side='right')
        
        GuiUtils.create_styled_button(
            right_buttons,
            "❌ Cancel",
            command=self._cancel_changes,
            style="secondary"
        ).pack(side='right', padx=5)
        
        GuiUtils.create_styled_button(
            right_buttons,
            "✅ Apply",
            command=self._apply_settings,
            style="success"
        ).pack(side='right', padx=5)
    
    def _load_settings(self):
        """Load current settings from configuration"""
        try:
            if not self.config_manager:
                return
            
            # Email settings
            email_settings = self.config_manager.get_email_settings()
            self.settings_vars['default_subject'].set(email_settings.default_subject)
            self.settings_vars['default_body'].delete('1.0', tk.END)
            self.settings_vars['default_body'].insert('1.0', email_settings.default_body)
            self.settings_vars['max_attachments'].set(email_settings.max_attachments)
            self.settings_vars['max_attachment_size'].set(email_settings.max_attachment_size_mb)
            
            # Schedule settings
            schedule_settings = self.config_manager.get_schedule_settings()
            self.settings_vars['emails_per_day'].set(schedule_settings.emails_per_day)
            self.settings_vars['emails_per_batch'].set(schedule_settings.emails_per_batch)
            self.settings_vars['start_time'].set(schedule_settings.start_time)
            self.settings_vars['working_days_only'].set(schedule_settings.working_days_only)
            self.settings_vars['retry_failed'].set(schedule_settings.retry_failed_emails)
            self.settings_vars['max_retries'].set(schedule_settings.retry_attempts)
            self.settings_vars['batch_interval'].set(schedule_settings.retry_delay_minutes)
            
            # Outlook settings
            outlook_settings = self.config_manager.get_outlook_settings()
            self.settings_vars['connection_timeout'].set(outlook_settings.connection_timeout)
            self.settings_vars['auto_reconnect'].set(outlook_settings.auto_reconnect)
            self.settings_vars['use_bcc'].set(outlook_settings.use_bcc)
            self.settings_vars['backup_drafts'].set(outlook_settings.backup_drafts)
            
            # Validation settings
            validation_settings = self.config_manager.get_validation_settings()
            self.settings_vars['strict_validation'].set(validation_settings.strict_validation)
            self.settings_vars['check_mx_records'].set(validation_settings.check_mx_records)
            self.settings_vars['allow_international'].set(validation_settings.allow_international_domains)
            self.settings_vars['max_email_length'].set(validation_settings.max_email_length)
            
            # Blacklist domains
            if validation_settings.blacklist_domains:
                blacklist_text = '\n'.join(validation_settings.blacklist_domains)
                self.settings_vars['blacklist_domains'].delete('1.0', tk.END)
                self.settings_vars['blacklist_domains'].insert('1.0', blacklist_text)
            
            # Security settings
            security_settings = self.config_manager.get_security_settings()
            self.settings_vars['encrypt_sensitive'].set(security_settings.encrypt_sensitive_data)
            self.settings_vars['log_emails'].set(security_settings.log_email_addresses)
            self.settings_vars['auto_cleanup'].set(security_settings.auto_cleanup_logs)
            self.settings_vars['log_retention'].set(security_settings.log_retention_days)
            self.settings_vars['backup_schedules'].set(security_settings.backup_schedules)
            
            # Performance settings
            performance_settings = self.config_manager.get_performance_settings()
            self.settings_vars['max_concurrent'].set(performance_settings.max_concurrent_operations)
            self.settings_vars['cache_size'].set(performance_settings.cache_size_mb)
            self.settings_vars['memory_optimization'].set(performance_settings.memory_optimization)
            self.settings_vars['auto_cleanup_cache'].set(performance_settings.auto_cleanup_cache)
            self.settings_vars['progress_interval'].set(performance_settings.progress_update_interval)
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def _apply_settings(self):
        """Apply current settings"""
        try:
            if not self.config_manager:
                messagebox.showerror("Error", "Configuration manager not available")
                return
            
            # Validate settings before applying
            if not self._validate_settings():
                return
            
            # Update configuration objects
            self._update_config_objects()
            
            # Save configuration
            success = self.config_manager.save_config()
            
            if success:# gui/components/settings_frame.py
"""
Settings Frame - Application Configuration
Comprehensive settings management interface
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from ..utils.gui_utils import GuiUtils

logger = logging.getLogger(__name__)

class SettingsFrame:
    """Application settings and configuration component"""
    
    def __init__(self, parent, app_manager, config_manager):
        self.parent = parent
        self.app_manager = app_manager
        self.config_manager = config_manager
        
        # Create main frame
        self.frame = tk.Frame(parent, bg='#f5f6fa')
        
        # Settings variables
        self.settings_vars = {}
        
        # Create settings interface
        self._create_interface()
        
        # Load current settings
        self._load_settings()
    
    def _create_interface(self):
        """Create settings interface"""
        try:
            # Create notebook for different setting categories
            notebook = ttk.Notebook(self.frame)
            notebook.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Email Settings tab
            self._create_email_settings_tab(notebook)
            
            # Schedule Settings tab
            self._create_schedule_settings_tab(notebook)
            
            # Outlook Settings tab
            self._create_outlook_settings_tab(notebook)
            
            # Validation Settings tab
            self._create_validation_settings_tab(notebook)
            
            # Security Settings tab
            self._create_security_settings_tab(notebook)
            
            # Performance Settings tab
            self._create_performance_settings_tab(notebook)
            
            # Action buttons
            self._create_action_buttons()
            
        except Exception as e:
            logger.error(f"Error creating settings interface: {e}")
    
    def _create_email_settings_tab(self, notebook):
        """Create email settings tab"""
        tab = tk.Frame(notebook, bg='white')
        notebook.add(tab, text="Email Settings")
        
        # Default subject
        subject_frame = GuiUtils.create_label_frame(tab, "Default Email Content")
        subject_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(subject_frame, text="Default Subject:", bg='white', font=('Segoe UI', 10)).pack(anchor='w', padx=20, pady=5)
        
        self.settings_vars['default_subject'] = tk.StringVar()
        subject_entry = tk.Entry(subject_frame, textvariable=self.settings_vars['default_subject'], width=80)
        subject_entry.pack(fill='x', padx=20, pady=5)
        
        # Default body
        tk.Label(subject_frame, text="Default Message Body:", bg='white', font=('Segoe UI', 10)).pack(anchor='w', padx=20, pady=(15, 5))
        
        self.settings_vars['default_body'] = tk.Text(subject_frame, height=8, wrap='word')
        self.settings_vars['default_body'].pack(fill='x', padx=20, pady=5)
        
        # Attachment settings
        attachment_frame = GuiUtils.create_label_frame(tab, "Attachment Settings")
        attachment_frame.pack(fill='x', padx=20, pady=10)
        
        att_grid = tk.Frame(attachment_frame, bg='white')
        att_grid.pack(padx=20, pady=15)
        
        tk.Label(att_grid, text="Max Attachments:", bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.settings_vars['max_attachments'] = tk.IntVar()
        tk.Spinbox(att_grid, from_=0, to=10, textvariable=self.settings_vars['max_attachments'], width=10).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(att_grid, text="Max Size (MB):", bg='white').grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.settings_vars['max_attachment_size'] = tk.IntVar()
        tk.Spinbox(att_grid, from_=1, to=100, textvariable=self.settings_vars['max_attachment_size'], width=10).grid(row=0, column=3, padx=5, pady=5)
    
    def _create_schedule_settings_tab(self, notebook):
        """Create schedule settings tab"""
        tab = tk.Frame(notebook, bg='white')
        notebook.add(tab, text="Schedule Settings")
        
        # Daily limits
        limits_frame = GuiUtils.create_label_frame(tab, "Daily Sending Limits")
        limits_frame.pack(fill='x', padx=20, pady=10)
        
        limits_grid = tk.Frame(limits_frame, bg='white')
        limits_grid.pack(padx=20, pady=15)
        
        tk.Label(limits_grid, text="Emails per Day:", bg='white').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.settings_vars['emails_per_day'] = tk.IntVar()
        tk.Spinbox(limits_grid, from_=1, to=1000, textvariable=self.settings_vars['emails_per_day'], width=10).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(limits_grid, text="Emails per Batch:", bg='white').grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.