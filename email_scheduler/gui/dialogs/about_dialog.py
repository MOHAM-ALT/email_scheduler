# gui/dialogs/about_dialog.py
"""
About Dialog - Application Information
Professional about dialog with application details and system information
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
import logging
from datetime import datetime
import sys
import platform

logger = logging.getLogger(__name__)

class AboutDialog:
    """Professional about dialog with comprehensive application information"""
    
    def __init__(self, parent, app_manager=None):
        self.parent = parent
        self.app_manager = app_manager
        self.dialog = None
        
    def show(self):
        """Show the about dialog"""
        try:
            # Create dialog window
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("About Professional Email Scheduler")
            self.dialog.geometry("600x500")
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
            self.dialog.resizable(False, False)
            
            # Center the dialog
            self._center_dialog()
            
            # Create dialog content
            self._create_content()
            
        except Exception as e:
            logger.error(f"Error showing about dialog: {e}")
    
    def _center_dialog(self):
        """Center the dialog on parent window"""
        try:
            self.dialog.update_idletasks()
            x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
            self.dialog.geometry(f"+{x}+{y}")
        except Exception as e:
            logger.error(f"Error centering dialog: {e}")
    
    def _create_content(self):
        """Create the dialog content"""
        try:
            # Main container
            main_frame = tk.Frame(self.dialog, bg='white')
            main_frame.pack(fill='both', expand=True)
            
            # Header section
            self._create_header(main_frame)
            
            # Create notebook for tabbed content
            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill='both', expand=True, padx=20, pady=10)
            
            # About tab
            about_tab = tk.Frame(notebook, bg='white')
            notebook.add(about_tab, text="About")
            self._create_about_tab(about_tab)
            
            # System Info tab
            system_tab = tk.Frame(notebook, bg='white')
            notebook.add(system_tab, text="System Info")
            self._create_system_tab(system_tab)
            
            # Credits tab
            credits_tab = tk.Frame(notebook, bg='white')
            notebook.add(credits_tab, text="Credits")
            self._create_credits_tab(credits_tab)
            
            # License tab
            license_tab = tk.Frame(notebook, bg='white')
            notebook.add(license_tab, text="License")
            self._create_license_tab(license_tab)
            
            # Footer with buttons
            self._create_footer(main_frame)
            
        except Exception as e:
            logger.error(f"Error creating dialog content: {e}")
    
    def _create_header(self, parent):
        """Create the header section"""
        try:
            header_frame = tk.Frame(parent, bg='#2c3e50', height=100)
            header_frame.pack(fill='x')
            header_frame.pack_propagate(False)
            
            # Application icon/logo (placeholder)
            logo_frame = tk.Frame(header_frame, bg='#2c3e50')
            logo_frame.pack(side='left', padx=20, pady=20)
            
            # Create a simple logo using text
            logo_label = tk.Label(
                logo_frame,
                text="📧",
                font=('Segoe UI', 36),
                bg='#2c3e50',
                fg='white'
            )
            logo_label.pack()
            
            # Application title and version
            title_frame = tk.Frame(header_frame, bg='#2c3e50')
            title_frame.pack(side='left', fill='both', expand=True, pady=20)
            
            title_label = tk.Label(
                title_frame,
                text="Professional Email Scheduler",
                font=('Segoe UI', 18, 'bold'),
                bg='#2c3e50',
                fg='white'
            )
            title_label.pack(anchor='w')
            
            version_label = tk.Label(
                title_frame,
                text="Version 4.0.0 Professional Edition",
                font=('Segoe UI', 12),
                bg='#2c3e50',
                fg='#bdc3c7'
            )
            version_label.pack(anchor='w')
            
            tagline_label = tk.Label(
                title_frame,
                text="Advanced Email Management & Scheduling System",
                font=('Segoe UI', 10),
                bg='#2c3e50',
                fg='#95a5a6'
            )
            tagline_label.pack(anchor='w', pady=(5, 0))
            
        except Exception as e:
            logger.error(f"Error creating header: {e}")
    
    def _create_about_tab(self, parent):
        """Create the about tab content"""
        try:
            # Scrollable frame
            canvas = tk.Canvas(parent, bg='white')
            scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='white')
            
            scrollable_frame.bind(
                '<Configure>',
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Content
            content_text = """
Professional Email Scheduler v4.0

A comprehensive email management and scheduling solution designed for professionals 
who need to send bulk emails efficiently and reliably.

Key Features:
• Advanced email validation and processing
• Intelligent scheduling with Outlook integration
• Batch processing with configurable limits
• Real-time monitoring and statistics
• Comprehensive error handling and recovery
• Professional user interface with modern design
• Extensive configuration and customization options

This application provides enterprise-grade email management capabilities with 
a focus on reliability, performance, and ease of use.

Built with Python and modern GUI frameworks, this tool represents the latest 
in email automation technology.

Copyright © 2024 Professional Email Scheduler Team
All rights reserved.
            """
            
            text_widget = tk.Text(
                scrollable_frame,
                font=('Segoe UI', 10),
                bg='white',
                wrap='word',
                relief='flat',
                padx=20,
                pady=20,
                height=15
            )
            text_widget.pack(fill='both', expand=True)
            text_widget.insert('1.0', content_text.strip())
            text_widget.config(state='disabled')
            
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
        except Exception as e:
            logger.error(f"Error creating about tab: {e}")
    
    def _create_system_tab(self, parent):
        """Create the system information tab"""
        try:
            # Create text widget with scrollbar
            text_frame = tk.Frame(parent, bg='white')
            text_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(
                text_frame,
                font=('Consolas', 9),
                bg='#f8f9fa',
                wrap='word'
            )
            scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            # Generate system information
            system_info = self._generate_system_info()
            text_widget.insert('1.0', system_info)
            text_widget.config(state='disabled')
            
        except Exception as e:
            logger.error(f"Error creating system tab: {e}")
    
    def _create_credits_tab(self, parent):
        """Create the credits tab"""
        try:
            canvas = tk.Canvas(parent, bg='white')
            scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='white')
            
            scrollable_frame.bind(
                '<Configure>',
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)
            
            credits_content = """
Professional Email Scheduler v4.0
Development Team & Acknowledgments

Core Development:
• Application Architecture & Design
• Email Processing Engine
• Outlook Integration System
• User Interface Design
• Quality Assurance & Testing

Third-Party Libraries:
• Python 3.8+ - Core programming language
• tkinter - GUI framework
• pandas - Data processing and analysis
• openpyxl - Excel file handling
• schedule - Task scheduling
• email-validator - Email validation
• pywin32 - Windows COM integration
• dnspython - DNS resolution
• cryptography - Security and encryption

Special Thanks:
• Microsoft Outlook team for COM automation support
• Python community for excellent libraries
• Open source contributors worldwide
• Beta testers and early adopters

Testing & Quality Assurance:
• Comprehensive unit testing
• Integration testing with Outlook
• Performance optimization
• Security validation
• Cross-platform compatibility testing

Documentation & Support:
• User manual and guides
• API documentation
• Video tutorials
• Community support forums

This project builds upon the excellent work of the Python community 
and various open-source projects. We extend our gratitude to all 
contributors who make tools like this possible.
            """
            
            text_widget = tk.Text(
                scrollable_frame,
                font=('Segoe UI', 10),
                bg='white',
                wrap='word',
                relief='flat',
                padx=20,
                pady=20
            )
            text_widget.pack(fill='both', expand=True)
            text_widget.insert('1.0', credits_content.strip())
            text_widget.config(state='disabled')
            
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
        except Exception as e:
            logger.error(f"Error creating credits tab: {e}")
    
    def _create_license_tab(self, parent):
        """Create the license tab"""
        try:
            text_frame = tk.Frame(parent, bg='white')
            text_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(
                text_frame,
                font=('Consolas', 9),
                bg='#f8f9fa',
                wrap='word'
            )
            scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            license_text = """
Professional Email Scheduler v4.0
SOFTWARE LICENSE AGREEMENT

This software is provided for educational and professional use.

TERMS AND CONDITIONS:

1. GRANT OF LICENSE
This software is licensed, not sold. Subject to the terms of this Agreement, 
the author grants you a limited, non-exclusive, non-transferable license to 
use this software.

2. PERMITTED USES
You may:
- Use the software for personal and professional email management
- Install the software on multiple computers for your use
- Create backups of the software for archival purposes

3. RESTRICTIONS
You may not:
- Distribute, sell, or sublicense the software
- Reverse engineer, decompile, or disassemble the software
- Remove or modify copyright notices
- Use the software for illegal or unauthorized purposes

4. DISCLAIMER OF WARRANTIES
This software is provided "AS IS" without warranty of any kind, either 
expressed or implied, including but not limited to the implied warranties 
of merchantability and fitness for a particular purpose.

5. LIMITATION OF LIABILITY
In no event shall the author be liable for any damages whatsoever arising 
out of the use of or inability to use this software.

6. THIRD-PARTY COMPONENTS
This software includes third-party components that are subject to their 
own license terms. Please refer to the Credits section for more information.

7. TERMINATION
This license is effective until terminated. It will terminate automatically 
if you fail to comply with any term or condition of this Agreement.

By using this software, you acknowledge that you have read this Agreement, 
understand it, and agree to be bound by its terms and conditions.

Copyright © 2024 Professional Email Scheduler Team
All rights reserved.
            """
            
            text_widget.insert('1.0', license_text.strip())
            text_widget.config(state='disabled')
            
        except Exception as e:
            logger.error(f"Error creating license tab: {e}")
    
    def _create_footer(self, parent):
        """Create the footer with buttons"""
        try:
            footer_frame = tk.Frame(parent, bg='white')
            footer_frame.pack(fill='x', padx=20, pady=15)
            
            # Links frame
            links_frame = tk.Frame(footer_frame, bg='white')
            links_frame.pack(side='left')
            
            # Website link
            website_btn = tk.Button(
                links_frame,
                text="🌐 Website",
                command=lambda: webbrowser.open("https://github.com"),
                font=('Segoe UI', 9),
                bg='#3498db',
                fg='white',
                relief='flat',
                padx=15,
                pady=5,
                cursor='hand2'
            )
            website_btn.pack(side='left', padx=5)
            
            # Documentation link
            docs_btn = tk.Button(
                links_frame,
                text="📖 Documentation",
                command=lambda: webbrowser.open("https://github.com"),
                font=('Segoe UI', 9),
                bg='#2ecc71',
                fg='white',
                relief='flat',
                padx=15,
                pady=5,
                cursor='hand2'
            )
            docs_btn.pack(side='left', padx=5)
            
            # Support link
            support_btn = tk.Button(
                links_frame,
                text="🆘 Support",
                command=lambda: webbrowser.open("mailto:support@emailscheduler.com"),
                font=('Segoe UI', 9),
                bg='#e74c3c',
                fg='white',
                relief='flat',
                padx=15,
                pady=5,
                cursor='hand2'
            )
            support_btn.pack(side='left', padx=5)
            
            # Close button
            close_btn = tk.Button(
                footer_frame,
                text="Close",
                command=self.dialog.destroy,
                font=('Segoe UI', 10),
                bg='#95a5a6',
                fg='white',
                relief='flat',
                padx=30,
                pady=8,
                cursor='hand2'
            )
            close_btn.pack(side='right')
            
        except Exception as e:
            logger.error(f"Error creating footer: {e}")
    
    def _generate_system_info(self):
        """Generate detailed system information"""
        try:
            info_lines = [
                "Professional Email Scheduler v4.0 - System Information",
                "=" * 60,
                "",
                f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ""
            ]
            
            # Python information
            info_lines.extend([
                "Python Environment:",
                "-" * 30,
                f"Python Version: {sys.version}",
                f"Python Executable: {sys.executable}",
                f"Platform: {platform.platform()}",
                f"Architecture: {platform.architecture()[0]}",
                f"Machine: {platform.machine()}",
                f"Processor: {platform.processor()}",
                ""
            ])
            
            # Application information
            if self.app_manager:
                app_status = self.app_manager.get_system_status()
                info_lines.extend([
                    "Application Status:",
                    "-" * 30,
                    f"Initialized: {app_status.get('initialized', 'Unknown')}",
                    f"Running: {app_status.get('running', 'Unknown')}",
                    f"Components: {len(app_status.get('components', []))}",
                    f"Outlook Connected: {app_status.get('outlook_connected', 'Unknown')}",
                    f"Active Schedules: {app_status.get('active_schedules', 0)}",
                    ""
                ])
                
                # Component health
                health_status = app_status.get('health_status', {})
                if health_status:
                    info_lines.extend([
                        "Component Health:",
                        "-" * 30
                    ])
                    for component, health in health_status.items():
                        status = health.get('status', 'unknown')
                        info_lines.append(f"{component}: {status}")
                    info_lines.append("")
            
            # Installed packages
            try:
                import pkg_resources
                installed_packages = [d for d in pkg_resources.working_set]
                
                info_lines.extend([
                    "Key Installed Packages:",
                    "-" * 30
                ])
                
                key_packages = ['pandas', 'openpyxl', 'schedule', 'email-validator', 'pywin32']
                for pkg in installed_packages:
                    if pkg.project_name.lower() in key_packages:
                        info_lines.append(f"{pkg.project_name}: {pkg.version}")
                
                info_lines.append("")
                
            except Exception:
                info_lines.extend([
                    "Package Information: Not available",
                    ""
                ])
            
            # System resources
            try:
                import psutil
                
                # Memory info
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                info_lines.extend([
                    "System Resources:",
                    "-" * 30,
                    f"CPU Cores: {psutil.cpu_count()}",
                    f"CPU Usage: {psutil.cpu_percent()}%",
                    f"Total Memory: {memory.total / (1024**3):.2f} GB",
                    f"Available Memory: {memory.available / (1024**3):.2f} GB",
                    f"Memory Usage: {memory.percent}%",
                    f"Total Disk: {disk.total / (1024**3):.2f} GB",
                    f"Free Disk: {disk.free / (1024**3):.2f} GB",
                    f"Disk Usage: {(disk.used / disk.total) * 100:.1f}%",
                    ""
                ])
                
            except ImportError:
                info_lines.extend([
                    "System Resources: Information not available (psutil not installed)",
                    ""
                ])
            except Exception as e:
                info_lines.extend([
                    f"System Resources: Error retrieving information - {e}",
                    ""
                ])
            
            # Network information
            try:
                import socket
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                
                info_lines.extend([
                    "Network Information:",
                    "-" * 30,
                    f"Hostname: {hostname}",
                    f"Local IP: {local_ip}",
                    ""
                ])
                
            except Exception:
                info_lines.extend([
                    "Network Information: Not available",
                    ""
                ])
            
            # Environment variables (selected)
            important_env_vars = ['PATH', 'PYTHONPATH', 'HOME', 'USER', 'USERNAME']
            env_info = []
            
            for var in important_env_vars:
                value = sys.platform == 'win32' and var == 'USER' and 'USERNAME' or var
                if value in ['USER', 'USERNAME']:
                    value = 'USERNAME' if sys.platform == 'win32' else 'USER'
                
                import os
                env_value = os.environ.get(value, 'Not set')
                if var == 'PATH':
                    env_value = f"{len(env_value.split(os.pathsep))} entries"
                elif len(env_value) > 50:
                    env_value = env_value[:47] + "..."
                
                env_info.append(f"{var}: {env_value}")
            
            if env_info:
                info_lines.extend([
                    "Environment (selected):",
                    "-" * 30
                ])
                info_lines.extend(env_info)
                info_lines.append("")
            
            # Application directories
            import os
            app_dirs = {
                'Current Directory': os.getcwd(),
                'User Home': os.path.expanduser('~'),
                'Temp Directory': os.environ.get('TEMP', os.environ.get('TMP', '/tmp'))
            }
            
            info_lines.extend([
                "Application Directories:",
                "-" * 30
            ])
            
            for name, path in app_dirs.items():
                info_lines.append(f"{name}: {path}")
            
            info_lines.append("")
            
            # Build information
            info_lines.extend([
                "Build Information:",
                "-" * 30,
                "Application: Professional Email Scheduler",
                "Version: 4.0.0",
                "Build Type: Professional Edition",
                "Architecture: Cross-platform",
                "GUI Framework: tkinter",
                "Email Engine: Custom with Outlook integration",
                "Configuration: Production",
                ""
            ])
            
            # Footer
            info_lines.extend([
                "=" * 60,
                "End of System Information Report"
            ])
            
            return "\n".join(info_lines)
            
        except Exception as e:
            logger.error(f"Error generating system info: {e}")
            return f"Error generating system information: {e}"

class HelpDialog:
    """Help dialog with user documentation"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
    
    def show(self):
        """Show the help dialog"""
        try:
            # Create dialog window
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("Professional Email Scheduler - Help")
            self.dialog.geometry("700x600")
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
            
            # Center the dialog
            self._center_dialog()
            
            # Create content
            self._create_help_content()
            
        except Exception as e:
            logger.error(f"Error showing help dialog: {e}")
    
    def _center_dialog(self):
        """Center the dialog on parent window"""
        try:
            self.dialog.update_idletasks()
            x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
            self.dialog.geometry(f"+{x}+{y}")
        except Exception as e:
            logger.error(f"Error centering help dialog: {e}")
    
    def _create_help_content(self):
        """Create help content"""
        try:
            # Main frame
            main_frame = tk.Frame(self.dialog, bg='white')
            main_frame.pack(fill='both', expand=True)
            
            # Title
            title_label = tk.Label(
                main_frame,
                text="Professional Email Scheduler - User Guide",
                font=('Segoe UI', 16, 'bold'),
                bg='white',
                fg='#2c3e50'
            )
            title_label.pack(pady=20)
            
            # Create notebook for help topics
            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill='both', expand=True, padx=20, pady=10)
            
            # Getting Started tab
            getting_started_tab = tk.Frame(notebook, bg='white')
            notebook.add(getting_started_tab, text="Getting Started")
            self._create_getting_started_tab(getting_started_tab)
            
            # Email Setup tab
            email_setup_tab = tk.Frame(notebook, bg='white')
            notebook.add(email_setup_tab, text="Email Setup")
            self._create_email_setup_tab(email_setup_tab)
            
            # Scheduling tab
            scheduling_tab = tk.Frame(notebook, bg='white')
            notebook.add(scheduling_tab, text="Scheduling")
            self._create_scheduling_tab(scheduling_tab)
            
            # Troubleshooting tab
            troubleshooting_tab = tk.Frame(notebook, bg='white')
            notebook.add(troubleshooting_tab, text="Troubleshooting")
            self._create_troubleshooting_tab(troubleshooting_tab)
            
            # Close button
            close_btn = tk.Button(
                main_frame,
                text="Close",
                command=self.dialog.destroy,
                font=('Segoe UI', 10),
                bg='#95a5a6',
                fg='white',
                relief='flat',
                padx=30,
                pady=8
            )
            close_btn.pack(pady=20)
            
        except Exception as e:
            logger.error(f"Error creating help content: {e}")
    
    def _create_getting_started_tab(self, parent):
        """Create getting started help content"""
        content = """
Getting Started with Professional Email Scheduler

OVERVIEW:
Professional Email Scheduler is designed to help you send bulk emails efficiently 
and reliably using Microsoft Outlook integration.

BASIC WORKFLOW:
1. Prepare your email list in Excel format
2. Configure your email content and attachments
3. Set up scheduling parameters
4. Review and start the email campaign
5. Monitor progress and results

FIRST TIME SETUP:
1. Ensure Microsoft Outlook is installed and configured
2. Open Professional Email Scheduler
3. Check system status in the status bar
4. Verify Outlook connection (should show green indicator)
5. Navigate to the Email Setup tab to begin

EMAIL LIST PREPARATION:
• Create an Excel file (.xlsx or .xls)
• Put email addresses in the first column (Column A)
• One email address per row
• No headers required
• Save the file in an accessible location

QUICK START:
1. Click "Email Setup" tab
2. Click "Select Excel File" to load your email list
3. Enter your email subject and message
4. Add PDF attachments if needed (optional)
5. Go to "Schedule" tab
6. Click "Create Schedule" 
7. Review the schedule and click "Start Sending"

The application will automatically:
• Validate all email addresses
• Remove duplicates
• Create optimized batches
• Send emails according to schedule
• Provide real-time progress updates
        """
        
        self._create_help_text_widget(parent, content)
    
    def _create_email_setup_tab(self, parent):
        """Create email setup help content"""
        content = """
Email Setup and Configuration

EMAIL LIST REQUIREMENTS:
• Supported formats: Excel (.xlsx, .xls), CSV, text files
• Email addresses should be in the first column
• Maximum file size: 100MB
• Recommended: Keep lists under 50,000 emails for optimal performance

EMAIL VALIDATION:
The application automatically validates email addresses for:
• Proper format (user@domain.com)
• Domain structure
• Character validation
• Duplicate detection
• Role-based address detection (optional)

EMAIL CONTENT:
• Subject Line: Keep under 100 characters for best deliverability
• Message Body: Supports plain text formatting
• Variables: Use placeholders if needed
• Length: No strict limit, but shorter emails often perform better

ATTACHMENTS:
• Supported format: PDF files only
• Maximum: 2 attachments per email
• Size limit: 25MB per attachment
• Recommendations: Keep attachments small for better delivery

SENDING METHODS:
• BCC (Blind Carbon Copy): Default method - recipients don't see other addresses
• Batch Size: Default 10 emails per batch (configurable)
• Daily Limits: Default 499 emails per day (configurable)

OUTLOOK INTEGRATION:
• Requires Microsoft Outlook installed and configured
• Uses your default Outlook profile
• Emails appear in your Sent folder
• Respects Outlook security settings

BEST PRACTICES:
• Test with a small list first (5-10 emails)
• Use professional email addresses
• Include unsubscribe information
• Comply with email marketing regulations
• Monitor bounce rates and responses
        """
        
        self._create_help_text_widget(parent, content)
    
    def _create_scheduling_tab(self, parent):
        """Create scheduling help content"""
        content = """
Email Scheduling and Management

SCHEDULING OVERVIEW:
The scheduler automatically distributes your emails across multiple days and times 
to ensure optimal delivery and compliance with sending limits.

SCHEDULE SETTINGS:
• Emails per Day: Maximum emails to send daily (default: 499)
• Emails per Batch: Number of emails sent together (default: 10)
• Start Time: Daily start time for sending (default: 06:00)
• Working Days Only: Skip weekends (recommended)
• Batch Interval: Time between batches (default: 5 minutes)

SCHEDULE CREATION:
1. Load your email list in Email Setup tab
2. Configure email content and attachments
3. Go to Schedule tab
4. Adjust settings if needed
5. Click "Create Schedule"
6. Review the generated schedule
7. Click "Start Sending" to begin

SCHEDULE MANAGEMENT:
• Start/Stop: Control schedule execution
• Pause/Resume: Temporarily halt and continue
• Monitor Progress: Real-time status updates
• View Statistics: Detailed sending reports

AUTOMATIC FEATURES:
• Weekend Skipping: Automatically skips Saturday and Sunday
• Optimal Timing: Distributes emails throughout business hours
• Retry Logic: Automatically retries failed sends
• Error Handling: Continues with remaining emails if some fail

MONITORING:
• Real-time progress updates
• Success/failure statistics
• Detailed logs of all activities
• Batch-by-batch status tracking

SCHEDULE PERSISTENCE:
• Schedules are saved automatically
• Can resume after application restart
• Full backup and recovery system
• Export capabilities for reporting

RECOMMENDATIONS:
• Start with smaller lists to test
• Monitor initial batches closely
• Adjust timing based on your audience
• Keep Outlook running during sending
• Review logs regularly for issues

WORKING WITH LARGE LISTS:
• Lists over 10,000 emails are split across multiple days
• Progress is saved continuously
• Can safely stop and resume at any time
• Detailed reporting shows exact progress
        """
        
        self._create_help_text_widget(parent, content)
    
    def _create_troubleshooting_tab(self, parent):
        """Create troubleshooting help content"""
        content = """
Troubleshooting Common Issues

OUTLOOK CONNECTION PROBLEMS:

Problem: "Outlook not connected" message
Solutions:
• Ensure Microsoft Outlook is installed and running
• Check that Outlook is configured with an email account
• Restart Outlook and try reconnecting
• Run the application as Administrator
• Check Windows firewall and antivirus settings

Problem: "COM object error"
Solutions:
• Install/reinstall pywin32 package
• Restart computer after installation
• Check for Outlook updates
• Verify Outlook is not in Safe Mode

EMAIL VALIDATION ISSUES:

Problem: Valid emails marked as invalid
Solutions:
• Check for hidden characters in email addresses
• Verify email format (no spaces, proper @ symbol)
• Review international domain settings
• Check validation settings in application

Problem: Large number of duplicates found
Solutions:
• Review source data for actual duplicates
• Check for different formatting of same address
• Consider case sensitivity settings

SCHEDULING PROBLEMS:

Problem: Schedule not starting
Solutions:
• Verify Outlook connection is active
• Check that email list is loaded
• Ensure subject and message are filled
• Review error messages in logs

Problem: Emails not sending
Solutions:
• Check Outlook security prompts
• Verify internet connection
• Confirm Outlook account is working
• Review attachment file paths

PERFORMANCE ISSUES:

Problem: Application running slowly
Solutions:
• Reduce batch size in settings
• Clear application cache
• Close unnecessary programs
• Check available disk space
• Consider splitting large email lists

Problem: High memory usage
Solutions:
• Restart the application
• Process smaller lists at a time
• Check for memory leaks in logs
• Update to latest version

FILE HANDLING ISSUES:

Problem: Cannot open Excel file
Solutions:
• Check file is not open in another program
• Verify file format (.xlsx, .xls)
• Ensure file is not corrupted
• Try saving file in different format

Problem: Attachment files not found
Solutions:
• Verify file paths are correct
• Check file permissions
• Ensure files are not moved/deleted
• Use full file paths instead of relative

GENERAL TROUBLESHOOTING:

1. Check the Diagnostics tab for system status
2. Review application logs for detailed error messages
3. Restart the application if experiencing issues
4. Ensure all required files are in correct locations
5. Check system requirements are met

GETTING HELP:
• Use the built-in diagnostics tools
• Export error logs for analysis
• Check system information in About dialog
• Contact support with specific error messages

PREVENTION:
• Keep regular backups of email lists
• Test with small batches first
• Monitor system resources during large sends
• Keep application and dependencies updated
        """
        
        self._create_help_text_widget(parent, content)
    
    def _create_help_text_widget(self, parent, content):
        """Create a text widget with help content"""
        try:
            # Create frame with scrollbar
            text_frame = tk.Frame(parent, bg='white')
            text_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Create text widget
            text_widget = tk.Text(
                text_frame,
                font=('Segoe UI', 10),
                bg='white',
                wrap='word',
                padx=15,
                pady=15
            )
            
            # Create scrollbar
            scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            # Pack widgets
            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            # Insert content
            text_widget.insert('1.0', content.strip())
            text_widget.config(state='disabled')
            
        except Exception as e:
            logger.error(f"Error creating help text widget: {e}")