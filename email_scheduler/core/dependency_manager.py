# core/dependency_manager.py
"""
Advanced Dependency Manager
Handles package installation, validation, and auto-recovery
"""

import sys
import subprocess
import importlib
import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)

@dataclass
class DependencyResult:
    """Result of dependency operations"""
    success: bool
    message: str
    installed_packages: List[str] = None
    failed_packages: List[str] = None
    warnings: List[str] = None
    critical_failures: List[str] = None

@dataclass
class PackageInfo:
    """Package information and requirements"""
    name: str
    version: str
    import_name: str = None
    critical: bool = True
    install_alternatives: List[str] = None
    post_install_check: callable = None

class DependencyManager:
    """Advanced dependency management with auto-recovery capabilities"""
    
    def __init__(self):
        self.required_packages = self._define_required_packages()
        self.installation_cache = {}
        self.failed_packages = set()
        
        # Create cache directory
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Load installation cache
        self._load_installation_cache()
    
    def _define_required_packages(self) -> Dict[str, PackageInfo]:
        """Define all required packages with detailed information"""
        return {
            'pandas': PackageInfo(
                name='pandas',
                version='>=2.0.0',
                import_name='pandas',
                critical=True,
                install_alternatives=['pandas==2.0.3', 'pandas>=1.5.0']
            ),
            'openpyxl': PackageInfo(
                name='openpyxl',
                version='>=3.1.0',
                import_name='openpyxl',
                critical=True,
                install_alternatives=['openpyxl==3.1.2', 'openpyxl>=3.0.0']
            ),
            'schedule': PackageInfo(
                name='schedule',
                version='>=1.2.0',
                import_name='schedule',
                critical=True,
                install_alternatives=['schedule==1.2.0', 'schedule>=1.1.0']
            ),
            'email_validator': PackageInfo(
                name='email-validator',
                version='>=2.0.0',
                import_name='email_validator',
                critical=True,
                install_alternatives=['email-validator==2.0.0', 'email-validator>=1.3.0']
            ),
            'pywin32': PackageInfo(
                name='pywin32',
                version='>=306',
                import_name='win32com.client',
                critical=False,  # Not critical for basic functionality
                install_alternatives=['pywin32==306', 'pywin32>=305'],
                post_install_check=self._check_pywin32
            ),
            'pillow': PackageInfo(
                name='Pillow',
                version='>=10.0.0',
                import_name='PIL',
                critical=False,
                install_alternatives=['Pillow==10.0.0', 'Pillow>=9.0.0']
            ),
            'cryptography': PackageInfo(
                name='cryptography',
                version='>=3.0.0',
                import_name='cryptography',
                critical=False,
                install_alternatives=['cryptography>=3.0.0']
            )
        }
    
    def _check_pywin32(self) -> bool:
        """Special check for pywin32 installation"""
        try:
            import win32com.client
            # Try to create a COM object to verify it's working
            win32com.client.Dispatch("Excel.Application")
            return True
        except Exception as e:
            logger.warning(f"pywin32 check failed: {e}")
            return False
    
    def _load_installation_cache(self):
        """Load installation cache from file"""
        cache_file = self.cache_dir / "installation_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.installation_cache = json.load(f)
                logger.info("Installation cache loaded")
            except Exception as e:
                logger.warning(f"Failed to load installation cache: {e}")
                self.installation_cache = {}
    
    def _save_installation_cache(self):
        """Save installation cache to file"""
        cache_file = self.cache_dir / "installation_cache.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.installation_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save installation cache: {e}")
    
    def check_package_installed(self, package_info: PackageInfo) -> Tuple[bool, str]:
        """Check if a package is properly installed"""
        try:
            # Check cache first
            cache_key = f"{package_info.name}_{package_info.version}"
            if cache_key in self.installation_cache:
                cached_result = self.installation_cache[cache_key]
                if cached_result.get('installed', False):
                    # Verify it's still working
                    module = importlib.import_module(package_info.import_name or package_info.name)
                    return True, cached_result.get('version', 'unknown')
            
            # Try to import the package
            module = importlib.import_module(package_info.import_name or package_info.name)
            
            # Get version if available
            version = 'unknown'
            for attr in ['__version__', 'version', 'VERSION']:
                if hasattr(module, attr):
                    version = getattr(module, attr)
                    break
            
            # Run post-install check if defined
            if package_info.post_install_check:
                if not package_info.post_install_check():
                    return False, f"Post-install check failed for {package_info.name}"
            
            # Update cache
            self.installation_cache[cache_key] = {
                'installed': True,
                'version': version,
                'check_time': time.time()
            }
            
            return True, version
            
        except ImportError as e:
            return False, f"Import failed: {e}"
        except Exception as e:
            return False, f"Check failed: {e}"
    
    def install_package(self, package_info: PackageInfo) -> bool:
        """Install a package with multiple fallback strategies"""
        if package_info.name in self.failed_packages:
            logger.warning(f"Skipping {package_info.name} - previously failed")
            return False
        
        logger.info(f"Installing package: {package_info.name}")
        
        # Try different installation methods
        install_commands = self._get_install_commands(package_info)
        
        for i, cmd in enumerate(install_commands, 1):
            try:
                logger.info(f"Installation attempt {i}/{len(install_commands)}: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minutes timeout
                    check=False
                )
                
                if result.returncode == 0:
                    logger.info(f"Successfully installed {package_info.name}")
                    
                    # Verify installation
                    time.sleep(2)  # Give it a moment
                    installed, version = self.check_package_installed(package_info)
                    
                    if installed:
                        logger.info(f"Installation verified for {package_info.name} (version: {version})")
                        self._save_installation_cache()
                        return True
                    else:
                        logger.warning(f"Installation completed but verification failed for {package_info.name}")
                
                else:
                    logger.warning(f"Installation attempt {i} failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Installation timeout for {package_info.name}")
            except Exception as e:
                logger.error(f"Installation error for {package_info.name}: {e}")
        
        # All installation attempts failed
        logger.error(f"All installation attempts failed for {package_info.name}")
        self.failed_packages.add(package_info.name)
        return False
    
    def _get_install_commands(self, package_info: PackageInfo) -> List[List[str]]:
        """Get list of installation commands to try"""
        commands = []
        python_exe = sys.executable
        
        # Primary installation options
        if package_info.install_alternatives:
            for alt in package_info.install_alternatives:
                commands.append([python_exe, "-m", "pip", "install", alt])
                commands.append([python_exe, "-m", "pip", "install", "--user", alt])
        
        # Standard installation
        package_spec = f"{package_info.name}{package_info.version}"
        commands.extend([
            [python_exe, "-m", "pip", "install", package_spec],
            [python_exe, "-m", "pip", "install", "--user", package_spec],
            [python_exe, "-m", "pip", "install", "--force-reinstall", package_spec],
            [python_exe, "-m", "pip", "install", "--no-deps", package_info.name],
            [python_exe, "-m", "pip", "install", "--upgrade", package_info.name]
        ])
        
        return commands
    
    def ensure_all_dependencies(self) -> DependencyResult:
        """Ensure all required dependencies are installed"""
        logger.info("Starting dependency check and installation")
        
        installed_packages = []
        failed_packages = []
        warnings = []
        critical_failures = []
        
        for name, package_info in self.required_packages.items():
            try:
                installed, version = self.check_package_installed(package_info)
                
                if installed:
                    logger.info(f"✓ {name}: installed (version: {version})")
                    installed_packages.append(f"{name} ({version})")
                else:
                    logger.warning(f"✗ {name}: not installed - {version}")
                    
                    # Attempt installation
                    if self.install_package(package_info):
                        installed_packages.append(f"{name} (newly installed)")
                    else:
                        failed_packages.append(name)
                        
                        if package_info.critical:
                            critical_failures.append(name)
                            logger.error(f"Critical package failed: {name}")
                        else:
                            warnings.append(f"Non-critical package failed: {name}")
                            logger.warning(f"Non-critical package failed: {name}")
                
            except Exception as e:
                logger.error(f"Error processing package {name}: {e}")
                failed_packages.append(name)
                if package_info.critical:
                    critical_failures.append(name)
        
        # Determine overall result
        success = len(critical_failures) == 0
        
        result_message = f"Dependency check completed. "
        if success:
            result_message += f"All critical dependencies satisfied. "
        else:
            result_message += f"{len(critical_failures)} critical dependencies failed. "
        
        result_message += f"Installed: {len(installed_packages)}, Failed: {len(failed_packages)}"
        
        logger.info(result_message)
        
        return DependencyResult(
            success=success,
            message=result_message,
            installed_packages=installed_packages,
            failed_packages=failed_packages,
            warnings=warnings,
            critical_failures=critical_failures
        )
    
    def repair_installation(self, package_name: str) -> bool:
        """Attempt to repair a failed package installation"""
        if package_name not in self.required_packages:
            logger.error(f"Unknown package for repair: {package_name}")
            return False
        
        logger.info(f"Attempting to repair package: {package_name}")
        
        # Remove from failed packages to allow retry
        self.failed_packages.discard(package_name)
        
        # Clear cache entry
        package_info = self.required_packages[package_name]
        cache_key = f"{package_info.name}_{package_info.version}"
        self.installation_cache.pop(cache_key, None)
        
        # Try to uninstall first
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "uninstall", "-y", package_info.name
            ], capture_output=True, timeout=60)
        except Exception:
            pass  # Ignore uninstall errors
        
        # Attempt reinstallation
        return self.install_package(package_info)
    
    def get_package_status(self) -> Dict[str, Dict]:
        """Get detailed status of all packages"""
        status = {}
        
        for name, package_info in self.required_packages.items():
            installed, version_info = self.check_package_installed(package_info)
            
            status[name] = {
                'installed': installed,
                'version': version_info if installed else None,
                'critical': package_info.critical,
                'required_version': package_info.version,
                'status': 'ok' if installed else 'missing'
            }
            
            if name in self.failed_packages:
                status[name]['status'] = 'failed'
        
        return status
    
    def health_check(self) -> bool:
        """Perform health check on dependency system"""
        try:
            # Check if critical packages are working
            critical_packages = [
                name for name, info in self.required_packages.items() 
                if info.critical
            ]
            
            working_count = 0
            for package_name in critical_packages:
                package_info = self.required_packages[package_name]
                installed, _ = self.check_package_installed(package_info)
                if installed:
                    working_count += 1
            
            # Consider healthy if at least 80% of critical packages work
            health_threshold = len(critical_packages) * 0.8
            return working_count >= health_threshold
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def generate_requirements_file(self, filename: str = "requirements.txt"):
        """Generate requirements.txt file"""
        try:
            requirements_path = Path(filename)
            
            with open(requirements_path, 'w') as f:
                f.write("# Professional Email Scheduler Requirements\n")
                f.write("# Auto-generated requirements file\n\n")
                
                for name, package_info in self.required_packages.items():
                    comment = " # Critical" if package_info.critical else " # Optional"
                    f.write(f"{package_info.name}{package_info.version}{comment}\n")
            
            logger.info(f"Requirements file generated: {requirements_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate requirements file: {e}")
            return False
    
    def install_from_requirements(self, requirements_file: str = "requirements.txt") -> bool:
        """Install packages from requirements file"""
        try:
            requirements_path = Path(requirements_file)
            if not requirements_path.exists():
                logger.error(f"Requirements file not found: {requirements_file}")
                return False
            
            logger.info(f"Installing from requirements file: {requirements_file}")
            
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info("Requirements installation completed successfully")
                return True
            else:
                logger.error(f"Requirements installation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing from requirements: {e}")
            return False
    
    def cleanup(self):
        """Cleanup dependency manager resources"""
        try:
            self._save_installation_cache()
            logger.info("Dependency manager cleanup completed")
        except Exception as e:
            logger.error(f"Error during dependency manager cleanup: {e}")