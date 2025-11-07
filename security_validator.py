"""
Security Validation Module

Provides security checks for:
- Secret scanning (API keys, tokens, passwords)
- PII detection (emails, phone numbers, SSNs)
- Forbidden pattern matching
- File size validation
- Domain allowlisting
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from schemas import SecurityConfig, SecurityLevel

logger = logging.getLogger(__name__)


@dataclass
class SecurityViolation:
    """A security violation found during scanning"""
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "secret", "pii", "forbidden_pattern", etc.
    message: str
    line_number: Optional[int] = None
    matched_pattern: Optional[str] = None
    suggestion: Optional[str] = None


class SecurityValidator:
    """Validates content for security issues"""
    
    # Common secret patterns
    SECRET_PATTERNS = {
        "aws_access_key": r"AKIA[0-9A-Z]{16}",
        "aws_secret_key": r"aws_secret_access_key\s*=\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
        "github_token": r"gh[ps]_[a-zA-Z0-9]{36}",
        "generic_api_key": r"(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
        "slack_token": r"xox[baprs]-[0-9a-zA-Z]{10,48}",
        "slack_webhook": r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}",
        "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "jwt_token": r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
        "password": r"(?i)password\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
        "stripe_key": r"(?:sk|pk)_live_[0-9a-zA-Z]{24,}",
        "google_api": r"AIza[0-9A-Za-z\-_]{35}",
        "heroku_api": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
    }
    
    # PII patterns
    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "phone_us": r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    }
    
    # High-risk code patterns
    DANGEROUS_PATTERNS = {
        "eval": r"\beval\s*\(",
        "exec": r"\bexec\s*\(",
        "os_system": r"os\.system\s*\(",
        "subprocess_shell": r"subprocess\.[a-zA-Z_]+\([^)]*shell\s*=\s*True",
        "sql_injection_risk": r"(execute|cursor)\s*\([^)]*%s|format\s*\(",
    }
    
    def __init__(self, config: SecurityConfig):
        """
        Initialize security validator
        
        Args:
            config: Security configuration
        """
        self.config = config
        
    def validate_content(
        self, 
        content: str,
        filename: str = "unknown",
        content_type: str = "general"
    ) -> Tuple[bool, List[SecurityViolation]]:
        """
        Validate content for security issues
        
        Args:
            content: The content to validate
            filename: Name of the file being validated
            content_type: Type of content (instruction, rule, workflow, etc.)
        
        Returns:
            Tuple of (is_valid, violations)
        """
        if not self.config.enabled:
            return True, []
        
        violations: List[SecurityViolation] = []
        
        # File size check
        content_size_kb = len(content.encode('utf-8')) / 1024
        if content_size_kb > self.config.max_file_size_kb:
            violations.append(SecurityViolation(
                severity="medium",
                category="file_size",
                message=f"File size ({content_size_kb:.2f} KB) exceeds limit ({self.config.max_file_size_kb} KB)",
                suggestion="Consider splitting into multiple files or removing unnecessary content"
            ))
        
        # Secret scanning
        if self.config.scan_for_secrets:
            secret_violations = self._scan_for_secrets(content, filename)
            violations.extend(secret_violations)
        
        # PII scanning
        if self.config.scan_for_pii:
            pii_violations = self._scan_for_pii(content, filename)
            violations.extend(pii_violations)
        
        # Forbidden patterns
        if self.config.forbidden_patterns:
            pattern_violations = self._check_forbidden_patterns(content, filename)
            violations.extend(pattern_violations)
        
        # Required patterns
        if self.config.required_patterns:
            required_violations = self._check_required_patterns(content, filename)
            violations.extend(required_violations)
        
        # Dangerous code patterns
        if self.config.level in [SecurityLevel.STRICT, SecurityLevel.PARANOID]:
            dangerous_violations = self._scan_for_dangerous_patterns(content, filename)
            violations.extend(dangerous_violations)
        
        # Determine if content is valid based on severity
        is_valid = self._is_valid(violations)
        
        return is_valid, violations
    
    def _scan_for_secrets(self, content: str, filename: str) -> List[SecurityViolation]:
        """Scan content for potential secrets"""
        violations = []
        lines = content.split('\n')
        
        for pattern_name, pattern in self.SECRET_PATTERNS.items():
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    # Skip if it's in a comment or documentation
                    if self._is_in_comment_or_doc(line):
                        continue
                    
                    violations.append(SecurityViolation(
                        severity="critical",
                        category="secret",
                        message=f"Potential {pattern_name} detected in {filename}",
                        line_number=line_num,
                        matched_pattern=pattern_name,
                        suggestion="Remove secrets and use environment variables or secret management tools"
                    ))
        
        return violations
    
    def _scan_for_pii(self, content: str, filename: str) -> List[SecurityViolation]:
        """Scan content for personally identifiable information"""
        violations = []
        lines = content.split('\n')
        
        # Skip PII scanning if explicitly allowed (e.g., for documentation with examples)
        if "<!-- SKIP_PII_SCAN -->" in content:
            return violations
        
        for pattern_name, pattern in self.PII_PATTERNS.items():
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    # Skip common false positives
                    if self._is_pii_false_positive(match.group(), pattern_name):
                        continue
                    
                    violations.append(SecurityViolation(
                        severity="high",
                        category="pii",
                        message=f"Potential {pattern_name} detected in {filename}",
                        line_number=line_num,
                        matched_pattern=pattern_name,
                        suggestion="Replace with placeholder or example data"
                    ))
        
        return violations
    
    def _scan_for_dangerous_patterns(self, content: str, filename: str) -> List[SecurityViolation]:
        """Scan for dangerous code patterns"""
        violations = []
        lines = content.split('\n')
        
        for pattern_name, pattern in self.DANGEROUS_PATTERNS.items():
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    if self._is_in_comment_or_doc(line):
                        continue
                    
                    violations.append(SecurityViolation(
                        severity="high",
                        category="dangerous_code",
                        message=f"Dangerous pattern '{pattern_name}' detected in {filename}",
                        line_number=line_num,
                        matched_pattern=pattern_name,
                        suggestion="Review this code pattern for security implications"
                    ))
        
        return violations
    
    def _check_forbidden_patterns(self, content: str, filename: str) -> List[SecurityViolation]:
        """Check for forbidden patterns defined in config"""
        violations = []
        
        for pattern in self.config.forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(SecurityViolation(
                    severity="high",
                    category="forbidden_pattern",
                    message=f"Forbidden pattern '{pattern}' found in {filename}",
                    matched_pattern=pattern,
                    suggestion="Remove or replace this pattern according to team policies"
                ))
        
        return violations
    
    def _check_required_patterns(self, content: str, filename: str) -> List[SecurityViolation]:
        """Check for required patterns defined in config"""
        violations = []
        
        for pattern in self.config.required_patterns:
            if not re.search(pattern, content, re.IGNORECASE):
                violations.append(SecurityViolation(
                    severity="medium",
                    category="missing_required",
                    message=f"Required pattern '{pattern}' not found in {filename}",
                    matched_pattern=pattern,
                    suggestion="Add the required pattern according to team policies"
                ))
        
        return violations
    
    def _is_in_comment_or_doc(self, line: str) -> bool:
        """Check if content is in a comment or documentation"""
        stripped = line.strip()
        return (
            stripped.startswith('#') or
            stripped.startswith('//') or
            stripped.startswith('/*') or
            stripped.startswith('*') or
            stripped.startswith('"""') or
            stripped.startswith("'''") or
            stripped.startswith('<!--')
        )
    
    def _is_pii_false_positive(self, match: str, pattern_name: str) -> bool:
        """Check if PII match is a common false positive"""
        false_positives = {
            "email": ["example@example.com", "user@example.com", "test@test.com"],
            "phone_us": ["555-555-5555", "123-456-7890"],
            "ssn": ["123-45-6789", "000-00-0000"],
            "ip_address": ["127.0.0.1", "0.0.0.0", "255.255.255.255"],
        }
        
        if pattern_name in false_positives:
            return match in false_positives[pattern_name]
        
        return False
    
    def _is_valid(self, violations: List[SecurityViolation]) -> bool:
        """
        Determine if content is valid based on violations and security level
        
        Args:
            violations: List of security violations
        
        Returns:
            True if content is valid, False otherwise
        """
        if not violations:
            return True
        
        # Check for critical violations
        critical_violations = [v for v in violations if v.severity == "critical"]
        if critical_violations:
            return False
        
        # For strict and paranoid levels, any high severity violation fails
        if self.config.level in [SecurityLevel.STRICT, SecurityLevel.PARANOID]:
            high_violations = [v for v in violations if v.severity == "high"]
            if high_violations:
                return False
        
        # For paranoid level, even medium violations fail
        if self.config.level == SecurityLevel.PARANOID:
            medium_violations = [v for v in violations if v.severity == "medium"]
            if medium_violations:
                return False
        
        return True
    
    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if URL is from an allowed domain
        
        Args:
            url: URL to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.config.enabled or not self.config.allowed_domains:
            return True, None
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        
        for allowed_domain in self.config.allowed_domains:
            if domain.endswith(allowed_domain) or domain == allowed_domain:
                return True, None
        
        return False, f"Domain '{domain}' is not in the allowed domains list"
    
    def generate_report(self, violations: List[SecurityViolation]) -> str:
        """
        Generate a human-readable security report
        
        Args:
            violations: List of security violations
        
        Returns:
            Formatted report string
        """
        if not violations:
            return "✅ No security violations found"
        
        report = ["🔒 Security Scan Report", "=" * 50]
        
        # Group by severity
        by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for v in violations:
            by_severity[v.severity].append(v)
        
        # Report by severity
        for severity in ["critical", "high", "medium", "low"]:
            items = by_severity[severity]
            if not items:
                continue
            
            emoji = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "⚡",
                "low": "ℹ️"
            }[severity]
            
            report.append(f"\n{emoji} {severity.upper()} ({len(items)} issue{'s' if len(items) > 1 else ''})")
            
            for v in items:
                report.append(f"  • {v.message}")
                if v.line_number:
                    report.append(f"    Line: {v.line_number}")
                if v.suggestion:
                    report.append(f"    💡 {v.suggestion}")
        
        report.append("\n" + "=" * 50)
        return "\n".join(report)


def create_default_security_config() -> SecurityConfig:
    """Create a default security configuration"""
    return SecurityConfig(
        enabled=True,
        level=SecurityLevel.BASIC,
        forbidden_patterns=[
            r"(?i)todo:?\s*hack",
            r"(?i)fixme:?\s*security",
        ],
        max_file_size_kb=1024,
        scan_for_secrets=True,
        scan_for_pii=True,
    )
