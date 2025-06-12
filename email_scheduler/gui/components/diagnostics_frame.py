# gui/components/diagnostics_frame.py
"""
Diagnostics Frame - System Diagnostics Component
Comprehensive system health monitoring and troubleshooting tools
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import logging
import threading
from datetime import datetime
from ..utils.gui_utils import GuiUtils

logger = logging.getLogger(__name__)

class DiagnosticsFrame:
    """System diagnostics and health monitoring component"""
    
    def __init__(self, parent, app_manager, config_manager):
        self.parent = parent
        self.app_manager = app_manager
        self.config_manager = config_manager
        
        # Create main frame
        self.frame = tk.Frame(parent, bg='#f5f6fa')
        
        # Diagnostic elements
        self.status_displays = {}
        self.test_results = {}
        self.diagnostic_log = None
        
        # Create diagnostics interface
        self._create_interface()
        
        # Run initial diagnostics
        self._run_initial_diagnostics()
    
    def _create_interface(self):
        """Create diagnostics interface"""
        try:
            # System health section
            health_section = GuiUtils.create_label_frame(self.frame, "🏥 System Health Overview")
            health_section.pack(fill='x', padx=20, pady=10)
            
            health_grid = tk.Frame(health_section, bg='white')
            health_grid.pack(fill='x', padx=20, pady=15)
            
            # Create health indicators
            components = [
                ('application', 'Application Manager'),
                ('outlook', 'Outlook Integration'),
                ('email_processor', 'Email Processor'),
                ('scheduler', 'Scheduler Manager'),
                ('file_manager', '