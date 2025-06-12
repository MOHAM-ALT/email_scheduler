#!/usr/bin/env python3
"""
Professional Email Scheduler System
A comprehensive email management solution with advanced scheduling capabilities
Version: 4.0 Professional
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
def setup_logging():
    """Setup comprehensive logging system"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"email_scheduler_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Import core modules
try:
    from core.app_manager import ApplicationManager
    from core.config_manager import ConfigManager
    from core.exception_handler import GlobalExceptionHandler
    from gui.main_window import MainWindow
    
except ImportError as e:
    logger.error(f"Failed to import core modules: {e}")
    print("Error: Missing core modules. Please ensure all files are present.")
    sys.exit(1)

class EmailSchedulerApplication:
    """Main application class that orchestrates all components"""
    
    def __init__(self):
        self.app_manager = None
        self.config_manager = None
        self.main_window = None
        self.exception_handler = None
        
    def initialize(self):
        """Initialize all application components"""
        try:
            logger.info("Initializing Professional Email Scheduler v4.0")
            
            # Initialize exception handler first
            self.exception_handler = GlobalExceptionHandler()
            self.exception_handler.setup()
            
            # Initialize configuration
            self.config_manager = ConfigManager()
            self.config_manager.load_config()
            
            # Initialize application manager
            self.app_manager = ApplicationManager(self.config_manager)
            initialization_result = self.app_manager.initialize()
            
            if not initialization_result.success:
                logger.error(f"Application initialization failed: {initialization_result.message}")
                return False
            
            # Initialize main GUI
            self.main_window = MainWindow(self.app_manager, self.config_manager)
            
            logger.info("Application initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Critical error during initialization: {e}")
            return False
    
    def run(self):
        """Start the application"""
        try:
            if not self.initialize():
                print("Failed to initialize application. Check logs for details.")
                return False
            
            logger.info("Starting main application window")
            self.main_window.run()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            self.shutdown()
            
        except Exception as e:
            logger.error(f"Unexpected error in main application: {e}")
            self.shutdown()
            return False
    
    def shutdown(self):
        """Gracefully shutdown the application"""
        try:
            logger.info("Shutting down application")
            
            if self.app_manager:
                self.app_manager.cleanup()
            
            if self.main_window:
                self.main_window.cleanup()
            
            logger.info("Application shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def main():
    """Main entry point"""
    try:
        # Print startup banner
        print("\n" + "="*70)
        print("🚀 Professional Email Scheduler v4.0")
        print("   Advanced Email Management & Scheduling System")
        print("="*70)
        
        # Create and run application
        app = EmailSchedulerApplication()
        success = app.run()
        
        if not success:
            print("\nApplication failed to start. Check logs for details.")
            input("Press Enter to exit...")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nCritical application error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()