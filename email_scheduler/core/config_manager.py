# core/config_manager.py
"""
Configuration Manager
Advanced configuration management with validation, encryption, and profiles
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import os
import hashlib
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

@dataclass
class EmailSettings:
    """Email configuration settings"""
    default_subject: str = "Important Email with Attachments"
    default_body: str = """Dear Recipient,

I hope this email finds you well. Please find the attached important documents for your review.

If you have any questions, please don't hesitate to contact us.

Best regards,
[Your Name]"""
    signature: str = ""
    max_attachments: int = 2
    max_attachment_size_mb: int = 25

@dataclass
class ScheduleSettings:
    """Schedule configuration settings"""
    emails_per_day: int = 499
    emails_per_batch: int = 10
    start_time: str = "06:00"
    working_days_only: bool = True
    retry_failed_emails: bool = True
    retry_attempts: int = 3
    retry_delay_minutes: int = 30
    batch_delay_minutes: int = 2

@dataclass
class OutlookSettings:
    """Outlook integration settings"""
    connection_timeout: int = 30
    retry_connection: bool = True
    auto_reconnect: bool = True
    use_bcc: bool = True
    security_prompts: bool = True
    backup_drafts: bool = True

@dataclass
class ValidationSettings:
    """Email validation settings"""
    strict_validation: bool = True
    allow_international_domains: bool = True
    check_mx_records: bool = False
    max_email_length: int = 254
    blacklist_domains: List[str] = None
    whitelist_domains: List[str] = None

@dataclass
class SecuritySettings:
    """Security and privacy settings"""
    encrypt_sensitive_data: bool = True
    log_email_addresses: bool = False
    auto_cleanup_logs: bool = True
    log_retention_days: int = 30
    backup_schedules: bool = True

@dataclass
class PerformanceSettings:
    """Performance optimization settings"""
    max_concurrent_operations: int = 5
    memory_optimization: bool = True
    auto_cleanup_cache: bool = True
    cache_size_mb: int = 100
    progress_update_interval: int = 1

class ConfigManager:
    """Advanced configuration manager with encryption and validation"""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "app_config.json"
        self.encrypted_config_file = self.config_dir / "secure_config.enc"
        self.profiles_dir = self.config_dir / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)
        
        # Configuration sections
        self.email_settings = EmailSettings()
        self.schedule_settings = ScheduleSettings()
        self.outlook_settings = OutlookSettings()
        self.validation_settings = ValidationSettings()
        self.security_settings = SecuritySettings()
        self.performance_settings = PerformanceSettings()
        
        # Runtime settings
        self.current_profile = "default"
        self.config_version = "4.0"
        self.last_modified = None
        
        # Encryption key management
        self.encryption_key = None
        self._setup_encryption()
    
    def _setup_encryption(self):
        """Setup encryption for sensitive configuration data"""
        try:
            key_file = self.config_dir / "config.key"
            
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
            else:
                # Generate new encryption key
                self.encryption_key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(self.encryption_key)
                # Make key file read-only
                os.chmod(key_file, 0o600)
                
            logger.info("Configuration encryption setup completed")
            
        except Exception as e:
            logger.warning(f"Failed to setup encryption: {e}")
            self.encryption_key = None
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not self.encryption_key:
            return data
        
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return data
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not self.encryption_key:
            return encrypted_data
        
        try:
            fernet = Fernet(self.encryption_key)
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_data
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            # Try to load from main config file first
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                self._apply_config_data(config_data)
                logger.info("Configuration loaded successfully")
                return True
            
            # If no config file exists, create default
            else:
                logger.info("No configuration file found, using defaults")
                self.save_config()
                return True
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Use defaults on error
            self._reset_to_defaults()
            return False
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            config_data = self._serialize_config()
            
            # Save to main config file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Create backup
            backup_file = self.config_dir / f"app_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Cleanup old backups (keep last 10)
            self._cleanup_old_backups()
            
            self.last_modified = datetime.now().isoformat()
            logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data to settings objects"""
        try:
            # Apply email settings
            if 'email_settings' in config_data:
                email_data = config_data['email_settings']
                self.email_settings = EmailSettings(**email_data)
            
            # Apply schedule settings
            if 'schedule_settings' in config_data:
                schedule_data = config_data['schedule_settings']
                self.schedule_settings = ScheduleSettings(**schedule_data)
            
            # Apply Outlook settings
            if 'outlook_settings' in config_data:
                outlook_data = config_data['outlook_settings']
                self.outlook_settings = OutlookSettings(**outlook_data)
            
            # Apply validation settings
            if 'validation_settings' in config_data:
                validation_data = config_data['validation_settings']
                # Handle None values for lists
                if validation_data.get('blacklist_domains') is None:
                    validation_data['blacklist_domains'] = []
                if validation_data.get('whitelist_domains') is None:
                    validation_data['whitelist_domains'] = []
                self.validation_settings = ValidationSettings(**validation_data)
            
            # Apply security settings
            if 'security_settings' in config_data:
                security_data = config_data['security_settings']
                self.security_settings = SecuritySettings(**security_data)
            
            # Apply performance settings
            if 'performance_settings' in config_data:
                performance_data = config_data['performance_settings']
                self.performance_settings = PerformanceSettings(**performance_data)
            
            # Apply runtime settings
            if 'runtime' in config_data:
                runtime_data = config_data['runtime']
                self.current_profile = runtime_data.get('current_profile', 'default')
                self.last_modified = runtime_data.get('last_modified')
            
        except Exception as e:
            logger.error(f"Error applying configuration data: {e}")
            raise
    
    def _serialize_config(self) -> Dict[str, Any]:
        """Serialize current configuration to dictionary"""
        config_data = {
            'version': self.config_version,
            'email_settings': asdict(self.email_settings),
            'schedule_settings': asdict(self.schedule_settings),
            'outlook_settings': asdict(self.outlook_settings),
            'validation_settings': asdict(self.validation_settings),
            'security_settings': asdict(self.security_settings),
            'performance_settings': asdict(self.performance_settings),
            'runtime': {
                'current_profile': self.current_profile,
                'last_modified': datetime.now().isoformat(),
                'created_date': getattr(self, 'created_date', datetime.now().isoformat())
            }
        }
        
        return config_data
    
    def _reset_to_defaults(self):
        """Reset all settings to default values"""
        self.email_settings = EmailSettings()
        self.schedule_settings = ScheduleSettings()
        self.outlook_settings = OutlookSettings()
        self.validation_settings = ValidationSettings(
            blacklist_domains=[],
            whitelist_domains=[]
        )
        self.security_settings = SecuritySettings()
        self.performance_settings = PerformanceSettings()
        
        logger.info("Configuration reset to defaults")
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Cleanup old backup files"""
        try:
            backup_pattern = "app_config_backup_*.json"
            backup_files = list(self.config_dir.glob(backup_pattern))
            
            if len(backup_files) > keep_count:
                # Sort by modification time, oldest first
                backup_files.sort(key=lambda x: x.stat().st_mtime)
                
                # Remove oldest files
                for old_file in backup_files[:-keep_count]:
                    old_file.unlink()
                    
                logger.info(f"Cleaned up {len(backup_files) - keep_count} old backup files")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
    
    def validate_config(self) -> Dict[str, List[str]]:
        """Validate current configuration and return any issues"""
        issues = {
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Validate email settings
        if not self.email_settings.default_subject.strip():
            issues['errors'].append("Default email subject cannot be empty")
        
        if self.email_settings.max_attachments < 0 or self.email_settings.max_attachments > 10:
            issues['warnings'].append("Max attachments should be between 0 and 10")
        
        if self.email_settings.max_attachment_size_mb < 1 or self.email_settings.max_attachment_size_mb > 100:
            issues['warnings'].append("Max attachment size should be between 1MB and 100MB")
        
        # Validate schedule settings
        if self.schedule_settings.emails_per_day < 1 or self.schedule_settings.emails_per_day > 1000:
            issues['errors'].append("Emails per day must be between 1 and 1000")
        
        if self.schedule_settings.emails_per_batch < 1 or self.schedule_settings.emails_per_batch > 100:
            issues['errors'].append("Emails per batch must be between 1 and 100")
        
        if self.schedule_settings.emails_per_batch > self.schedule_settings.emails_per_day:
            issues['errors'].append("Emails per batch cannot exceed emails per day")
        
        # Validate time format
        try:
            time_parts = self.schedule_settings.start_time.split(':')
            if len(time_parts) != 2:
                raise ValueError("Invalid format")
            hour, minute = int(time_parts[0]), int(time_parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time range")
        except ValueError:
            issues['errors'].append("Start time must be in HH:MM format (00:00 to 23:59)")
        
        # Validate validation settings
        if self.validation_settings.max_email_length < 10 or self.validation_settings.max_email_length > 500:
            issues['warnings'].append("Max email length should be between 10 and 500 characters")
        
        # Performance recommendations
        if self.performance_settings.max_concurrent_operations > 10:
            issues['suggestions'].append("High concurrent operations may impact system performance")
        
        if self.performance_settings.cache_size_mb > 500:
            issues['suggestions'].append("Large cache size may consume significant memory")
        
        return issues
    
    def create_profile(self, profile_name: str) -> bool:
        """Create a new configuration profile"""
        try:
            if not profile_name or not profile_name.strip():
                logger.error("Profile name cannot be empty")
                return False
            
            profile_file = self.profiles_dir / f"{profile_name}.json"
            
            if profile_file.exists():
                logger.warning(f"Profile already exists: {profile_name}")
                return False
            
            # Save current configuration as new profile
            config_data = self._serialize_config()
            config_data['profile_name'] = profile_name
            config_data['created_date'] = datetime.now().isoformat()
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created new profile: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create profile {profile_name}: {e}")
            return False
    
    def load_profile(self, profile_name: str) -> bool:
        """Load configuration from a specific profile"""
        try:
            profile_file = self.profiles_dir / f"{profile_name}.json"
            
            if not profile_file.exists():
                logger.error(f"Profile not found: {profile_name}")
                return False
            
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            self._apply_config_data(profile_data)
            self.current_profile = profile_name
            
            logger.info(f"Loaded profile: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load profile {profile_name}: {e}")
            return False
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """List all available configuration profiles"""
        profiles = []
        
        try:
            for profile_file in self.profiles_dir.glob("*.json"):
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                    
                    profiles.append({
                        'name': profile_file.stem,
                        'display_name': profile_data.get('profile_name', profile_file.stem),
                        'created_date': profile_data.get('created_date', 'Unknown'),
                        'last_modified': profile_data.get('runtime', {}).get('last_modified', 'Unknown'),
                        'version': profile_data.get('version', 'Unknown')
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to read profile {profile_file}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to list profiles: {e}")
        
        return sorted(profiles, key=lambda x: x['name'])
    
    def delete_profile(self, profile_name: str) -> bool:
        """Delete a configuration profile"""
        try:
            if profile_name == 'default':
                logger.error("Cannot delete default profile")
                return False
            
            profile_file = self.profiles_dir / f"{profile_name}.json"
            
            if not profile_file.exists():
                logger.error(f"Profile not found: {profile_name}")
                return False
            
            profile_file.unlink()
            
            # If current profile was deleted, switch to default
            if self.current_profile == profile_name:
                self.current_profile = 'default'
            
            logger.info(f"Deleted profile: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete profile {profile_name}: {e}")
            return False
    
    def export_config(self, filepath: str, include_sensitive: bool = False) -> bool:
        """Export configuration to external file"""
        try:
            config_data = self._serialize_config()
            
            # Remove sensitive data if requested
            if not include_sensitive:
                # Remove any potentially sensitive fields
                sensitive_fields = ['encryption_key', 'passwords', 'tokens']
                for field in sensitive_fields:
                    config_data.pop(field, None)
            
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'version': self.config_version,
                    'source_profile': self.current_profile,
                    'includes_sensitive': include_sensitive
                },
                'configuration': config_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exported to: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, filepath: str) -> bool:
        """Import configuration from external file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import data structure
            if 'configuration' not in import_data:
                logger.error("Invalid configuration file format")
                return False
            
            config_data = import_data['configuration']
            
            # Create backup of current config
            backup_name = f"pre_import_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_profile(backup_name)
            
            # Apply imported configuration
            self._apply_config_data(config_data)
            
            # Validate imported configuration
            validation_result = self.validate_config()
            if validation_result['errors']:
                logger.warning(f"Imported configuration has errors: {validation_result['errors']}")
            
            # Save the imported configuration
            self.save_config()
            
            logger.info(f"Configuration imported from: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'profile': self.current_profile,
            'version': self.config_version,
            'last_modified': self.last_modified,
            'settings_summary': {
                'emails_per_day': self.schedule_settings.emails_per_day,
                'emails_per_batch': self.schedule_settings.emails_per_batch,
                'start_time': self.schedule_settings.start_time,
                'working_days_only': self.schedule_settings.working_days_only,
                'strict_validation': self.validation_settings.strict_validation,
                'use_encryption': self.security_settings.encrypt_sensitive_data,
                'auto_backup': self.security_settings.backup_schedules
            },
            'validation_status': self.validate_config()
        }
    
    def reset_to_factory_defaults(self) -> bool:
        """Reset configuration to factory defaults"""
        try:
            # Create backup before reset
            backup_name = f"factory_reset_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_profile(backup_name)
            
            # Reset to defaults
            self._reset_to_defaults()
            
            # Save default configuration
            self.save_config()
            
            logger.info("Configuration reset to factory defaults")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset to factory defaults: {e}")
            return False
    
    def health_check(self) -> bool:
        """Perform health check on configuration system"""
        try:
            # Check if config directory is accessible
            if not self.config_dir.exists():
                return False
            
            # Check if we can write to config directory
            test_file = self.config_dir / "health_check.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            # Validate current configuration
            validation_result = self.validate_config()
            if validation_result['errors']:
                return False
            
            # Check encryption system
            if self.security_settings.encrypt_sensitive_data and not self.encryption_key:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration health check failed: {e}")
            return False
    
    # Convenience methods for getting specific settings
    def get_email_settings(self) -> EmailSettings:
        """Get email settings"""
        return self.email_settings
    
    def get_schedule_settings(self) -> ScheduleSettings:
        """Get schedule settings"""
        return self.schedule_settings
    
    def get_outlook_settings(self) -> OutlookSettings:
        """Get Outlook settings"""
        return self.outlook_settings
    
    def get_validation_settings(self) -> ValidationSettings:
        """Get validation settings"""
        return self.validation_settings
    
    def get_security_settings(self) -> SecuritySettings:
        """Get security settings"""
        return self.security_settings
    
    def get_performance_settings(self) -> PerformanceSettings:
        """Get performance settings"""
        return self.performance_settings