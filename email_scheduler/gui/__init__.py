# gui/__init__.py
"""
GUI Module - Professional Email Scheduler
Graphical User Interface components and utilities
"""

from .main_window import MainWindow

__version__ = "4.0.0"
__description__ = "Professional GUI components for email scheduling"

# GUI component registry
GUI_COMPONENTS = {
    'main_window': MainWindow
}

def get_gui_component(component_name):
    """Get GUI component class by name"""
    return GUI_COMPONENTS.get(component_name)

def list_gui_components():
    """List available GUI components"""
    return list(GUI_COMPONENTS.keys())

__all__ = [
    'MainWindow',
    'get_gui_component',
    'list_gui_components'
]