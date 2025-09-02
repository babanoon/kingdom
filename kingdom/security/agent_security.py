#!/usr/bin/env python3
"""
Security Framework for Kingdom Agents

This module provides security controls, access management, and secret protection
for the Kingdom agent system, ensuring that agents operate within secure boundaries
and sensitive information remains protected.
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import logging

class SecurityLevel(Enum):
    """Security clearance levels for agents"""
    PUBLIC = "public"              # No restrictions
    STANDARD = "standard"          # Basic restrictions
    ELEVATED = "elevated"          # Enhanced restrictions  
    CLASSIFIED = "classified"      # High security
    RESTRICTED = "restricted"      # Maximum security

class Permission(Enum):
    """Agent permissions"""
    # Data access
    READ_MEMORY = "read_memory"
    WRITE_MEMORY = "write_memory"
    DELETE_MEMORY = "delete_memory"
    
    # Communication
    SEND_MESSAGE = "send_message"
    BROADCAST_MESSAGE = "broadcast_message"
    CREATE_DOCUMENT = "create_document"
    
    # System operations
    CREATE_AGENT = "create_agent"
    STOP_AGENT = "stop_agent"
    ACCESS_LOGS = "access_logs"
    
    # External systems
    API_CALLS = "api_calls"
    FILE_SYSTEM = "file_system"
    NETWORK_ACCESS = "network_access"
    
    # Database operations
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    DATABASE_ADMIN = "database_admin"

@dataclass
class SecurityContext:
    """Security context for agent operations"""
    agent_id: str
    security_level: SecurityLevel
    permissions: Set[Permission]
    api_quota: Dict[str, int]  # API call limits
    network_restrictions: List[str]  # Allowed domains/IPs
    resource_limits: Dict[str, Any]  # CPU, memory, etc.
    session_start: datetime
    session_expires: Optional[datetime] = None

class AgentSecurityManager:
    """
    Manages security policies and access control for all agents.
    
    Provides authentication, authorization, secret management, and audit logging
    to ensure the Kingdom system operates securely.
    """
    
    def __init__(self, config_path: str = "./kingdom/security/security_config.json"):
        self.config_path = config_path
        self.security_config = self._load_security_config()
        
        # Active sessions and contexts
        self.active_sessions: Dict[str, SecurityContext] = {}
        self.permission_cache: Dict[str, Set[Permission]] = {}
        
        # Secret management
        self.secrets_store: Dict[str, Any] = {}
        self.api_keys: Dict[str, str] = {}
        
        # Audit logging
        self.audit_logger = self._setup_audit_logger()
        
        # Resource monitoring
        self.resource_usage: Dict[str, Dict[str, Any]] = {}
        
        # Security policies
        self.security_policies = self._load_security_policies()
        
        print("🔒 Agent Security Manager initialized")
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration"""
        default_config = {
            "default_security_level": "standard",
            "session_timeout_minutes": 480,  # 8 hours
            "max_api_calls_per_hour": 1000,
            "allowed_networks": ["localhost", "127.0.0.1"],
            "secret_encryption_key": None,  # Will be generated
            "audit_log_retention_days": 90,
            "resource_limits": {
                "max_memory_mb": 1024,
                "max_cpu_percent": 80,
                "max_disk_mb": 5000
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"⚠️  Could not load security config: {e}")
        
        return default_config
    
    def _load_security_policies(self) -> Dict[SecurityLevel, Set[Permission]]:
        """Define security policies for different levels"""
        return {
            SecurityLevel.PUBLIC: {
                Permission.READ_MEMORY,
                Permission.SEND_MESSAGE,
                Permission.CREATE_DOCUMENT
            },
            SecurityLevel.STANDARD: {
                Permission.READ_MEMORY,
                Permission.WRITE_MEMORY,
                Permission.SEND_MESSAGE,
                Permission.CREATE_DOCUMENT,
                Permission.DATABASE_READ,
                Permission.API_CALLS
            },
            SecurityLevel.ELEVATED: {
                Permission.READ_MEMORY,
                Permission.WRITE_MEMORY,
                Permission.DELETE_MEMORY,
                Permission.SEND_MESSAGE,
                Permission.BROADCAST_MESSAGE,
                Permission.CREATE_DOCUMENT,
                Permission.DATABASE_READ,
                Permission.DATABASE_WRITE,
                Permission.API_CALLS,
                Permission.FILE_SYSTEM
            },
            SecurityLevel.CLASSIFIED: {
                Permission.READ_MEMORY,
                Permission.WRITE_MEMORY,
                Permission.DELETE_MEMORY,
                Permission.SEND_MESSAGE,
                Permission.BROADCAST_MESSAGE,
                Permission.CREATE_DOCUMENT,
                Permission.CREATE_AGENT,
                Permission.DATABASE_READ,
                Permission.DATABASE_WRITE,
                Permission.API_CALLS,
                Permission.FILE_SYSTEM,
                Permission.NETWORK_ACCESS,
                Permission.ACCESS_LOGS
            },
            SecurityLevel.RESTRICTED: set(Permission)  # All permissions
        }
    
    def _setup_audit_logger(self) -> logging.Logger:
        """Setup security audit logging"""
        logger = logging.getLogger("kingdom.security.audit")
        logger.setLevel(logging.INFO)
        
        # Create audit log directory
        log_dir = "./kingdom/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler for audit logs
        handler = logging.FileHandler(f"{log_dir}/security_audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def create_security_context(self, agent_id: str, 
                                    security_level: SecurityLevel = None) -> SecurityContext:
        """Create security context for an agent"""
        if security_level is None:
            security_level = SecurityLevel(self.security_config["default_security_level"])
        
        # Get permissions for security level
        permissions = self.security_policies.get(security_level, set())
        
        # Create session
        session_timeout = timedelta(minutes=self.security_config["session_timeout_minutes"])
        context = SecurityContext(
            agent_id=agent_id,
            security_level=security_level,
            permissions=permissions,
            api_quota={"openai": self.security_config["max_api_calls_per_hour"]},
            network_restrictions=self.security_config["allowed_networks"],
            resource_limits=self.security_config["resource_limits"],
            session_start=datetime.now(),
            session_expires=datetime.now() + session_timeout
        )
        
        self.active_sessions[agent_id] = context
        self.permission_cache[agent_id] = permissions
        
        # Log session creation
        self.audit_logger.info(f"Security context created for agent {agent_id} with level {security_level.value}")
        
        return context
    
    async def check_permission(self, agent_id: str, permission: Permission) -> bool:
        """Check if agent has specific permission"""
        if agent_id not in self.active_sessions:
            self.audit_logger.warning(f"Permission check failed - no active session for agent {agent_id}")
            return False
        
        context = self.active_sessions[agent_id]
        
        # Check session expiry
        if context.session_expires and datetime.now() > context.session_expires:
            self.audit_logger.warning(f"Session expired for agent {agent_id}")
            await self.revoke_security_context(agent_id)
            return False
        
        # Check permission
        has_permission = permission in context.permissions
        
        # Log permission check
        result = "GRANTED" if has_permission else "DENIED"
        self.audit_logger.info(f"Permission {permission.value} {result} for agent {agent_id}")
        
        return has_permission
    
    async def request_api_access(self, agent_id: str, api_name: str) -> Optional[str]:
        """Request API access token for agent"""
        if not await self.check_permission(agent_id, Permission.API_CALLS):
            return None
        
        context = self.active_sessions.get(agent_id)
        if not context:
            return None
        
        # Check API quota
        if api_name in context.api_quota:
            if context.api_quota[api_name] <= 0:
                self.audit_logger.warning(f"API quota exceeded for {agent_id} on {api_name}")
                return None
            
            # Decrement quota
            context.api_quota[api_name] -= 1
        
        # Get or create API key for this agent
        api_key = self._get_api_key(agent_id, api_name)
        
        self.audit_logger.info(f"API access granted to agent {agent_id} for {api_name}")
        return api_key
    
    def _get_api_key(self, agent_id: str, api_name: str) -> str:
        """Get API key for agent and service"""
        # In production, this would retrieve from secure storage
        # For now, use environment variables or config
        
        env_var = f"{api_name.upper()}_API_KEY"
        api_key = os.getenv(env_var)
        
        if not api_key:
            # Generate a proxy key that maps to the real key
            proxy_key = f"agent_{agent_id}_{api_name}_{secrets.token_hex(16)}"
            self.api_keys[proxy_key] = {
                'agent_id': agent_id,
                'service': api_name,
                'real_key': 'PLACEHOLDER_KEY',  # Would be real key in production
                'created_at': datetime.now()
            }
            return proxy_key
        
        return api_key
    
    async def store_secret(self, agent_id: str, secret_name: str, secret_value: str) -> bool:
        """Store a secret for an agent"""
        if not await self.check_permission(agent_id, Permission.WRITE_MEMORY):
            return False
        
        # Encrypt the secret (simplified - use proper encryption in production)
        encrypted_secret = self._encrypt_secret(secret_value)
        
        secret_key = f"{agent_id}:{secret_name}"
        self.secrets_store[secret_key] = {
            'value': encrypted_secret,
            'created_at': datetime.now(),
            'accessed_count': 0
        }
        
        self.audit_logger.info(f"Secret {secret_name} stored for agent {agent_id}")
        return True
    
    async def retrieve_secret(self, agent_id: str, secret_name: str) -> Optional[str]:
        """Retrieve a secret for an agent"""
        if not await self.check_permission(agent_id, Permission.READ_MEMORY):
            return None
        
        secret_key = f"{agent_id}:{secret_name}"
        if secret_key not in self.secrets_store:
            return None
        
        secret_data = self.secrets_store[secret_key]
        
        # Decrypt and return
        decrypted_secret = self._decrypt_secret(secret_data['value'])
        
        # Update access count
        secret_data['accessed_count'] += 1
        secret_data['last_accessed'] = datetime.now()
        
        self.audit_logger.info(f"Secret {secret_name} accessed by agent {agent_id}")
        return decrypted_secret
    
    async def revoke_security_context(self, agent_id: str):
        """Revoke security context and clean up"""
        if agent_id in self.active_sessions:
            del self.active_sessions[agent_id]
        
        if agent_id in self.permission_cache:
            del self.permission_cache[agent_id]
        
        # Clean up API keys
        expired_keys = []
        for key, data in self.api_keys.items():
            if data['agent_id'] == agent_id:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.api_keys[key]
        
        self.audit_logger.info(f"Security context revoked for agent {agent_id}")
    
    def _encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret (simplified implementation)"""
        # In production, use proper encryption like Fernet
        return hashlib.sha256(secret.encode()).hexdigest()
    
    def _decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret (simplified implementation)"""
        # In production, use proper decryption
        # For now, secrets are hashed (one-way), so this is a placeholder
        return "DECRYPTED_SECRET_PLACEHOLDER"
    
    async def audit_agent_activity(self, agent_id: str, activity: str, details: Dict[str, Any] = None):
        """Log agent activity for audit purposes"""
        details = details or {}
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': agent_id,
            'activity': activity,
            'details': details
        }
        
        self.audit_logger.info(f"ACTIVITY: {json.dumps(log_entry)}")
    
    async def check_resource_limits(self, agent_id: str, resource_type: str, requested_amount: float) -> bool:
        """Check if agent can use requested resources"""
        context = self.active_sessions.get(agent_id)
        if not context:
            return False
        
        limit = context.resource_limits.get(resource_type, float('inf'))
        current_usage = self.resource_usage.get(agent_id, {}).get(resource_type, 0)
        
        if current_usage + requested_amount > limit:
            self.audit_logger.warning(f"Resource limit exceeded: agent {agent_id} requesting {requested_amount} {resource_type}")
            return False
        
        return True
    
    async def update_resource_usage(self, agent_id: str, resource_type: str, amount: float):
        """Update resource usage tracking"""
        if agent_id not in self.resource_usage:
            self.resource_usage[agent_id] = {}
        
        self.resource_usage[agent_id][resource_type] = self.resource_usage[agent_id].get(resource_type, 0) + amount
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get comprehensive security report"""
        return {
            'active_sessions': len(self.active_sessions),
            'total_secrets': len(self.secrets_store),
            'active_api_keys': len(self.api_keys),
            'security_levels': {level.value: len([s for s in self.active_sessions.values() if s.security_level == level]) 
                              for level in SecurityLevel},
            'resource_usage': dict(self.resource_usage),
            'config': {k: v for k, v in self.security_config.items() if 'key' not in k.lower()}  # Exclude keys from report
        }


class SecureAPIWrapper:
    """
    Wrapper for external API calls that enforces security policies.
    
    Prevents agents from accessing APIs they shouldn't have access to
    and ensures API usage is properly logged and monitored.
    """
    
    def __init__(self, security_manager: AgentSecurityManager):
        self.security_manager = security_manager
        self.blocked_domains = [
            # Add domains that should be blocked
            "suspicious-site.com",
            "malware-domain.com"
        ]
    
    async def make_api_call(self, agent_id: str, url: str, method: str = "GET", 
                          data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Optional[Any]:
        """Make a secure API call on behalf of an agent"""
        
        # Check permissions
        if not await self.security_manager.check_permission(agent_id, Permission.API_CALLS):
            await self.security_manager.audit_agent_activity(
                agent_id, "api_call_blocked", {"reason": "insufficient_permissions", "url": url}
            )
            return None
        
        # Check domain restrictions
        from urllib.parse import urlparse
        domain = urlparse(url).netlify
        
        context = self.security_manager.active_sessions.get(agent_id)
        if context and context.network_restrictions:
            if domain not in context.network_restrictions:
                await self.security_manager.audit_agent_activity(
                    agent_id, "api_call_blocked", {"reason": "domain_restricted", "domain": domain}
                )
                return None
        
        # Check blocked domains
        if domain in self.blocked_domains:
            await self.security_manager.audit_agent_activity(
                agent_id, "api_call_blocked", {"reason": "domain_blocked", "domain": domain}
            )
            return None
        
        # Log the API call
        await self.security_manager.audit_agent_activity(
            agent_id, "api_call_made", {"url": url, "method": method}
        )
        
        # In a real implementation, this would make the actual HTTP request
        # For now, return a placeholder
        return {"status": "success", "data": "API_RESPONSE_PLACEHOLDER"}


# Global security manager instance
_security_manager = None

def get_security_manager() -> AgentSecurityManager:
    """Get the global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = AgentSecurityManager()
    return _security_manager

async def initialize_security_system():
    """Initialize the Kingdom security system"""
    manager = get_security_manager()
    print("🔒 Kingdom Security System initialized")
    return manager