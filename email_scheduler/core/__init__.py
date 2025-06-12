# core/__init__.py
"""
Core Module - Professional Email Scheduler
Initialization file for core components
"""

__version__ = "4.0.0"
__author__ = "Professional Email Scheduler Team"
__description__ = "Advanced email scheduling and management system"

# Import core components
from .app_manager import ApplicationManager
from .config_manager import ConfigManager
from .dependency_manager import DependencyManager
from .exception_handler import GlobalExceptionHandler
from .outlook_manager import OutlookManager
from .email_processor import EmailProcessor
from .scheduler_manager import SchedulerManager
from .file_manager import FileManager
from .validation_engine import ValidationEngine

# Version information
VERSION_INFO = {
    'major': 4,
    'minor': 0,
    'patch': 0,
    'release': 'stable'
}

def get_version():
    """Get version string"""
    return f"{VERSION_INFO['major']}.{VERSION_INFO['minor']}.{VERSION_INFO['patch']}"

def get_version_info():
    """Get detailed version information"""
    return VERSION_INFO.copy()

# Component registry for dynamic loading
CORE_COMPONENTS = {
    'app_manager': ApplicationManager,
    'config_manager': ConfigManager,
    'dependency_manager': DependencyManager,
    'exception_handler': GlobalExceptionHandler,
    'outlook_manager': OutlookManager,
    'email_processor': EmailProcessor,
    'scheduler_manager': SchedulerManager,
    'file_manager': FileManager,
    'validation_engine': ValidationEngine
}

def get_component_class(component_name):
    """Get component class by name"""
    return CORE_COMPONENTS.get(component_name)

def list_components():
    """List available core components"""
    return list(CORE_COMPONENTS.keys())

__all__ = [
    'ApplicationManager',
    'ConfigManager', 
    'DependencyManager',
    'GlobalExceptionHandler',
    'OutlookManager',
    'EmailProcessor',
    'SchedulerManager',
    'FileManager',
    'ValidationEngine',
    'get_version',
    'get_version_info',
    'get_component_class',
    'list_components'
]