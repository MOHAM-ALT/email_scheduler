# core/file_manager.py
"""
File Manager - Advanced File Operations
Handles file operations, validation, backup, and management
"""

import logging
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import json
import os
import tempfile
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """File information structure"""
    path: Path
    size: int
    modified_time: datetime
    checksum: str
    file_type: str
    is_valid: bool = True
    error_message: str = None

@dataclass
class BackupInfo:
    """Backup information structure"""
    original_path: Path
    backup_path: Path
    created_time: datetime
    checksum: str
    size: int

class FileManager:
    """Advanced file management with validation, backup, and recovery"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
        # Directory structure
        self.base_dir = Path.cwd()
        self.data_dir = self.base_dir / "data"
        self.backup_dir = self.base_dir / "backups"
        self.temp_dir = self.base_dir / "temp"
        self.export_dir = self.base_dir / "exports"
        
        # File tracking
        self.managed_files = {}
        self.backup_registry = {}
        self.file_cache = {}
        
        # Validation settings
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {
            '.xlsx', '.xls', '.csv', '.txt', '.json',
            '.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg'
        }
        
        # Cleanup settings
        self.cleanup_older_than_days = 30
        self.max_backup_files = 50
        
    def initialize(self):
        """Initialize file manager and create directory structure"""
        try:
            logger.info("Initializing file manager")
            
            # Create directory structure
            directories = [
                self.data_dir,
                self.backup_dir,
                self.temp_dir,
                self.export_dir
            ]
            
            for directory in directories:
                directory.mkdir(exist_ok=True, parents=True)
                logger.debug(f"Directory ensured: {directory}")
            
            # Load file registry
            self._load_file_registry()
            
            # Perform initial cleanup
            self._cleanup_old_files()
            
            logger.info("File manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize file manager: {e}")
            return False
    
    def validate_file(self, file_path: str) -> FileInfo:
        """Comprehensive file validation"""
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                return FileInfo(
                    path=path,
                    size=0,
                    modified_time=datetime.now(),
                    checksum="",
                    file_type="unknown",
                    is_valid=False,
                    error_message="File does not exist"
                )
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                return FileInfo(
                    path=path,
                    size=file_size,
                    modified_time=datetime.fromtimestamp(path.stat().st_mtime),
                    checksum="",
                    file_type="oversized",
                    is_valid=False,
                    error_message=f"File size ({file_size} bytes) exceeds maximum allowed ({self.max_file_size} bytes)"
                )
            
            # Check file extension
            file_extension = path.suffix.lower()
            if file_extension not in self.allowed_extensions:
                return FileInfo(
                    path=path,
                    size=file_size,
                    modified_time=datetime.fromtimestamp(path.stat().st_mtime),
                    checksum="",
                    file_type="unsupported",
                    is_valid=False,
                    error_message=f"File type '{file_extension}' is not supported"
                )
            
            # Calculate checksum
            checksum = self._calculate_checksum(path)
            
            # Determine file type
            file_type = self._determine_file_type(path)
            
            # Additional validation based on file type
            validation_result = self._validate_file_content(path, file_type)
            
            file_info = FileInfo(
                path=path,
                size=file_size,
                modified_time=datetime.fromtimestamp(path.stat().st_mtime),
                checksum=checksum,
                file_type=file_type,
                is_valid=validation_result[0],
                error_message=validation_result[1] if not validation_result[0] else None
            )
            
            # Cache file info
            self.file_cache[str(path)] = file_info
            
            logger.debug(f"File validation completed: {path} - Valid: {file_info.is_valid}")
            return file_info
            
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            return FileInfo(
                path=Path(file_path),
                size=0,
                modified_time=datetime.now(),
                checksum="",
                file_type="error",
                is_valid=False,
                error_message=f"Validation error: {e}"
            )
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def _determine_file_type(self, file_path: Path) -> str:
        """Determine detailed file type"""
        extension = file_path.suffix.lower()
        
        type_mapping = {
            '.xlsx': 'excel_modern',
            '.xls': 'excel_legacy',
            '.csv': 'csv',
            '.txt': 'text',
            '.json': 'json',
            '.pdf': 'pdf',
            '.doc': 'word_legacy',
            '.docx': 'word_modern',
            '.png': 'image_png',
            '.jpg': 'image_jpg',
            '.jpeg': 'image_jpeg'
        }
        
        return type_mapping.get(extension, 'unknown')
    
    def _validate_file_content(self, file_path: Path, file_type: str) -> Tuple[bool, Optional[str]]:
        """Validate file content based on type"""
        try:
            if file_type in ['excel_modern', 'excel_legacy']:
                return self._validate_excel_file(file_path)
            elif file_type == 'csv':
                return self._validate_csv_file(file_path)
            elif file_type == 'json':
                return self._validate_json_file(file_path)
            elif file_type == 'text':
                return self._validate_text_file(file_path)
            else:
                return True, None  # No specific validation for other types
                
        except Exception as e:
            return False, f"Content validation error: {e}"
    
    def _validate_excel_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate Excel file content"""
        try:
            import pandas as pd
            
            # Try to read the file
            df = pd.read_excel(file_path, nrows=1)  # Read just first row to test
            
            if df.empty:
                return False, "Excel file is empty"
            
            if len(df.columns) == 0:
                return False, "Excel file has no columns"
            
            return True, None
            
        except ImportError:
            return False, "pandas library not available for Excel validation"
        except Exception as e:
            return False, f"Excel file is corrupted or invalid: {e}"
    
    def _validate_csv_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate CSV file content"""
        try:
            import pandas as pd
            
            # Try different encodings and delimiters
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            delimiters = [',', ';', '\t', '|']
            
            for encoding in encodings:
                for delimiter in delimiters:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter, nrows=1)
                        if not df.empty and len(df.columns) > 0:
                            return True, None
                    except Exception:
                        continue
            
            return False, "CSV file format not recognized or corrupted"
            
        except ImportError:
            return False, "pandas library not available for CSV validation"
        except Exception as e:
            return False, f"CSV validation error: {e}"
    
    def _validate_json_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate JSON file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            return False, f"JSON validation error: {e}"
    
    def _validate_text_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate text file content"""
        try:
            # Try to read with different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read(1024)  # Read first 1KB
                    if content:
                        return True, None
                except UnicodeDecodeError:
                    continue
            
            return False, "Text file encoding not supported"
            
        except Exception as e:
            return False, f"Text file validation error: {e}"
    
    def create_backup(self, file_path: str, backup_name: str = None) -> Optional[BackupInfo]:
        """Create backup of a file"""
        try:
            source_path = Path(file_path)
            
            if not source_path.exists():
                logger.error(f"Cannot backup non-existent file: {file_path}")
                return None
            
            # Generate backup name if not provided
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            
            backup_path = self.backup_dir / backup_name
            
            # Create backup
            shutil.copy2(source_path, backup_path)
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)
            
            # Create backup info
            backup_info = BackupInfo(
                original_path=source_path,
                backup_path=backup_path,
                created_time=datetime.now(),
                checksum=checksum,
                size=backup_path.stat().st_size
            )
            
            # Register backup
            self.backup_registry[str(source_path)] = backup_info
            
            # Save registry
            self._save_backup_registry()
            
            logger.info(f"Backup created: {source_path} -> {backup_path}")
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return None
    
    def restore_from_backup(self, original_path: str, backup_time: datetime = None) -> bool:
        """Restore file from backup"""
        try:
            source_path = Path(original_path)
            
            if str(source_path) not in self.backup_registry:
                logger.error(f"No backup found for: {original_path}")
                return False
            
            backup_info = self.backup_registry[str(source_path)]
            
            if not backup_info.backup_path.exists():
                logger.error(f"Backup file not found: {backup_info.backup_path}")
                return False
            
            # Verify backup integrity
            current_checksum = self._calculate_checksum(backup_info.backup_path)
            if current_checksum != backup_info.checksum:
                logger.error(f"Backup file corrupted: {backup_info.backup_path}")
                return False
            
            # Create backup of current file if it exists
            if source_path.exists():
                current_backup_name = f"{source_path.stem}_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}{source_path.suffix}"
                current_backup = self.backup_dir / current_backup_name
                shutil.copy2(source_path, current_backup)
                logger.info(f"Current file backed up to: {current_backup}")
            
            # Restore from backup
            shutil.copy2(backup_info.backup_path, source_path)
            
            logger.info(f"File restored from backup: {original_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return False
    
    def copy_file(self, source: str, destination: str, create_backup: bool = True) -> bool:
        """Copy file with optional backup"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                logger.error(f"Source file does not exist: {source}")
                return False
            
            # Create backup of destination if it exists and backup is requested
            if create_backup and dest_path.exists():
                self.create_backup(str(dest_path))
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, dest_path)
            
            logger.info(f"File copied: {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying file: {e}")
            return False
    
    def move_file(self, source: str, destination: str, create_backup: bool = True) -> bool:
        """Move file with optional backup"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                logger.error(f"Source file does not exist: {source}")
                return False
            
            # Create backup of destination if it exists and backup is requested
            if create_backup and dest_path.exists():
                self.create_backup(str(dest_path))
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source_path), str(dest_path))
            
            logger.info(f"File moved: {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving file: {e}")
            return False
    
    def delete_file(self, file_path: str, create_backup: bool = True) -> bool:
        """Delete file with optional backup"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return True  # Already deleted
            
            # Create backup before deletion if requested
            if create_backup:
                backup_info = self.create_backup(file_path)
                if backup_info:
                    logger.info(f"Backup created before deletion: {backup_info.backup_path}")
            
            # Delete file
            path.unlink()
            
            logger.info(f"File deleted: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def create_temp_file(self, content: str = "", suffix: str = ".tmp") -> Optional[Path]:
        """Create temporary file"""
        try:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix=suffix,
                dir=self.temp_dir,
                delete=False
            )
            
            if content:
                temp_file.write(content)
            
            temp_file.close()
            temp_path = Path(temp_file.name)
            
            logger.debug(f"Temporary file created: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error creating temporary file: {e}")
            return None
    
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """Clean up old temporary files"""
        try:
            cleanup_time = datetime.now() - timedelta(hours=older_than_hours)
            cleaned_count = 0
            
            for temp_file in self.temp_dir.glob("*"):
                if temp_file.is_file():
                    file_time = datetime.fromtimestamp(temp_file.stat().st_mtime)
                    if file_time < cleanup_time:
                        try:
                            temp_file.unlink()
                            cleaned_count += 1
                            logger.debug(f"Cleaned temp file: {temp_file}")
                        except Exception as e:
                            logger.warning(f"Failed to clean temp file {temp_file}: {e}")
            
            logger.info(f"Cleaned {cleaned_count} temporary files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning temporary files: {e}")
            return 0
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage statistics"""
        try:
            # Get usage for managed directories
            usage_stats = {}
            
            directories = {
                'data': self.data_dir,
                'backups': self.backup_dir,
                'temp': self.temp_dir,
                'exports': self.export_dir
            }
            
            for name, directory in directories.items():
                if directory.exists():
                    total_size = sum(
                        f.stat().st_size for f in directory.rglob('*') if f.is_file()
                    )
                    file_count = len([f for f in directory.rglob('*') if f.is_file()])
                    
                    usage_stats[name] = {
                        'path': str(directory),
                        'size_bytes': total_size,
                        'size_mb': round(total_size / (1024 * 1024), 2),
                        'file_count': file_count
                    }
                else:
                    usage_stats[name] = {
                        'path': str(directory),
                        'size_bytes': 0,
                        'size_mb': 0,
                        'file_count': 0
                    }
            
            # Get total disk usage
            try:
                disk_usage = shutil.disk_usage(self.base_dir)
                usage_stats['disk'] = {
                    'total_bytes': disk_usage.total,
                    'used_bytes': disk_usage.used,
                    'free_bytes': disk_usage.free,
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'used_gb': round(disk_usage.used / (1024**3), 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2),
                    'usage_percentage': round((disk_usage.used / disk_usage.total) * 100, 1)
                }
            except Exception as e:
                logger.warning(f"Could not get disk usage: {e}")
                usage_stats['disk'] = {'error': str(e)}
            
            return usage_stats
            
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {'error': str(e)}
    
    def _cleanup_old_files(self):
        """Clean up old files and backups"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.cleanup_older_than_days)
            
            # Clean up old temporary files
            self.cleanup_temp_files(24)
            
            # Clean up old backups
            backup_files = list(self.backup_dir.glob("*"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the most recent backups
            if len(backup_files) > self.max_backup_files:
                for old_backup in backup_files[self.max_backup_files:]:
                    try:
                        old_backup.unlink()
                        logger.debug(f"Cleaned old backup: {old_backup}")
                    except Exception as e:
                        logger.warning(f"Failed to clean backup {old_backup}: {e}")
            
            logger.info("File cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")
    
    def _load_file_registry(self):
        """Load file registry from disk"""
        try:
            registry_file = self.data_dir / "file_registry.json"
            
            if registry_file.exists():
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry_data = json.load(f)
                
                self.managed_files = registry_data.get('managed_files', {})
                
                # Load backup registry
                backup_data = registry_data.get('backup_registry', {})
                for original_path, backup_data in backup_data.items():
                    self.backup_registry[original_path] = BackupInfo(
                        original_path=Path(backup_data['original_path']),
                        backup_path=Path(backup_data['backup_path']),
                        created_time=datetime.fromisoformat(backup_data['created_time']),
                        checksum=backup_data['checksum'],
                        size=backup_data['size']
                    )
                
                logger.info("File registry loaded")
        except Exception as e:
            logger.warning(f"Failed to load file registry: {e}")
    
    def _save_backup_registry(self):
        """Save backup registry to disk"""
        try:
            registry_file = self.data_dir / "file_registry.json"
            
            # Convert backup registry to serializable format
            backup_data = {}
            for original_path, backup_info in self.backup_registry.items():
                backup_data[original_path] = {
                    'original_path': str(backup_info.original_path),
                    'backup_path': str(backup_info.backup_path),
                    'created_time': backup_info.created_time.isoformat(),
                    'checksum': backup_info.checksum,
                    'size': backup_info.size
                }
            
            registry_data = {
                'managed_files': self.managed_files,
                'backup_registry': backup_data,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("File registry saved")
            
        except Exception as e:
            logger.warning(f"Failed to save file registry: {e}")
    
    def get_file_statistics(self) -> Dict[str, Any]:
        """Get comprehensive file management statistics"""
        return {
            'managed_files_count': len(self.managed_files),
            'backup_count': len(self.backup_registry),
            'cache_size': len(self.file_cache),
            'disk_usage': self.get_disk_usage(),
            'directory_structure': {
                'data_dir': str(self.data_dir),
                'backup_dir': str(self.backup_dir),
                'temp_dir': str(self.temp_dir),
                'export_dir': str(self.export_dir)
            },
            'settings': {
                'max_file_size_mb': self.max_file_size / (1024 * 1024),
                'allowed_extensions': list(self.allowed_extensions),
                'cleanup_older_than_days': self.cleanup_older_than_days,
                'max_backup_files': self.max_backup_files
            }
        }
    
    def clear_cache(self):
        """Clear file cache"""
        try:
            self.file_cache.clear()
            logger.info("File cache cleared")
        except Exception as e:
            logger.error(f"Error clearing file cache: {e}")
    
    def health_check(self) -> bool:
        """Perform health check on file manager"""
        try:
            # Check if directories exist and are writable
            test_dirs = [self.data_dir, self.backup_dir, self.temp_dir, self.export_dir]
            
            for directory in test_dirs:
                if not directory.exists():
                    return False
                
                # Test write access
                test_file = directory / "health_check.tmp"
                try:
                    test_file.write_text("health check")
                    test_file.unlink()
                except Exception:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"File manager health check failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup file manager resources"""
        try:
            # Save registry
            self._save_backup_registry()
            
            # Clean up temporary files
            self.cleanup_temp_files()
            
            # Clear caches
            self.clear_cache()
            
            logger.info("File manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during file manager cleanup: {e}")