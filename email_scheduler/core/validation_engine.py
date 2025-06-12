# core/validation_engine.py
"""
Validation Engine - Advanced Email Validation
Comprehensive email validation with multiple validation methods
"""

import logging
import re
import threading
import time
import socket
import dns.resolver
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Email validation result"""
    email: str
    is_valid: bool
    score: float  # 0.0 to 1.0
    validation_method: str
    checks_passed: List[str]
    checks_failed: List[str]
    details: Dict[str, Any]
    validated_time: datetime

@dataclass
class DomainInfo:
    """Domain information"""
    domain: str
    has_mx_record: bool
    mx_records: List[str]
    is_disposable: bool
    is_role_based: bool
    reputation_score: float
    last_checked: datetime

class ValidationEngine:
    """Advanced email validation engine with comprehensive checks"""
    
    def __init__(self):
        # Validation patterns
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        # Domain cache
        self.domain_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Validation settings
        self.enable_mx_check = False
        self.enable_role_check = True
        self.enable_disposable_check = True
        self.strict_mode = True
        
        # Thread management
        self.validation_lock = threading.Lock()
        
        # Known lists
        self.disposable_domains = set()
        self.role_based_addresses = {
            'admin', 'administrator', 'postmaster', 'hostmaster', 'webmaster',
            'www', 'ftp', 'mail', 'email', 'marketing', 'sales', 'support',
            'help', 'info', 'contact', 'service', 'noreply', 'no-reply',
            'donotreply', 'do-not-reply', 'bounce', 'bounces', 'billing',
            'accounts', 'accounting', 'finance', 'hr', 'legal', 'compliance'
        }
        
        # Statistics
        self.validation_stats = {
            'total_validations': 0,
            'valid_emails': 0,
            'invalid_emails': 0,
            'mx_checks_performed': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Load data
        self._load_disposable_domains()
        
    def initialize(self):
        """Initialize validation engine"""
        try:
            logger.info("Initializing validation engine")
            
            # Create cache directory
            cache_dir = Path("cache")
            cache_dir.mkdir(exist_ok=True)
            
            # Load cached domain information
            self._load_domain_cache()
            
            # Update disposable domains list
            self._update_disposable_domains()
            
            logger.info("Validation engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize validation engine: {e}")
            return False
    
    def validate_email(self, email: str) -> ValidationResult:
        """Comprehensive email validation"""
        start_time = datetime.now()
        
        try:
            with self.validation_lock:
                self.validation_stats['total_validations'] += 1
            
            email = email.strip().lower()
            checks_passed = []
            checks_failed = []
            details = {}
            
            # Basic format validation
            if self._validate_format(email):
                checks_passed.append('format')
                details['format_valid'] = True
            else:
                checks_failed.append('format')
                details['format_valid'] = False
                
                # If basic format fails, return early
                result = ValidationResult(
                    email=email,
                    is_valid=False,
                    score=0.0,
                    validation_method='format_only',
                    checks_passed=checks_passed,
                    checks_failed=checks_failed,
                    details=details,
                    validated_time=start_time
                )
                
                with self.validation_lock:
                    self.validation_stats['invalid_emails'] += 1
                
                return result
            
            # Extract domain
            domain = email.split('@')[1]
            details['domain'] = domain
            
            # Length validation
            if self._validate_length(email):
                checks_passed.append('length')
                details['length_valid'] = True
            else:
                checks_failed.append('length')
                details['length_valid'] = False
            
            # Character validation
            if self._validate_characters(email):
                checks_passed.append('characters')
                details['characters_valid'] = True
            else:
                checks_failed.append('characters')
                details['characters_valid'] = False
            
            # Domain validation
            domain_result = self._validate_domain(domain)
            if domain_result['is_valid']:
                checks_passed.append('domain')
                details.update(domain_result)
            else:
                checks_failed.append('domain')
                details.update(domain_result)
            
            # Role-based email check
            if self.enable_role_check:
                local_part = email.split('@')[0]
                if self._is_role_based(local_part):
                    checks_failed.append('role_based')
                    details['is_role_based'] = True
                else:
                    checks_passed.append('not_role_based')
                    details['is_role_based'] = False
            
            # Disposable email check
            if self.enable_disposable_check:
                if self._is_disposable_domain(domain):
                    checks_failed.append('disposable')
                    details['is_disposable'] = True
                else:
                    checks_passed.append('not_disposable')
                    details['is_disposable'] = False
            
            # MX record check
            if self.enable_mx_check:
                mx_result = self._check_mx_record(domain)
                if mx_result['has_mx']:
                    checks_passed.append('mx_record')
                    details.update(mx_result)
                    
                    with self.validation_lock:
                        self.validation_stats['mx_checks_performed'] += 1
                else:
                    checks_failed.append('mx_record')
                    details.update(mx_result)
            
            # Calculate validation score
            score = self._calculate_validation_score(checks_passed, checks_failed, details)
            
            # Determine if email is valid
            is_valid = self._determine_validity(checks_passed, checks_failed, score)
            
            # Create result
            result = ValidationResult(
                email=email,
                is_valid=is_valid,
                score=score,
                validation_method='comprehensive',
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                details=details,
                validated_time=start_time
            )
            
            # Update statistics
            with self.validation_lock:
                if is_valid:
                    self.validation_stats['valid_emails'] += 1
                else:
                    self.validation_stats['invalid_emails'] += 1
            
            logger.debug(f"Email validation completed: {email} - Valid: {is_valid}, Score: {score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating email {email}: {e}")
            
            # Return error result
            return ValidationResult(
                email=email,
                is_valid=False,
                score=0.0,
                validation_method='error',
                checks_passed=[],
                checks_failed=['validation_error'],
                details={'error': str(e)},
                validated_time=start_time
            )
    
    def _validate_format(self, email: str) -> bool:
        """Basic email format validation"""
        try:
            # Use regex pattern
            if not self.email_pattern.match(email):
                return False
            
            # Additional checks
            if email.count('@') != 1:
                return False
            
            local, domain = email.rsplit('@', 1)
            
            # Local part checks
            if not local or len(local) > 64:
                return False
            
            if local.startswith('.') or local.endswith('.'):
                return False
            
            if '..' in local:
                return False
            
            # Domain part checks
            if not domain or len(domain) > 253:
                return False
            
            if domain.startswith('.') or domain.endswith('.'):
                return False
            
            if '..' in domain:
                return False
            
            # Check domain labels
            labels = domain.split('.')
            if len(labels) < 2:
                return False
            
            for label in labels:
                if not label or len(label) > 63:
                    return False
                if label.startswith('-') or label.endswith('-'):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_length(self, email: str) -> bool:
        """Validate email length"""
        return 6 <= len(email) <= 254
    
    def _validate_characters(self, email: str) -> bool:
        """Validate allowed characters"""
        try:
            local, domain = email.rsplit('@', 1)
            
            # Local part character validation
            allowed_local_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+-')
            if not all(c in allowed_local_chars for c in local):
                return False
            
            # Domain part character validation
            allowed_domain_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-')
            if not all(c in allowed_domain_chars for c in domain):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_domain(self, domain: str) -> Dict[str, Any]:
        """Validate domain structure and format"""
        try:
            result = {
                'domain': domain,
                'is_valid': True,
                'domain_checks': []
            }
            
            # Check domain length
            if len(domain) > 253:
                result['is_valid'] = False
                result['domain_checks'].append('domain_too_long')
            
            # Check labels
            labels = domain.split('.')
            if len(labels) < 2:
                result['is_valid'] = False
                result['domain_checks'].append('insufficient_labels')
            
            # Check TLD
            tld = labels[-1]
            if len(tld) < 2 or not tld.isalpha():
                result['is_valid'] = False
                result['domain_checks'].append('invalid_tld')
            
            # Check each label
            for i, label in enumerate(labels):
                if not label:
                    result['is_valid'] = False
                    result['domain_checks'].append(f'empty_label_{i}')
                elif len(label) > 63:
                    result['is_valid'] = False
                    result['domain_checks'].append(f'label_too_long_{i}')
                elif label.startswith('-') or label.endswith('-'):
                    result['is_valid'] = False
                    result['domain_checks'].append(f'invalid_label_format_{i}')
            
            if result['is_valid']:
                result['domain_checks'].append('format_valid')
            
            return result
            
        except Exception as e:
            return {
                'domain': domain,
                'is_valid': False,
                'domain_checks': ['validation_error'],
                'error': str(e)
            }
    
    def _is_role_based(self, local_part: str) -> bool:
        """Check if email is role-based"""
        return local_part.lower() in self.role_based_addresses
    
    def _is_disposable_domain(self, domain: str) -> bool:
        """Check if domain is disposable/temporary"""
        return domain.lower() in self.disposable_domains
    
    def _check_mx_record(self, domain: str) -> Dict[str, Any]:
        """Check MX record for domain"""
        try:
            # Check cache first
            cache_key = f"mx_{domain}"
            if cache_key in self.domain_cache:
                cached_info = self.domain_cache[cache_key]
                cache_time = cached_info.get('timestamp', datetime.min)
                if (datetime.now() - cache_time).total_seconds() < self.cache_ttl:
                    with self.validation_lock:
                        self.validation_stats['cache_hits'] += 1
                    return cached_info['data']
            
            # Perform MX lookup
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                mx_list = [str(mx) for mx in mx_records]
                
                result = {
                    'has_mx': True,
                    'mx_records': mx_list,
                    'mx_count': len(mx_list)
                }
                
            except dns.resolver.NXDOMAIN:
                result = {
                    'has_mx': False,
                    'mx_records': [],
                    'mx_count': 0,
                    'error': 'Domain does not exist'
                }
            except dns.resolver.NoAnswer:
                result = {
                    'has_mx': False,
                    'mx_records': [],
                    'mx_count': 0,
                    'error': 'No MX records found'
                }
            except Exception as e:
                result = {
                    'has_mx': False,
                    'mx_records': [],
                    'mx_count': 0,
                    'error': f'MX lookup failed: {e}'
                }
            
            # Cache result
            self.domain_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            with self.validation_lock:
                self.validation_stats['cache_misses'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking MX record for {domain}: {e}")
            return {
                'has_mx': False,
                'mx_records': [],
                'mx_count': 0,
                'error': str(e)
            }
    
    def _calculate_validation_score(self, checks_passed: List[str], 
                                  checks_failed: List[str], details: Dict[str, Any]) -> float:
        """Calculate validation score based on checks"""
        try:
            total_checks = len(checks_passed) + len(checks_failed)
            if total_checks == 0:
                return 0.0
            
            # Weight different checks
            weights = {
                'format': 0.3,
                'length': 0.1,
                'characters': 0.1,
                'domain': 0.2,
                'not_role_based': 0.1,
                'not_disposable': 0.1,
                'mx_record': 0.1
            }
            
            score = 0.0
            total_weight = 0.0
            
            for check in checks_passed:
                weight = weights.get(check, 0.05)
                score += weight
                total_weight += weight
            
            for check in checks_failed:
                weight = weights.get(check.replace('not_', ''), 0.05)
                total_weight += weight
            
            # Normalize score
            if total_weight > 0:
                score = score / total_weight
            
            # Apply penalties for critical failures
            if 'format' in checks_failed:
                score *= 0.1  # Heavy penalty for format failure
            
            if 'domain' in checks_failed:
                score *= 0.5  # Moderate penalty for domain failure
            
            return min(max(score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating validation score: {e}")
            return 0.0
    
    def _determine_validity(self, checks_passed: List[str], 
                          checks_failed: List[str], score: float) -> bool:
        """Determine if email is valid based on checks and score"""
        try:
            # Critical failures that make email invalid
            critical_failures = ['format', 'domain']
            
            if any(failure in checks_failed for failure in critical_failures):
                return False
            
            # In strict mode, apply stricter rules
            if self.strict_mode:
                # Fail if disposable or role-based in strict mode
                if 'disposable' in checks_failed or 'role_based' in checks_failed:
                    return False
                
                # Require higher score in strict mode
                return score >= 0.8
            else:
                # In permissive mode, use lower threshold
                return score >= 0.6
                
        except Exception as e:
            logger.error(f"Error determining validity: {e}")
            return False
    
    def validate_email_list(self, emails: List[str]) -> List[ValidationResult]:
        """Validate a list of emails efficiently"""
        results = []
        
        logger.info(f"Validating {len(emails)} emails")
        
        try:
            for i, email in enumerate(emails):
                result = self.validate_email(email)
                results.append(result)
                
                # Log progress for large lists
                if len(emails) > 100 and (i + 1) % 100 == 0:
                    logger.info(f"Validated {i + 1}/{len(emails)} emails")
            
            logger.info(f"Email list validation completed: {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error validating email list: {e}")
            return results
    
    def _load_disposable_domains(self):
        """Load disposable email domains list"""
        try:
            # Built-in list of common disposable domains
            builtin_disposable = {
                '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
                'mailinator.com', 'throwaway.email', 'temp-mail.org',
                'yopmail.com', 'maildrop.cc', 'mohmal.com', 'sharklasers.com',
                'trashmail.com', 'deadaddress.com', 'spamgourmet.com',
                'incognitomail.org', 'tempinbox.com', 'emailondeck.com'
            }
            
            self.disposable_domains.update(builtin_disposable)
            
            # Try to load from file
            disposable_file = Path("data") / "disposable_domains.txt"
            if disposable_file.exists():
                with open(disposable_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        domain = line.strip().lower()
                        if domain and not domain.startswith('#'):
                            self.disposable_domains.add(domain)
            
            logger.info(f"Loaded {len(self.disposable_domains)} disposable domains")
            
        except Exception as e:
            logger.warning(f"Error loading disposable domains: {e}")
    
    def _update_disposable_domains(self):
        """Update disposable domains list (placeholder for future enhancement)"""
        try:
            # This could be enhanced to fetch updated lists from external sources
            # For now, we'll just use the built-in list
            logger.debug("Disposable domains list is up to date")
            
        except Exception as e:
            logger.warning(f"Error updating disposable domains: {e}")
    
    def _load_domain_cache(self):
        """Load domain cache from file"""
        try:
            cache_file = Path("cache") / "domain_cache.json"
            
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Convert timestamp strings back to datetime objects
                for key, value in cache_data.items():
                    if 'timestamp' in value:
                        value['timestamp'] = datetime.fromisoformat(value['timestamp'])
                
                self.domain_cache = cache_data
                logger.info(f"Loaded {len(self.domain_cache)} cached domains")
                
        except Exception as e:
            logger.warning(f"Error loading domain cache: {e}")
    
    def _save_domain_cache(self):
        """Save domain cache to file"""
        try:
            cache_file = Path("cache") / "domain_cache.json"
            
            # Convert datetime objects to strings for JSON serialization
            serializable_cache = {}
            for key, value in self.domain_cache.items():
                serializable_value = value.copy()
                if 'timestamp' in serializable_value:
                    serializable_value['timestamp'] = serializable_value['timestamp'].isoformat()
                serializable_cache[key] = serializable_value
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_cache, f, indent=2, ensure_ascii=False)
            
            logger.debug("Domain cache saved")
            
        except Exception as e:
            logger.warning(f"Error saving domain cache: {e}")
    
    def clear_cache(self):
        """Clear domain validation cache"""
        try:
            self.domain_cache.clear()
            
            # Remove cache file
            cache_file = Path("cache") / "domain_cache.json"
            if cache_file.exists():
                cache_file.unlink()
            
            logger.info("Domain validation cache cleared")
            
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics"""
        with self.validation_lock:
            stats = self.validation_stats.copy()
        
        # Calculate additional metrics
        if stats['total_validations'] > 0:
            stats['valid_percentage'] = (stats['valid_emails'] / stats['total_validations']) * 100
            stats['invalid_percentage'] = (stats['invalid_emails'] / stats['total_validations']) * 100
            stats['cache_hit_rate'] = (stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses'])) * 100 if (stats['cache_hits'] + stats['cache_misses']) > 0 else 0
        else:
            stats['valid_percentage'] = 0
            stats['invalid_percentage'] = 0
            stats['cache_hit_rate'] = 0
        
        stats.update({
            'cache_size': len(self.domain_cache),
            'disposable_domains_count': len(self.disposable_domains),
            'role_based_addresses_count': len(self.role_based_addresses),
            'settings': {
                'enable_mx_check': self.enable_mx_check,
                'enable_role_check': self.enable_role_check,
                'enable_disposable_check': self.enable_disposable_check,
                'strict_mode': self.strict_mode,
                'cache_ttl_seconds': self.cache_ttl
            }
        })
        
        return stats
    
    def update_settings(self, **kwargs):
        """Update validation settings"""
        try:
            if 'enable_mx_check' in kwargs:
                self.enable_mx_check = bool(kwargs['enable_mx_check'])
            
            if 'enable_role_check' in kwargs:
                self.enable_role_check = bool(kwargs['enable_role_check'])
            
            if 'enable_disposable_check' in kwargs:
                self.enable_disposable_check = bool(kwargs['enable_disposable_check'])
            
            if 'strict_mode' in kwargs:
                self.strict_mode = bool(kwargs['strict_mode'])
            
            if 'cache_ttl' in kwargs:
                self.cache_ttl = int(kwargs['cache_ttl'])
            
            logger.info("Validation settings updated")
            
        except Exception as e:
            logger.error(f"Error updating validation settings: {e}")
    
    def export_validation_report(self, results: List[ValidationResult], filepath: str) -> bool:
        """Export validation results to detailed report"""
        try:
            report_data = {
                'report_info': {
                    'generated_time': datetime.now().isoformat(),
                    'total_validations': len(results),
                    'validation_engine_version': '4.0'
                },
                'summary': {
                    'valid_emails': len([r for r in results if r.is_valid]),
                    'invalid_emails': len([r for r in results if not r.is_valid]),
                    'average_score': sum(r.score for r in results) / len(results) if results else 0
                },
                'validation_results': [
                    {
                        'email': result.email,
                        'is_valid': result.is_valid,
                        'score': result.score,
                        'validation_method': result.validation_method,
                        'checks_passed': result.checks_passed,
                        'checks_failed': result.checks_failed,
                        'details': result.details,
                        'validated_time': result.validated_time.isoformat()
                    }
                    for result in results
                ],
                'statistics': self.get_validation_statistics()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Validation report exported to: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting validation report: {e}")
            return False
    
    def health_check(self) -> bool:
        """Perform health check on validation engine"""
        try:
            # Test basic validation
            test_email = "test@example.com"
            result = self.validate_email(test_email)
            
            if not hasattr(result, 'is_valid'):
                return False
            
            # Test domain cache access
            if not isinstance(self.domain_cache, dict):
                return False
            
            # Test disposable domains list
            if not isinstance(self.disposable_domains, set):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation engine health check failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup validation engine resources"""
        try:
            # Save cache
            self._save_domain_cache()
            
            # Clear runtime data
            self.domain_cache.clear()
            
            logger.info("Validation engine cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during validation engine cleanup: {e}")