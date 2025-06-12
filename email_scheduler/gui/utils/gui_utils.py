# gui/utils/gui_utils.py
"""
GUI Utilities - Helper Functions
Common GUI utility functions and helpers
"""

import tkinter as tk
from tkinter import ttk
import threading
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class GuiUtils:
    """Collection of GUI utility functions"""
    
    @staticmethod
    def center_window(window, width=None, height=None):
        """Center a window on the screen"""
        try:
            window.update_idletasks()
            
            # Get current window size if not specified
            if width is None:
                width = window.winfo_width()
            if height is None:
                height = window.winfo_height()
            
            # Calculate position
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
            window.geometry(f"{width}x{height}+{x}+{y}")
            
        except Exception as e:
            logger.warning(f"Failed to center window: {e}")
    
    @staticmethod
    def create_styled_button(parent, text, command=None, style="default", **kwargs):
        """Create a styled button with consistent appearance"""
        try:
            style_configs = {
                "default": {"bg": "#007ACC", "fg": "white", "relief": "flat"},
                "success": {"bg": "#28a745", "fg": "white", "relief": "flat"},
                "warning": {"bg": "#ffc107", "fg": "black", "relief": "flat"},
                "danger": {"bg": "#dc3545", "fg": "white", "relief": "flat"},
                "secondary": {"bg": "#6c757d", "fg": "white", "relief": "flat"}
            }
            
            config = style_configs.get(style, style_configs["default"])
            config.update(kwargs)
            
            button = tk.Button(
                parent,
                text=text,
                command=command,
                font=('Segoe UI', 10),
                padx=15,
                pady=8,
                cursor='hand2',
                **config
            )
            
            # Add hover effects
            def on_enter(e):
                button.config(relief="raised")
            
            def on_leave(e):
                button.config(relief="flat")
            
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
            
            return button
            
        except Exception as e:
            logger.error(f"Error creating styled button: {e}")
            return tk.Button(parent, text=text, command=command)
    
    @staticmethod
    def create_label_frame(parent, title, **kwargs):
        """Create a styled label frame"""
        try:
            frame = tk.LabelFrame(
                parent,
                text=title,
                font=('Segoe UI', 10, 'bold'),
                bg='white',
                fg='#2c3e50',
                relief='solid',
                bd=1,
                **kwargs
            )
            return frame
            
        except Exception as e:
            logger.error(f"Error creating label frame: {e}")
            return tk.LabelFrame(parent, text=title)
    
    @staticmethod
    def create_progress_dialog(parent, title, message, can_cancel=True):
        """Create a progress dialog"""
        try:
            dialog = tk.Toplevel(parent)
            dialog.title(title)
            dialog.geometry("400x150")
            dialog.transient(parent)
            dialog.grab_set()
            dialog.resizable(False, False)
            
            GuiUtils.center_window(dialog, 400, 150)
            
            # Message label
            message_label = tk.Label(
                dialog,
                text=message,
                font=('Segoe UI', 10),
                wraplength=350
            )
            message_label.pack(pady=20)
            
            # Progress bar
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(
                dialog,
                variable=progress_var,
                maximum=100,
                length=300
            )
            progress_bar.pack(pady=10)
            
            # Cancel button
            cancelled = {'value': False}
            
            if can_cancel:
                def cancel():
                    cancelled['value'] = True
                    dialog.destroy()
                
                cancel_btn = GuiUtils.create_styled_button(
                    dialog,
                    "Cancel",
                    command=cancel,
                    style="secondary"
                )
                cancel_btn.pack(pady=10)
            
            dialog.progress_var = progress_var
            dialog.message_label = message_label
            dialog.cancelled = cancelled
            
            return dialog
            
        except Exception as e:
            logger.error(f"Error creating progress dialog: {e}")
            return None
    
    @staticmethod
    def show_info_dialog(parent, title, message, details=None):
        """Show an information dialog with optional details"""
        try:
            dialog = tk.Toplevel(parent)
            dialog.title(title)
            dialog.geometry("500x300" if details else "400x150")
            dialog.transient(parent)
            dialog.grab_set()
            
            GuiUtils.center_window(dialog)
            
            # Main message
            message_label = tk.Label(
                dialog,
                text=message,
                font=('Segoe UI', 10),
                wraplength=450,
                justify='left'
            )
            message_label.pack(pady=20, padx=20)
            
            # Details section
            if details:
                details_frame = GuiUtils.create_label_frame(dialog, "Details")
                details_frame.pack(fill='both', expand=True, padx=20, pady=10)
                
                details_text = tk.Text(
                    details_frame,
                    font=('Consolas', 9),
                    wrap='word',
                    height=8
                )
                details_text.pack(fill='both', expand=True, padx=10, pady=10)
                
                details_text.insert('1.0', details)
                details_text.config(state='disabled')
            
            # OK button
            ok_btn = GuiUtils.create_styled_button(
                dialog,
                "OK",
                command=dialog.destroy
            )
            ok_btn.pack(pady=10)
            
            return dialog
            
        except Exception as e:
            logger.error(f"Error showing info dialog: {e}")
            return None
    
    @staticmethod
    def validate_entry_input(entry_widget, validation_func, error_message="Invalid input"):
        """Add validation to an entry widget"""
        try:
            def validate():
                try:
                    value = entry_widget.get()
                    if validation_func(value):
                        entry_widget.config(bg='white')
                        return True
                    else:
                        entry_widget.config(bg='#ffcccc')
                        return False
                except Exception:
                    entry_widget.config(bg='#ffcccc')
                    return False
            
            entry_widget.validate_func = validate
            entry_widget.bind('<KeyRelease>', lambda e: validate())
            entry_widget.bind('<FocusOut>', lambda e: validate())
            
        except Exception as e:
            logger.error(f"Error adding validation to entry: {e}")
    
    @staticmethod
    def create_tooltip(widget, text):
        """Add tooltip to a widget"""
        try:
            def show_tooltip(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                label = tk.Label(
                    tooltip,
                    text=text,
                    background='#ffffe0',
                    relief='solid',
                    borderwidth=1,
                    font=('Segoe UI', 9)
                )
                label.pack()
                
                def hide_tooltip():
                    tooltip.destroy()
                
                tooltip.after(3000, hide_tooltip)  # Auto hide after 3 seconds
                widget.tooltip = tooltip
            
            def hide_tooltip(event):
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
                    delattr(widget, 'tooltip')
            
            widget.bind('<Enter>', show_tooltip)
            widget.bind('<Leave>', hide_tooltip)
            
        except Exception as e:
            logger.error(f"Error creating tooltip: {e}")
    
    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in human readable format"""
        try:
            if size_bytes == 0:
                return "0 B"
            
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            unit_index = 0
            size = float(size_bytes)
            
            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1
            
            return f"{size:.1f} {units[unit_index]}"
            
        except Exception as e:
            logger.error(f"Error formatting file size: {e}")
            return f"{size_bytes} B"
    
    @staticmethod
    def format_datetime(dt, include_time=True):
        """Format datetime for display"""
        try:
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            
            if include_time:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return dt.strftime("%Y-%m-%d")
                
        except Exception as e:
            logger.error(f"Error formatting datetime: {e}")
            return str(dt)
    
    @staticmethod
    def safe_thread_call(root, func, *args, **kwargs):
        """Safely call function in main thread"""
        try:
            def wrapper():
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in thread call: {e}")
            
            root.after(0, wrapper)
            
        except Exception as e:
            logger.error(f"Error scheduling thread call: {e}")
    
    @staticmethod
    def create_scrollable_frame(parent):
        """Create a scrollable frame"""
        try:
            # Create canvas and scrollbar
            canvas = tk.Canvas(parent, bg='white')
            scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
            
            # Create frame inside canvas
            scrollable_frame = tk.Frame(canvas, bg='white')
            
            # Configure scrolling
            def configure_scroll_region(event):
                canvas.configure(scrollreg