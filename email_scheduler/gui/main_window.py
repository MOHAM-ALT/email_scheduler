# gui/main_window.py
"""
Main Window - Professional GUI Interface
Advanced email scheduler interface with modern design and comprehensive functionality
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import webbrowser

from .components.dashboard_frame import DashboardFrame
from .components.email_setup_frame import EmailSetupFrame
from .components.schedule_frame import ScheduleFrame
from .components.monitoring_frame import MonitoringFrame
from .components.settings_frame import SettingsFrame
from .components.diagnostics_frame import DiagnosticsFrame
from .components.status_bar import StatusBar
from .dialogs.about_dialog import AboutDialog
from .dialogs.help_dialog import HelpDialog
from .utils.gui_utils import GuiUtils

logger = logging.getLogger(__name__)

class MainWindow:
    """Main application window with comprehensive GUI"""
    
    def __init__(self, app_manager, config_manager):
        self.app_manager = app_manager
        self.config_manager = config_manager
        
        # GUI components
        self.root = None
        self.notebook = None
        self.frames = {}
        self.status_bar = None
        
        # Application state
        self.running = False
        self.current_theme = "default"
        
        # Update timers
        self.update_timers = {}
        
        # Setup GUI
        self._setup_gui()
        
        # Initialize components
        self._initialize_components()
        
        # Start update cycle
        self._start_update_cycle()
    
    def _setup_gui(self):
        """Setup main GUI window and basic components"""
        self.root = tk.Tk()
        
        # Window configuration
        self.root.title("Professional Email Scheduler v4.0 - Advanced Email Management System")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Configure style
        self._setup_styles()
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create main layout
        self._create_main_layout()
        
        # Setup window events
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.bind("<F5>", lambda e: self._refresh_all())
        self.root.bind("<F1>", lambda e: self._show_help())
        
        # Center window
        GuiUtils.center_window(self.root)
        
        logger.info("Main window setup completed")
    
    def _setup_styles(self):
        """Setup GUI styles and themes"""
        style = ttk.Style()
        
        # Use modern theme
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        
        # Custom styles
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Heading.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
        
        # Notebook styles
        style.configure('TNotebook', tabposition='n')
        style.configure('TNotebook.Tab', padding=[20, 10])
        
        logger.info("GUI styles configured")
    
    def _create_menu_bar(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Schedule", command=self._new_schedule, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Schedule", command=self._open_schedule, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Schedule", command=self._save_schedule, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self._save_schedule_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Import Configuration", command=self._import_config)
        file_menu.add_command(label="Export Configuration", command=self._export_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing, accelerator="Alt+F4")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Preferences", command=self._show_preferences, accelerator="Ctrl+,")
        edit_menu.add_command(label="Reset to Defaults", command=self._reset_to_defaults)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Test Outlook Connection", command=self._test_outlook)
        tools_menu.add_command(label="Validate Email List", command=self._validate_emails)
        tools_menu.add_command(label="System Diagnostics", command=self._show_diagnostics)
        tools_menu.add_command(label="Performance Monitor", command=self._show_performance_monitor)
        tools_menu.add_separator()
        tools_menu.add_command(label="Repair Dependencies", command=self._repair_dependencies)
        tools_menu.add_command(label="Clear Cache", command=self._clear_cache)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh All", command=self._refresh_all, accelerator="F5")
        view_menu.add_command(label="Full Screen", command=self._toggle_fullscreen, accelerator="F11")
        view_menu.add_separator()
        
        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Default", command=lambda: self._change_theme("default"))
        theme_menu.add_command(label="Dark", command=lambda: self._change_theme("dark"))
        theme_menu.add_command(label="Light", command=lambda: self._change_theme("light"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self._show_help, accelerator="F1")
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_command(label="Troubleshooting", command=self._show_troubleshooting)
        help_menu.add_separator()
        help_menu.add_command(label="Check for Updates", command=self._check_updates)
        help_menu.add_command(label="Report Bug", command=self._report_bug)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self._new_schedule())
        self.root.bind('<Control-o>', lambda e: self._open_schedule())
        self.root.bind('<Control-s>', lambda e: self._save_schedule())
        self.root.bind('<Control-comma>', lambda e: self._show_preferences())
        self.root.bind('<F11>', lambda e: self._toggle_fullscreen())
    
    def _create_main_layout(self):
        """Create main application layout"""
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True)
        
        # Create status bar
        self.status_bar = StatusBar(self.root, self.app_manager)
        
        logger.info("Main layout created")
    
    def _initialize_components(self):
        """Initialize all GUI components/tabs"""
        try:
            # Dashboard tab
            self.frames['dashboard'] = DashboardFrame(
                self.notebook, self.app_manager, self.config_manager
            )
            self.notebook.add(
                self.frames['dashboard'].frame, 
                text="🏠 Dashboard"
            )
            
            # Email Setup tab
            self.frames['email_setup'] = EmailSetupFrame(
                self.notebook, self.app_manager, self.config_manager
            )
            self.notebook.add(
                self.frames['email_setup'].frame, 
                text="✉️ Email Setup"
            )
            
            # Schedule Management tab
            self.frames['schedule'] = ScheduleFrame(
                self.notebook, self.app_manager, self.config_manager
            )
            self.notebook.add(
                self.frames['schedule'].frame, 
                text="📅 Schedule"
            )
            
            # Monitoring tab
            self.frames['monitoring'] = MonitoringFrame(
                self.notebook, self.app_manager, self.config_manager
            )
            self.notebook.add(
                self.frames['monitoring'].frame, 
                text="📊 Monitoring"
            )
            
            # Settings tab
            self.frames['settings'] = SettingsFrame(
                self.notebook, self.app_manager, self.config_manager
            )
            self.notebook.add(
                self.frames['settings'].frame, 
                text="⚙️ Settings"
            )
            
            # Diagnostics tab
            self.frames['diagnostics'] = DiagnosticsFrame(
                self.notebook, self.app_manager, self.config_manager
            )
            self.notebook.add(
                self.frames['diagnostics'].frame, 
                text="🔧 Diagnostics"
            )
            
            logger.info("All GUI components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing GUI components: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize GUI components: {e}")
    
    def _start_update_cycle(self):
        """Start periodic update cycle for GUI components"""
        def update_dashboard():
            try:
                if 'dashboard' in self.frames:
                    self.frames['dashboard'].update_display()
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
            finally:
                # Schedule next update
                self.update_timers['dashboard'] = self.root.after(5000, update_dashboard)
        
        def update_monitoring():
            try:
                if 'monitoring' in self.frames:
                    self.frames['monitoring'].update_display()
            except Exception as e:
                logger.error(f"Monitoring update error: {e}")
            finally:
                # Schedule next update
                self.update_timers['monitoring'] = self.root.after(10000, update_monitoring)
        
        def update_status_bar():
            try:
                if self.status_bar:
                    self.status_bar.update_status()
            except Exception as e:
                logger.error(f"Status bar update error: {e}")
            finally:
                # Schedule next update
                self.update_timers['status_bar'] = self.root.after(2000, update_status_bar)
        
        # Start update cycles
        self.update_timers['dashboard'] = self.root.after(1000, update_dashboard)
        self.update_timers['monitoring'] = self.root.after(2000, update_monitoring)
        self.update_timers['status_bar'] = self.root.after(500, update_status_bar)
        
        logger.info("Update cycles started")
    
    def _stop_update_cycle(self):
        """Stop all update cycles"""
        for timer_name, timer_id in self.update_timers.items():
            try:
                self.root.after_cancel(timer_id)
                logger.debug(f"Cancelled update timer: {timer_name}")
            except Exception as e:
                logger.warning(f"Error cancelling timer {timer_name}: {e}")
        
        self.update_timers.clear()
        logger.info("Update cycles stopped")
    
    # Menu action handlers
    def _new_schedule(self):
        """Create new schedule"""
        try:
            if 'schedule' in self.frames:
                self.frames['schedule'].new_schedule()
                self.notebook.select(self.frames['schedule'].frame)
        except Exception as e:
            logger.error(f"Error creating new schedule: {e}")
            messagebox.showerror("Error", f"Failed to create new schedule: {e}")
    
    def _open_schedule(self):
        """Open existing schedule file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Open Schedule File",
                filetypes=[
                    ("Excel files", "*.xlsx *.xls"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                if 'schedule' in self.frames:
                    self.frames['schedule'].load_schedule(file_path)
                    self.notebook.select(self.frames['schedule'].frame)
        except Exception as e:
            logger.error(f"Error opening schedule: {e}")
            messagebox.showerror("Error", f"Failed to open schedule: {e}")
    
    def _save_schedule(self):
        """Save current schedule"""
        try:
            if 'schedule' in self.frames:
                self.frames['schedule'].save_schedule()
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")
            messagebox.showerror("Error", f"Failed to save schedule: {e}")
    
    def _save_schedule_as(self):
        """Save schedule with new name"""
        try:
            if 'schedule' in self.frames:
                self.frames['schedule'].save_schedule_as()
        except Exception as e:
            logger.error(f"Error saving schedule as: {e}")
            messagebox.showerror("Error", f"Failed to save schedule: {e}")
    
    def _import_config(self):
        """Import configuration from file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Import Configuration",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                success = self.config_manager.import_config(file_path)
                if success:
                    messagebox.showinfo("Success", "Configuration imported successfully")
                    self._refresh_all()
                else:
                    messagebox.showerror("Error", "Failed to import configuration")
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            messagebox.showerror("Error", f"Failed to import configuration: {e}")
    
    def _export_config(self):
        """Export configuration to file"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Configuration",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                success = self.config_manager.export_config(file_path)
                if success:
                    messagebox.showinfo("Success", "Configuration exported successfully")
                else:
                    messagebox.showerror("Error", "Failed to export configuration")
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            messagebox.showerror("Error", f"Failed to export configuration: {e}")
    
    def _show_preferences(self):
        """Show preferences dialog"""
        try:
            if 'settings' in self.frames:
                self.notebook.select(self.frames['settings'].frame)
        except Exception as e:
            logger.error(f"Error showing preferences: {e}")
    
    def _reset_to_defaults(self):
        """Reset configuration to defaults"""
        try:
            result = messagebox.askyesno(
                "Reset to Defaults",
                "Are you sure you want to reset all settings to defaults?\n\nThis action cannot be undone."
            )
            
            if result:
                success = self.config_manager.reset_to_factory_defaults()
                if success:
                    messagebox.showinfo("Success", "Settings reset to defaults")
                    self._refresh_all()
                else:
                    messagebox.showerror("Error", "Failed to reset settings")
        except Exception as e:
            logger.error(f"Error resetting to defaults: {e}")
            messagebox.showerror("Error", f"Failed to reset settings: {e}")
    
    def _test_outlook(self):
        """Test Outlook connection"""
        try:
            outlook_manager = self.app_manager.get_outlook_manager()
            if outlook_manager:
                test_results = outlook_manager.test_connection()
                
                # Show results dialog
                self._show_test_results("Outlook Connection Test", test_results)
            else:
                messagebox.showerror("Error", "Outlook manager not available")
        except Exception as e:
            logger.error(f"Error testing Outlook: {e}")
            messagebox.showerror("Error", f"Failed to test Outlook connection: {e}")
    
    def _validate_emails(self):
        """Validate email list"""
        try:
            if 'email_setup' in self.frames:
                self.frames['email_setup'].validate_emails()
                self.notebook.select(self.frames['email_setup'].frame)
        except Exception as e:
            logger.error(f"Error validating emails: {e}")
            messagebox.showerror("Error", f"Failed to validate emails: {e}")
    
    def _show_diagnostics(self):
        """Show system diagnostics"""
        try:
            if 'diagnostics' in self.frames:
                self.notebook.select(self.frames['diagnostics'].frame)
                self.frames['diagnostics'].run_full_diagnostics()
        except Exception as e:
            logger.error(f"Error showing diagnostics: {e}")
            messagebox.showerror("Error", f"Failed to show diagnostics: {e}")
    
    def _show_performance_monitor(self):
        """Show performance monitor"""
        try:
            if 'monitoring' in self.frames:
                self.notebook.select(self.frames['monitoring'].frame)
                self.frames['monitoring'].show_performance_details()
        except Exception as e:
            logger.error(f"Error showing performance monitor: {e}")
    
    def _repair_dependencies(self):
        """Repair dependencies"""
        try:
            dependency_manager = self.app_manager.get_component('dependency_manager')
            if dependency_manager:
                # Show progress dialog
                progress_dialog = self._show_progress_dialog("Repairing Dependencies", "Checking and repairing package dependencies...")
                
                def repair_thread():
                    try:
                        result = dependency_manager.ensure_all_dependencies()
                        self.root.after(0, lambda: self._handle_repair_result(result, progress_dialog))
                    except Exception as e:
                        self.root.after(0, lambda: self._handle_repair_error(e, progress_dialog))
                
                threading.Thread(target=repair_thread, daemon=True).start()
            else:
                messagebox.showerror("Error", "Dependency manager not available")
        except Exception as e:
            logger.error(f"Error repairing dependencies: {e}")
            messagebox.showerror("Error", f"Failed to repair dependencies: {e}")
    
    def _clear_cache(self):
        """Clear application cache"""
        try:
            result = messagebox.askyesno(
                "Clear Cache",
                "Are you sure you want to clear all application cache?\n\nThis may improve performance but will require reloading data."
            )
            
            if result:
                # Clear various caches
                cache_cleared = False
                
                # Clear file manager cache
                file_manager = self.app_manager.get_file_manager()
                if file_manager and hasattr(file_manager, 'clear_cache'):
                    file_manager.clear_cache()
                    cache_cleared = True
                
                # Clear email processor cache
                email_processor = self.app_manager.get_email_processor()
                if email_processor and hasattr(email_processor, 'clear_cache'):
                    email_processor.clear_cache()
                    cache_cleared = True
                
                if cache_cleared:
                    messagebox.showinfo("Success", "Cache cleared successfully")
                    self._refresh_all()
                else:
                    messagebox.showinfo("Info", "No cache to clear")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            messagebox.showerror("Error", f"Failed to clear cache: {e}")
    
    def _refresh_all(self):
        """Refresh all GUI components"""
        try:
            for frame_name, frame in self.frames.items():
                if hasattr(frame, 'refresh'):
                    try:
                        frame.refresh()
                    except Exception as e:
                        logger.warning(f"Error refreshing {frame_name}: {e}")
            
            if self.status_bar:
                self.status_bar.update_status()
            
            logger.info("All components refreshed")
        except Exception as e:
            logger.error(f"Error refreshing components: {e}")
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        try:
            current_state = self.root.attributes('-fullscreen')
            self.root.attributes('-fullscreen', not current_state)
        except Exception as e:
            logger.error(f"Error toggling fullscreen: {e}")
    
    def _change_theme(self, theme_name):
        """Change application theme"""
        try:
            self.current_theme = theme_name
            # Theme changing logic would be implemented here
            logger.info(f"Theme changed to: {theme_name}")
        except Exception as e:
            logger.error(f"Error changing theme: {e}")
    
    def _show_help(self):
        """Show help dialog"""
        try:
            help_dialog = HelpDialog(self.root)
            help_dialog.show()
        except Exception as e:
            logger.error(f"Error showing help: {e}")
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts"""
        try:
            shortcuts_text = """
Keyboard Shortcuts:

File Operations:
Ctrl+N          New Schedule
Ctrl+O          Open Schedule
Ctrl+S          Save Schedule
Ctrl+Shift+S    Save As
Ctrl+,          Preferences
Alt+F4          Exit

View:
F5              Refresh All
F11             Toggle Fullscreen
F1              Help

Tools:
Ctrl+T          Test Outlook Connection
Ctrl+D          System Diagnostics
Ctrl+M          Performance Monitor

Navigation:
Ctrl+Tab        Next Tab
Ctrl+Shift+Tab  Previous Tab
Ctrl+1-6        Go to Tab 1-6
            """
            
            messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)
        except Exception as e:
            logger.error(f"Error showing shortcuts: {e}")
    
    def _show_troubleshooting(self):
        """Show troubleshooting guide"""
        try:
            troubleshooting_text = """
Common Issues and Solutions:

1. Outlook Connection Problems:
   - Ensure Microsoft Outlook is installed and running
   - Check if pywin32 package is installed: pip install pywin32
   - Try restarting Outlook application
   - Run as administrator if permission issues

2. Email Validation Errors:
   - Verify email format in Excel file
   - Check for hidden characters or spaces
   - Ensure one email per row in first column

3. Scheduling Issues:
   - Check system time and date
   - Verify Outlook calendar permissions
   - Ensure sufficient disk space

4. Performance Problems:
   - Clear application cache (Tools > Clear Cache)
   - Reduce batch size in settings
   - Close unnecessary applications

5. Installation Issues:
   - Run installer as administrator
   - Check internet connection for package downloads
   - Temporarily disable antivirus during installation

For additional help, visit the documentation or contact support.
            """
            
            messagebox.showinfo("Troubleshooting Guide", troubleshooting_text)
        except Exception as e:
            logger.error(f"Error showing troubleshooting: {e}")
    
    def _check_updates(self):
        """Check for application updates"""
        try:
            # Simulated update check
            messagebox.showinfo(
                "Update Check", 
                "You are running the latest version of Professional Email Scheduler v4.0.\n\nNo updates available at this time."
            )
        except Exception as e:
            logger.error(f"Error checking updates: {e}")
    
    def _report_bug(self):
        """Open bug report page"""
        try:
            webbrowser.open("mailto:support@emailscheduler.com?subject=Bug%20Report%20-%20Email%20Scheduler%20v4.0")
        except Exception as e:
            logger.error(f"Error opening bug report: {e}")
            messagebox.showerror("Error", "Failed to open email client for bug report")
    
    def _show_about(self):
        """Show about dialog"""
        try:
            about_dialog = AboutDialog(self.root, self.app_manager)
            about_dialog.show()
        except Exception as e:
            logger.error(f"Error showing about dialog: {e}")
    
    def _show_test_results(self, title, results):
        """Show test results in a dialog"""
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title(title)
            dialog.geometry("600x400")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Center dialog
            GuiUtils.center_window(dialog)
            
            # Create text widget with scrollbar
            text_frame = ttk.Frame(dialog)
            text_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            text_widget = scrolledtext.ScrolledText(
                text_frame,
                font=('Consolas', 10),
                wrap='word'
            )
            text_widget.pack(fill='both', expand=True)
            
            # Format and display results
            result_text = f"Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            result_text += "=" * 60 + "\n\n"
            
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, dict):
                        result_text += f"{key.replace('_', ' ').title()}:\n"
                        for sub_key, sub_value in value.items():
                            result_text += f"  {sub_key.replace('_', ' ').title()}: {sub_value}\n"
                        result_text += "\n"
                    else:
                        result_text += f"{key.replace('_', ' ').title()}: {value}\n"
            else:
                result_text += str(results)
            
            text_widget.insert('1.0', result_text)
            text_widget.config(state='disabled')
            
            # Close button
            ttk.Button(
                dialog,
                text="Close",
                command=dialog.destroy
            ).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error showing test results: {e}")
    
    def _show_progress_dialog(self, title, message):
        """Show progress dialog"""
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title(title)
            dialog.geometry("400x150")
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.resizable(False, False)
            
            # Center dialog
            GuiUtils.center_window(dialog)
            
            # Message label
            ttk.Label(
                dialog,
                text=message,
                font=('Segoe UI', 10)
            ).pack(pady=20)
            
            # Progress bar
            progress = ttk.Progressbar(
                dialog,
                mode='indeterminate',
                length=300
            )
            progress.pack(pady=10)
            progress.start()
            
            # Cancel button
            ttk.Button(
                dialog,
                text="Cancel",
                command=dialog.destroy
            ).pack(pady=10)
            
            return dialog
            
        except Exception as e:
            logger.error(f"Error showing progress dialog: {e}")
            return None
    
    def _handle_repair_result(self, result, progress_dialog):
        """Handle dependency repair result"""
        try:
            if progress_dialog:
                progress_dialog.destroy()
            
            if result.success:
                message = "Dependencies repaired successfully!"
                if result.installed_packages:
                    message += f"\n\nInstalled packages:\n" + "\n".join(result.installed_packages)
                if result.warnings:
                    message += f"\n\nWarnings:\n" + "\n".join(result.warnings)
                
                messagebox.showinfo("Repair Complete", message)
                self._refresh_all()
            else:
                message = f"Dependency repair failed: {result.message}"
                if result.failed_packages:
                    message += f"\n\nFailed packages:\n" + "\n".join(result.failed_packages)
                
                messagebox.showerror("Repair Failed", message)
        except Exception as e:
            logger.error(f"Error handling repair result: {e}")
    
    def _handle_repair_error(self, error, progress_dialog):
        """Handle dependency repair error"""
        try:
            if progress_dialog:
                progress_dialog.destroy()
            
            messagebox.showerror("Repair Error", f"An error occurred during repair: {error}")
        except Exception as e:
            logger.error(f"Error handling repair error: {e}")
    
    def _on_closing(self):
        """Handle window closing event"""
        try:
            # Check if any operations are running
            scheduler_manager = self.app_manager.get_scheduler_manager()
            if scheduler_manager and hasattr(scheduler_manager, 'is_running') and scheduler_manager.is_running():
                result = messagebox.askyesno(
                    "Confirm Exit",
                    "Email scheduling is currently active. Are you sure you want to exit?\n\nThis will stop all scheduled operations."
                )
                if not result:
                    return
            
            # Save current configuration
            try:
                self.config_manager.save_config()
            except Exception as e:
                logger.warning(f"Error saving configuration on exit: {e}")
            
            # Stop update cycles
            self._stop_update_cycle()
            
            # Cleanup components
            for frame_name, frame in self.frames.items():
                if hasattr(frame, 'cleanup'):
                    try:
                        frame.cleanup()
                    except Exception as e:
                        logger.warning(f"Error cleaning up {frame_name}: {e}")
            
            # Cleanup status bar
            if self.status_bar:
                self.status_bar.cleanup()
            
            self.running = False
            logger.info("Main window closing")
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"Error during window closing: {e}")
            # Force close if cleanup fails
            self.root.destroy()
    
    def run(self):
        """Start the main GUI loop"""
        try:
            self.running = True
            logger.info("Starting main GUI loop")
            
            # Show startup message
            if self.status_bar:
                self.status_bar.set_message("Professional Email Scheduler ready")
            
            # Check initial system status
            self._check_initial_status()
            
            # Start main loop
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Error in main GUI loop: {e}")
            messagebox.showerror("Critical Error", f"A critical error occurred: {e}")
        finally:
            self.running = False
            logger.info("Main GUI loop ended")
    
    def _check_initial_status(self):
        """Check initial system status and show warnings if needed"""
        try:
            # Check application manager status
            if not self.app_manager.is_ready():
                messagebox.showwarning(
                    "System Warning",
                    "Some system components are not fully initialized.\n\nPlease check the Diagnostics tab for details."
                )
            
            # Check Outlook connection
            outlook_manager = self.app_manager.get_outlook_manager()
            if outlook_manager and not outlook_manager.is_connected():
                messagebox.showwarning(
                    "Outlook Warning",
                    "Outlook connection is not available.\n\nSome features may be limited. Please check Outlook installation and try reconnecting."
                )
            
        except Exception as e:
            logger.error(f"Error checking initial status: {e}")
    
    def cleanup(self):
        """Cleanup main window resources"""
        try:
            if self.running:
                self._on_closing()
        except Exception as e:
            logger.error(f"Error during main window cleanup: {e}")
    
    # Public methods for external access
    def get_current_tab(self):
        """Get currently selected tab"""
        try:
            if self.notebook:
                current_tab = self.notebook.select()
                tab_text = self.notebook.tab(current_tab, "text")
                return tab_text
        except Exception:
            return None
    
    def switch_to_tab(self, tab_name):
        """Switch to specific tab"""
        try:
            if tab_name in self.frames:
                self.notebook.select(self.frames[tab_name].frame)
                return True
        except Exception as e:
            logger.error(f"Error switching to tab {tab_name}: {e}")
        return False
    
    def show_notification(self, message, title="Notification", msg_type="info"):
        """Show notification message"""
        try:
            if msg_type == "error":
                messagebox.showerror(title, message)
            elif msg_type == "warning":
                messagebox.showwarning(title, message)
            elif msg_type == "question":
                return messagebox.askyesno(title, message)
            else:
                messagebox.showinfo(title, message)
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
        return None
    
    def set_status_message(self, message):
        """Set status bar message"""
        try:
            if self.status_bar:
                self.status_bar.set_message(message)
        except Exception as e:
            logger.error(f"Error setting status message: {e}")
    
    def update_progress(self, percentage, message=""):
        """Update progress display"""
        try:
            if self.status_bar:
                self.status_bar.set_progress(percentage, message)
        except Exception as e:
            logger.error(f"Error updating progress: {e}")