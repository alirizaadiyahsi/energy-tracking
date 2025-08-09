"""
IP blocking and threat detection system
Automatically blocks malicious IPs and detects attack patterns
"""

import time
import json
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from libs.common.cache import CacheManager
from infrastructure.logging import ServiceLogger

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ThreatEvent:
    """Represents a security threat event"""
    ip_address: str
    event_type: str
    severity: ThreatLevel
    timestamp: datetime
    details: Dict
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['severity'] = self.severity.value
        return data

@dataclass
class IPReputation:
    """IP address reputation and threat information"""
    ip_address: str
    threat_score: int  # 0-100, higher is more dangerous
    is_blocked: bool
    first_seen: datetime
    last_activity: datetime
    threat_events: List[ThreatEvent]
    country: Optional[str] = None
    asn: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['first_seen'] = self.first_seen.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        data['threat_events'] = [event.to_dict() for event in self.threat_events]
        return data

class ThreatDetector:
    """Detects various types of security threats"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.logger = ServiceLogger("threat-detector")
        
        # Threat detection thresholds
        self.FAILED_LOGIN_THRESHOLD = 5  # Failed logins in 10 minutes
        self.RAPID_REQUEST_THRESHOLD = 100  # Requests in 1 minute
        self.ERROR_RATE_THRESHOLD = 0.5  # 50% error rate
        self.SUSPICIOUS_ENDPOINT_THRESHOLD = 10  # Hits to admin endpoints
        
        # Known malicious patterns
        self.MALICIOUS_PATTERNS = [
            # SQL injection
            "union select", "drop table", "insert into", "delete from",
            "exec master", "xp_cmdshell", "sp_executesql",
            
            # XSS patterns
            "<script", "</script>", "javascript:", "vbscript:",
            "onload=", "onerror=", "onclick=",
            
            # Path traversal
            "../", "..\\", "/etc/passwd", "/etc/shadow", "\\x",
            
            # Command injection
            "; cat ", "; ls ", "| nc ", "&& wget", "curl -",
            
            # File inclusion
            "php://", "file://", "data://", "expect://",
        ]
        
        # Suspicious user agents
        self.SUSPICIOUS_USER_AGENTS = [
            "sqlmap", "nikto", "nmap", "masscan", "zap",
            "burp", "metasploit", "havij", "acunetix"
        ]
    
    async def analyze_request(self, ip: str, user_agent: str, endpoint: str, 
                            method: str, status_code: int) -> List[ThreatEvent]:
        """Analyze a request for threats"""
        threats = []
        now = datetime.utcnow()
        
        # Check for malicious patterns in endpoint
        endpoint_lower = endpoint.lower()
        for pattern in self.MALICIOUS_PATTERNS:
            if pattern in endpoint_lower:
                threats.append(ThreatEvent(
                    ip_address=ip,
                    event_type="malicious_pattern_detected",
                    severity=ThreatLevel.HIGH,
                    timestamp=now,
                    details={
                        "pattern": pattern,
                        "endpoint": endpoint,
                        "method": method
                    },
                    user_agent=user_agent,
                    endpoint=endpoint
                ))
        
        # Check for suspicious user agent
        user_agent_lower = user_agent.lower()
        for suspicious_agent in self.SUSPICIOUS_USER_AGENTS:
            if suspicious_agent in user_agent_lower:
                threats.append(ThreatEvent(
                    ip_address=ip,
                    event_type="suspicious_user_agent",
                    severity=ThreatLevel.MEDIUM,
                    timestamp=now,
                    details={
                        "user_agent": user_agent,
                        "endpoint": endpoint
                    },
                    user_agent=user_agent,
                    endpoint=endpoint
                ))
        
        # Check for admin endpoint access
        admin_endpoints = ["/admin", "/wp-admin", "/phpmyadmin", "/.env", "/config"]
        if any(admin_ep in endpoint_lower for admin_ep in admin_endpoints):
            threats.append(ThreatEvent(
                ip_address=ip,
                event_type="admin_endpoint_access",
                severity=ThreatLevel.MEDIUM,
                timestamp=now,
                details={
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code
                },
                user_agent=user_agent,
                endpoint=endpoint
            ))
        
        # Check for error responses (potential probing)
        if status_code >= 400:
            threats.append(ThreatEvent(
                ip_address=ip,
                event_type="error_response",
                severity=ThreatLevel.LOW,
                timestamp=now,
                details={
                    "status_code": status_code,
                    "endpoint": endpoint,
                    "method": method
                },
                user_agent=user_agent,
                endpoint=endpoint
            ))
        
        return threats
    
    async def check_rate_anomalies(self, ip: str) -> List[ThreatEvent]:
        """Check for rate-based anomalies"""
        threats = []
        now = datetime.utcnow()
        
        # Check request rate
        minute_key = f"request_count:minute:{ip}:{now.strftime('%Y%m%d%H%M')}"
        minute_count = await self.cache.get(minute_key) or 0
        
        if int(minute_count) > self.RAPID_REQUEST_THRESHOLD:
            threats.append(ThreatEvent(
                ip_address=ip,
                event_type="rapid_requests",
                severity=ThreatLevel.HIGH,
                timestamp=now,
                details={
                    "requests_per_minute": int(minute_count),
                    "threshold": self.RAPID_REQUEST_THRESHOLD
                }
            ))
        
        # Check failed login attempts
        failed_login_key = f"failed_logins:{ip}"
        failed_logins = await self.cache.get(failed_login_key) or 0
        
        if int(failed_logins) > self.FAILED_LOGIN_THRESHOLD:
            threats.append(ThreatEvent(
                ip_address=ip,
                event_type="brute_force_login",
                severity=ThreatLevel.HIGH,
                timestamp=now,
                details={
                    "failed_attempts": int(failed_logins),
                    "threshold": self.FAILED_LOGIN_THRESHOLD
                }
            ))
        
        return threats

class IPBlocklist:
    """Manages IP address blocking"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.logger = ServiceLogger("ip-blocklist")
        
        # Default block durations (in seconds)
        self.BLOCK_DURATIONS = {
            ThreatLevel.LOW: 300,      # 5 minutes
            ThreatLevel.MEDIUM: 1800,  # 30 minutes
            ThreatLevel.HIGH: 3600,    # 1 hour
            ThreatLevel.CRITICAL: 86400  # 24 hours
        }
    
    async def is_blocked(self, ip: str) -> tuple[bool, Optional[Dict]]:
        """Check if IP is currently blocked"""
        block_key = f"blocked_ip:{ip}"
        block_data = await self.cache.get(block_key)
        
        if block_data:
            try:
                block_info = json.loads(block_data)
                return True, block_info
            except json.JSONDecodeError:
                # Clear invalid block data
                await self.cache.delete(block_key)
                return False, None
        
        return False, None
    
    async def block_ip(self, ip: str, reason: str, severity: ThreatLevel, 
                      duration: Optional[int] = None):
        """Block an IP address"""
        if duration is None:
            duration = self.BLOCK_DURATIONS[severity]
        
        block_info = {
            "ip": ip,
            "reason": reason,
            "severity": severity.value,
            "blocked_at": datetime.utcnow().isoformat(),
            "duration": duration,
            "expires_at": (datetime.utcnow() + timedelta(seconds=duration)).isoformat()
        }
        
        block_key = f"blocked_ip:{ip}"
        await self.cache.set(block_key, json.dumps(block_info), expire=duration)
        
        self.logger.warning(f"IP blocked: {ip}", extra=block_info)
    
    async def unblock_ip(self, ip: str):
        """Manually unblock an IP address"""
        block_key = f"blocked_ip:{ip}"
        await self.cache.delete(block_key)
        
        self.logger.info(f"IP unblocked: {ip}")
    
    async def get_blocked_ips(self) -> List[Dict]:
        """Get list of currently blocked IPs"""
        # This would require Redis SCAN or a separate index
        # For simplicity, we'll return empty list
        # In production, maintain a separate index of blocked IPs
        return []

class ThreatIntelligence:
    """Threat intelligence and IP reputation management"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.detector = ThreatDetector(cache_manager)
        self.blocklist = IPBlocklist(cache_manager)
        self.logger = ServiceLogger("threat-intelligence")
        
        # Auto-block thresholds
        self.AUTO_BLOCK_THRESHOLDS = {
            ThreatLevel.HIGH: 3,      # 3 high-severity events
            ThreatLevel.CRITICAL: 1   # 1 critical event
        }
    
    async def process_request(self, ip: str, user_agent: str, endpoint: str,
                            method: str, status_code: int) -> bool:
        """
        Process a request and determine if it should be blocked
        Returns True if request should be allowed, False if blocked
        """
        # Check if IP is already blocked
        is_blocked, block_info = await self.blocklist.is_blocked(ip)
        if is_blocked:
            self.logger.info(f"Blocked IP attempted access: {ip}", extra=block_info)
            return False
        
        # Analyze request for threats
        threats = await self.detector.analyze_request(
            ip, user_agent, endpoint, method, status_code
        )
        
        # Check for rate anomalies
        rate_threats = await self.detector.check_rate_anomalies(ip)
        threats.extend(rate_threats)
        
        # Update IP reputation
        if threats:
            await self._update_ip_reputation(ip, threats)
            
            # Check if IP should be auto-blocked
            should_block, block_reason = await self._should_auto_block(ip, threats)
            if should_block:
                await self.blocklist.block_ip(
                    ip, block_reason, ThreatLevel.HIGH
                )
                return False
        
        # Update request counters
        await self._update_request_counters(ip, status_code)
        
        return True
    
    async def _update_ip_reputation(self, ip: str, threats: List[ThreatEvent]):
        """Update IP reputation based on threats"""
        rep_key = f"ip_reputation:{ip}"
        
        # Get existing reputation
        existing_data = await self.cache.get(rep_key)
        if existing_data:
            try:
                rep_data = json.loads(existing_data)
                reputation = IPReputation(**rep_data)
            except (json.JSONDecodeError, TypeError):
                reputation = self._create_new_reputation(ip)
        else:
            reputation = self._create_new_reputation(ip)
        
        # Add new threats
        reputation.threat_events.extend(threats)
        reputation.last_activity = datetime.utcnow()
        
        # Calculate threat score
        reputation.threat_score = self._calculate_threat_score(reputation.threat_events)
        
        # Store updated reputation
        await self.cache.set(
            rep_key, 
            json.dumps(reputation.to_dict(), default=str),
            expire=86400 * 7  # 7 days
        )
        
        # Log high-threat IPs
        if reputation.threat_score > 70:
            self.logger.warning(f"High-threat IP detected: {ip}", extra={
                "threat_score": reputation.threat_score,
                "recent_threats": len([t for t in threats if 
                    (datetime.utcnow() - t.timestamp).seconds < 3600])
            })
    
    def _create_new_reputation(self, ip: str) -> IPReputation:
        """Create new IP reputation record"""
        now = datetime.utcnow()
        return IPReputation(
            ip_address=ip,
            threat_score=0,
            is_blocked=False,
            first_seen=now,
            last_activity=now,
            threat_events=[]
        )
    
    def _calculate_threat_score(self, events: List[ThreatEvent]) -> int:
        """Calculate threat score based on events"""
        score = 0
        now = datetime.utcnow()
        
        # Weight recent events more heavily
        for event in events:
            age_hours = (now - event.timestamp).total_seconds() / 3600
            age_weight = max(0.1, 1.0 - (age_hours / 24))  # Decay over 24 hours
            
            severity_weights = {
                ThreatLevel.LOW: 5,
                ThreatLevel.MEDIUM: 15,
                ThreatLevel.HIGH: 30,
                ThreatLevel.CRITICAL: 50
            }
            
            score += severity_weights[event.severity] * age_weight
        
        return min(100, int(score))
    
    async def _should_auto_block(self, ip: str, threats: List[ThreatEvent]) -> tuple[bool, str]:
        """Determine if IP should be automatically blocked"""
        recent_threats = [t for t in threats if 
            (datetime.utcnow() - t.timestamp).seconds < 3600]  # Last hour
        
        # Count threats by severity
        severity_counts = {}
        for threat in recent_threats:
            severity_counts[threat.severity] = severity_counts.get(threat.severity, 0) + 1
        
        # Check auto-block thresholds
        for severity, threshold in self.AUTO_BLOCK_THRESHOLDS.items():
            if severity_counts.get(severity, 0) >= threshold:
                return True, f"Auto-blocked: {severity_counts[severity]} {severity.value} severity events"
        
        return False, ""
    
    async def _update_request_counters(self, ip: str, status_code: int):
        """Update request counters for rate monitoring"""
        now = datetime.utcnow()
        minute_key = f"request_count:minute:{ip}:{now.strftime('%Y%m%d%H%M')}"
        
        # Increment request counter
        current_count = await self.cache.get(minute_key) or 0
        await self.cache.set(minute_key, int(current_count) + 1, expire=60)
        
        # Track failed logins specifically
        if status_code == 401:  # Unauthorized
            failed_login_key = f"failed_logins:{ip}"
            current_failures = await self.cache.get(failed_login_key) or 0
            await self.cache.set(failed_login_key, int(current_failures) + 1, expire=600)  # 10 minutes

# Helper function for easy integration
async def create_threat_intelligence(cache_manager: CacheManager) -> ThreatIntelligence:
    """Create and initialize threat intelligence system"""
    return ThreatIntelligence(cache_manager)
