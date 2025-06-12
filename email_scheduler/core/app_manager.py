# core/app_manager.py
"""
Application Manager - Central coordinator for all system components
Handles initialization, dependency management, and system health monitoring
"""

import logging
import threading
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from pathlib import Path

from .dependency_manager import DependencyManager
from .email_processor import EmailProcessor
from .scheduler_manager import SchedulerManager
from .outlook_manager import OutlookManager
from .file_manager import FileManager
from .validation_engine import ValidationEngine

logger = logging.getLogger(__name__)

@dataclass
class InitializationResult:
    """Result of application initialization"""
    success: bool
    message: str
    failed_components: List[str] = None
    warnings: List[str] = None

class ApplicationManager:
    """Central application manager that coordinates all components"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.dependency_manager = None
        self.email_processor = None
        self.scheduler_manager = None
        self.outlook_manager = None
        self.file_manager = None
        self.validation_engine = None
        
        # System state
        self.initialized = False
        self.running = False
        self.health_monitor_thread = None
        self.health_status = {}
        
        # Component registry
        self.components = {}
        
    def initialize(self) -> InitializationResult:
        """Initialize all application components with comprehensive error handling"""
        try:
            logger.info("Starting application component initialization")
            
            failed_components = []
            warnings = []
            
            # Step 1: Initialize dependency manager
            try:
                self.dependency_manager = DependencyManager()
                dependency_result = self.dependency_manager.ensure_all_dependencies()
                
                if not dependency_result.success:
                    warnings.extend(dependency_result.warnings)
                    if dependency_result.critical_failures:
                        failed_components.extend(dependency_result.critical_failures)
                        
                self.components['dependency_manager'] = self.dependency_manager
                logger.info("Dependency manager initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize dependency manager: {e}")
                failed_components.append('dependency_manager')
            
            # Step 2: Initialize file manager
            try:
                self.file_manager = FileManager(self.config_manager)
                self.file_manager.initialize()
                self.components['file_manager'] = self.file_manager
                logger.info("File manager initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize file manager: {e}")
                failed_components.append('file_manager')
            
            # Step 3: Initialize validation engine
            try:
                self.validation_engine = ValidationEngine()
                self.validation_engine.initialize()
                self.components['validation_engine'] = self.validation_engine
                logger.info("Validation engine initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize validation engine: {e}")
                failed_components.append('validation_engine')
            
            # Step 4: Initialize Outlook manager
            try:
                self.outlook_manager = OutlookManager(self.config_manager)
                outlook_result = self.outlook_manager.initialize()
                
                if outlook_result.success:
                    self.components['outlook_manager'] = self.outlook_manager
                    logger.info("Outlook manager initialized successfully")
                else:
                    warnings.append(f"Outlook initialization warning: {outlook_result.message}")
                    # Don't fail completely if Outlook fails
                    self.components['outlook_manager'] = self.outlook_manager
                    
            except Exception as e:
                logger.error(f"Failed to initialize Outlook manager: {e}")
                warnings.append(f"Outlook manager failed: {e}")
                # Create a dummy Outlook manager for graceful degradation
                self.outlook_manager = OutlookManager(self.config_manager, fallback_mode=True)
                self.components['outlook_manager'] = self.outlook_manager
            
            # Step 5: Initialize email processor
            try:
                self.email_processor = EmailProcessor(
                    self.outlook_manager,
                    self.validation_engine,
                    self.file_manager,
                    self.config_manager
                )
                self.email_processor.initialize()
                self.components['email_processor'] = self.email_processor
                logger.info("Email processor initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize email processor: {e}")
                failed_components.append('email_processor')
            
            # Step 6: Initialize scheduler manager
            try:
                self.scheduler_manager = SchedulerManager(
                    self.email_processor,
                    self.config_manager
                )
                self.scheduler_manager.initialize()
                self.components['scheduler_manager'] = self.scheduler_manager
                logger.info("Scheduler manager initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize scheduler manager: {e}")
                failed_components.append('scheduler_manager')
            
            # Step 7: Start health monitoring
            self._start_health_monitoring()
            
            # Determine overall initialization result
            critical_components = ['email_processor', 'scheduler_manager']
            critical_failures = [comp for comp in failed_components if comp in critical_components]
            
            if critical_failures:
                self.initialized = False
                return InitializationResult(
                    success=False,
                    message=f"Critical components failed: {', '.join(critical_failures)}",
                    failed_components=failed_components,
                    warnings=warnings
                )
            
            self.initialized = True
            self.running = True
            
            result_message = "Application initialized successfully"
            if warnings:
                result_message += f" with {len(warnings)} warnings"
            
            logger.info(result_message)
            
            return InitializationResult(
                success=True,
                message=result_message,
                failed_components=failed_components,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Critical error during initialization: {e}")
            return InitializationResult(
                success=False,
                message=f"Critical initialization error: {e}",
                failed_components=['application_manager']
            )
    
    def _start_health_monitoring(self):
        """Start background health monitoring"""
        def monitor_health():
            while self.running:
                try:
                    self._check_component_health()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Error in health monitoring: {e}")
                    time.sleep(60)  # Wait longer on error
        
        self.health_monitor_thread = threading.Thread(target=monitor_health, daemon=True)
        self.health_monitor_thread.start()
        logger.info("Health monitoring started")
    
    def _check_component_health(self):
        """Check health of all components"""
        for name, component in self.components.items():
            try:
                if hasattr(component, 'health_check'):
                    health_result = component.health_check()
                    self.health_status[name] = {
                        'status': 'healthy' if health_result else 'unhealthy',
                        'last_check': datetime.now(),
                        'details': getattr(health_result, 'details', None) if hasattr(health_result, 'details') else None
                    }
                else:
                    self.health_status[name] = {
                        'status': 'unknown',
                        'last_check': datetime.now(),
                        'details': 'Health check not implemented'
                    }
            except Exception as e:
                self.health_status[name] = {
                    'status': 'error',
                    'last_check': datetime.now(),
                    'details': str(e)
                }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'initialized': self.initialized,
            'running': self.running,
            'components': list(self.components.keys()),
            'health_status': self.health_status,
            'outlook_connected': self.outlook_manager.is_connected() if self.outlook_manager else False,
            'active_schedules': self.scheduler_manager.get_active_schedule_count() if self.scheduler_manager else 0,
            'uptime': time.time() - getattr(self, '_start_time', time.time())
        }
    
    def get_component(self, component_name: str):
        """Get a specific component by name"""
        return self.components.get(component_name)
    
    def restart_component(self, component_name: str) -> bool:
        """Restart a specific component"""
        try:
            logger.info(f"Restarting component: {component_name}")
            
            if component_name not in self.components:
                logger.error(f"Component not found: {component_name}")
                return False
            
            component = self.components[component_name]
            
            # Cleanup old component
            if hasattr(component, 'cleanup'):
                component.cleanup()
            
            # Reinitialize based on component type
            if component_name == 'outlook_manager':
                self.outlook_manager = OutlookManager(self.config_manager)
                result = self.outlook_manager.initialize()
                self.components['outlook_manager'] = self.outlook_manager
                return result.success
            
            # Add other component restart logic as needed
            
            logger.info(f"Component restarted successfully: {component_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart component {component_name}: {e}")
            return False
    
    def perform_self_diagnosis(self) -> Dict[str, Any]:
        """Perform comprehensive system self-diagnosis"""
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'unknown',
            'components': {},
            'recommendations': [],
            'critical_issues': [],
            'warnings': []
        }
        
        try:
            # Check each component
            healthy_count = 0
            total_count = len(self.components)
            
            for name, component in self.components.items():
                component_diag = {
                    'status': 'unknown',
                    'details': {},
                    'issues': [],
                    'recommendations': []
                }
                
                try:
                    if hasattr(component, 'self_diagnose'):
                        diag_result = component.self_diagnose()
                        component_diag.update(diag_result)
                    elif hasattr(component, 'health_check'):
                        health_ok = component.health_check()
                        component_diag['status'] = 'healthy' if health_ok else 'unhealthy'
                    
                    if component_diag['status'] == 'healthy':
                        healthy_count += 1
                    elif component_diag['status'] == 'unhealthy':
                        diagnosis['critical_issues'].extend(component_diag.get('issues', []))
                    
                except Exception as e:
                    component_diag['status'] = 'error'
                    component_diag['details'] = {'error': str(e)}
                    diagnosis['critical_issues'].append(f"Component {name} diagnosis failed: {e}")
                
                diagnosis['components'][name] = component_diag
            
            # Determine overall health
            if healthy_count == total_count:
                diagnosis['overall_health'] = 'healthy'
            elif healthy_count >= total_count * 0.7:
                diagnosis['overall_health'] = 'degraded'
            else:
                diagnosis['overall_health'] = 'unhealthy'
            
            # Generate recommendations
            if diagnosis['overall_health'] != 'healthy':
                diagnosis['recommendations'].append("Run component diagnostics")
                diagnosis['recommendations'].append("Check system logs for detailed error information")
            
            logger.info(f"Self-diagnosis completed. Overall health: {diagnosis['overall_health']}")
            
        except Exception as e:
            logger.error(f"Self-diagnosis failed: {e}")
            diagnosis['overall_health'] = 'error'
            diagnosis['critical_issues'].append(f"Self-diagnosis system failure: {e}")
        
        return diagnosis
    
    def cleanup(self):
        """Cleanup all components and resources"""
        try:
            logger.info("Starting application cleanup")
            
            self.running = False
            
            # Wait for health monitor to stop
            if self.health_monitor_thread and self.health_monitor_thread.is_alive():
                self.health_monitor_thread.join(timeout=5)
            
            # Cleanup components in reverse order
            cleanup_order = [
                'scheduler_manager',
                'email_processor',
                'outlook_manager',
                'validation_engine',
                'file_manager',
                'dependency_manager'
            ]
            
            for component_name in cleanup_order:
                if component_name in self.components:
                    try:
                        component = self.components[component_name]
                        if hasattr(component, 'cleanup'):
                            component.cleanup()
                        logger.info(f"Component cleaned up: {component_name}")
                    except Exception as e:
                        logger.error(f"Error cleaning up {component_name}: {e}")
            
            self.components.clear()
            self.initialized = False
            
            logger.info("Application cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    # Utility methods for GUI integration
    def is_ready(self) -> bool:
        """Check if the application is ready for use"""
        return self.initialized and self.running
    
    def get_email_processor(self):
        """Get the email processor component"""
        return self.email_processor
    
    def get_scheduler_manager(self):
        """Get the scheduler manager component"""
        return self.scheduler_manager
    
    def get_outlook_manager(self):
        """Get the Outlook manager component"""
        return self.outlook_manager
    
    def get_file_manager(self):
        """Get the file manager component"""
        return self.file_manager