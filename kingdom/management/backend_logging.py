"""
Centralized Logging Module for Kingdom Management Backend

This module provides unified logging for the Kingdom Management Backend (FastAPI server).
It supports both local file logging and cloud storage with structured JSON logs.

Key Features:
- Backend-specific log files with structured JSON format
- Environment-aware logging (local vs cloud deployment)
- Request/response logging with correlation IDs
- Automatic log rotation and cleanup
- Performance metrics and error tracking
- Integration with FastAPI middleware

Usage:
    from kingdom.management.backend_logging import get_backend_logger, log_request, log_response

    logger = get_backend_logger("local")
    logger.log_request("/api/chat", "POST", {"sender": "user123"})
    logger.log_response("/api/chat", 200, {"response": "success"})
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import Request, Response


class BackendLogger:
    """
    Centralized logging system for Kingdom Management Backend.

    This class provides unified logging for all backend operations including
    API requests, responses, agent interactions, and system events.
    """

    def __init__(self, environment: str = "local",
                 log_level: str = "INFO", max_logs_per_file: int = 2000):
        """
        Initialize the backend logger.

        Args:
            environment: "local" or "cloud"
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            max_logs_per_file: Maximum log entries per file before rotation
        """
        self.environment = environment
        self.log_level = log_level
        self.max_logs_per_file = max_logs_per_file

        # Setup logging directory based on environment
        self._setup_log_directory()

        # Initialize log file counter
        self.current_log_file = 0
        self.current_log_count = 0

        # Setup Python logging for internal operations
        self._setup_internal_logging()

        # Log initialization
        self.log("system", "BackendLogger initialized", {
            "environment": environment,
            "log_directory": str(self.log_directory),
            "max_logs_per_file": max_logs_per_file
        })

    def _setup_log_directory(self):
        """Setup the appropriate log directory based on environment."""
        if self.environment == "local":
            # Local development logging
            self.log_directory = Path("/Users/ed/King/B2/kingdom-backend-logs")
        elif self.environment == "cloud":
            # Cloud deployment - placeholder for cloud storage
            self.log_directory = Path("/tmp/kingdom-backend-logs")  # Fallback for now
            self._setup_cloud_logging()
        else:
            raise ValueError(f"Invalid environment: {self.environment}. Must be 'local' or 'cloud'")

        # Create directory if it doesn't exist
        self.log_directory.mkdir(parents=True, exist_ok=True)

    def _setup_cloud_logging(self):
        """
        Setup cloud logging (placeholder for future implementation).

        TODO: Implement cloud logging integration (AWS CloudWatch, Google Cloud Logging, etc.)
        """
        # Placeholder for cloud implementation
        self.cloud_bucket_name = "kingdom-backend-logs"  # Configurable
        self.cloud_credentials_path = os.getenv("BACKEND_CLOUD_CREDENTIALS_PATH")

        if not self.cloud_credentials_path:
            self.logger.warning("BACKEND_CLOUD_CREDENTIALS_PATH not set. Falling back to local logging.")
            self.environment = "local"
            self._setup_log_directory()
            return

        # TODO: Implement cloud client initialization
        # Example for AWS CloudWatch:
        # import boto3
        # self.cloud_client = boto3.client('logs', region_name='us-east-1')

        # Example for Google Cloud Logging:
        # from google.cloud import logging as cloud_logging
        # self.cloud_client = cloud_logging.Client()

        self.logger.info("Cloud logging setup placeholder - not yet implemented")

    def _setup_internal_logging(self):
        """Setup internal Python logging for the logger itself."""
        self.logger = logging.getLogger(f"BackendLogger.{self.environment}")
        self.logger.setLevel(getattr(logging, self.log_level))

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level))

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - Backend - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(console_handler)

    def _get_log_filename(self, log_type: str = "general") -> str:
        """Generate the current log filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"kingdom_backend_{log_type}_{timestamp}_{self.current_log_file:03d}.log"

    def _should_rotate_log(self) -> bool:
        """Check if log file should be rotated."""
        return self.current_log_count >= self.max_logs_per_file

    def _rotate_log_file(self, log_type: str = "general"):
        """Rotate to a new log file."""
        self.current_log_file += 1
        self.current_log_count = 0
        self.logger.info(f"Rotated backend log file to {self._get_log_filename(log_type)}")

    def log(self, operation: str, message: str, metadata: Optional[Dict[str, Any]] = None,
            log_level: str = "INFO", log_type: str = "general"):
        """
        Log a message with structured data.

        Args:
            operation: The operation being performed (e.g., "api_request", "agent_task")
            message: Human-readable message
            metadata: Optional structured data (dict, will be JSON serialized)
            log_level: Log level (DEBUG, INFO, WARNING, ERROR)
            log_type: Type of log (general, api, agent, system, error)
        """
        try:
            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "environment": self.environment,
                "component": "kingdom_backend",
                "operation": operation,
                "message": message,
                "log_level": log_level,
                "log_type": log_type,
                "metadata": metadata or {}
            }

            # Check if log rotation is needed
            if self._should_rotate_log():
                self._rotate_log_file(log_type)

            # Write to appropriate destination
            if self.environment == "local":
                self._write_to_file(log_entry, log_type)
            elif self.environment == "cloud":
                self._write_to_cloud(log_entry, log_type)

            # Update counter
            self.current_log_count += 1

            # Log to internal logger
            self.logger.info(f"{operation}: {message}")

        except Exception as e:
            # Fallback error logging
            print(f"❌ BackendLogger Error: {e}")
            print(f"   Failed to log: {operation} - {message}")
            import traceback
            traceback.print_exc()

    def log_request(self, endpoint: str, method: str, client_ip: str,
                   user_agent: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Log an API request.

        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            client_ip: Client IP address
            user_agent: User agent string
            metadata: Additional request metadata
        """
        request_metadata = {
            "endpoint": endpoint,
            "method": method,
            "client_ip": client_ip,
            "user_agent": user_agent,
            **(metadata or {})
        }

        self.log("api_request", f"{method} {endpoint} from {client_ip}",
                request_metadata, "INFO", "api")

    def log_response(self, endpoint: str, method: str, status_code: int,
                    response_time_ms: float, metadata: Optional[Dict[str, Any]] = None):
        """
        Log an API response.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            metadata: Additional response metadata
        """
        response_metadata = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            **(metadata or {})
        }

        log_level = "INFO" if status_code < 400 else "WARNING" if status_code < 500 else "ERROR"

        self.log("api_response", f"{method} {endpoint} -> {status_code} ({response_time_ms:.2f}ms)",
                response_metadata, log_level, "api")

    def log_agent_interaction(self, agent_id: str, operation: str, task_id: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None):
        """
        Log agent interaction.

        Args:
            agent_id: ID of the interacting agent
            operation: Operation performed (task_submitted, task_completed, etc.)
            task_id: Associated task ID if applicable
            metadata: Additional interaction metadata
        """
        interaction_metadata = {
            "agent_id": agent_id,
            "task_id": task_id,
            **(metadata or {})
        }

        self.log("agent_interaction", f"Agent {agent_id}: {operation}",
                interaction_metadata, "INFO", "agent")

    def log_system_event(self, event_type: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log system-level events.

        Args:
            event_type: Type of system event (startup, shutdown, error, etc.)
            message: Event description
            metadata: Additional event metadata
        """
        self.log("system_event", message, {
            "event_type": event_type,
            **(metadata or {})
        }, "INFO", "system")

    def log_error(self, operation: str, error: Exception, metadata: Optional[Dict[str, Any]] = None):
        """
        Log error events.

        Args:
            operation: Operation where error occurred
            error: Exception object
            metadata: Additional error metadata
        """
        error_metadata = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "operation": operation,
            **(metadata or {})
        }

        self.log("error", f"Error in {operation}: {str(error)}",
                error_metadata, "ERROR", "error")

    def _write_to_file(self, log_entry: Dict[str, Any], log_type: str):
        """Write log entry to local file."""
        log_file_path = self.log_directory / self._get_log_filename(log_type)

        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"❌ Failed to write to backend log file {log_file_path}: {e}")

    def _write_to_cloud(self, log_entry: Dict[str, Any], log_type: str):
        """
        Write log entry to cloud storage (placeholder).

        TODO: Implement actual cloud upload
        """
        # Placeholder implementation
        print(f"☁️ [Cloud Placeholder] Would upload backend log entry to {self.cloud_bucket_name}")
        print(f"   Type: {log_type}")
        print(f"   Entry: {json.dumps(log_entry, indent=2)}")

        # For now, also write to local file as fallback
        self._write_to_file(log_entry, log_type)

    def get_recent_logs(self, limit: int = 10, log_type: str = "general") -> list:
        """
        Get recent log entries for the backend.

        Args:
            limit: Number of recent entries to return
            log_type: Type of logs to retrieve

        Returns:
            List of recent log entries (newest first)
        """
        if self.environment != "local":
            self.logger.warning("get_recent_logs only supported for local environment")
            return []

        try:
            log_file_path = self.log_directory / self._get_log_filename(log_type)
            if not log_file_path.exists():
                return []

            logs = []
            with open(log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line.strip()))

            # Return most recent logs
            return logs[-limit:] if logs else []

        except Exception as e:
            self.logger.error(f"Failed to read recent backend logs: {e}")
            return []

    def cleanup_old_logs(self, days_to_keep: int = 7):
        """
        Clean up old log files.

        Args:
            days_to_keep: Number of days of logs to keep
        """
        if self.environment != "local":
            self.logger.warning("cleanup_old_logs only supported for local environment")
            return

        try:
            import time
            current_time = time.time()

            for log_file in self.log_directory.glob("kingdom_backend_*.log"):
                file_age_days = (current_time - log_file.stat().st_mtime) / (24 * 3600)

                if file_age_days > days_to_keep:
                    log_file.unlink()
                    self.logger.info(f"Cleaned up old backend log file: {log_file.name}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old backend logs: {e}")


# Global logger registry for easy access
_backend_logger_registry = {}


def get_backend_logger(environment: str = "local") -> BackendLogger:
    """
    Get or create a backend logger instance.

    Args:
        environment: "local" or "cloud"

    Returns:
        BackendLogger instance
    """
    key = f"backend_{environment}"

    if key not in _backend_logger_registry:
        _backend_logger_registry[key] = BackendLogger(environment)

    return _backend_logger_registry[key]


def cleanup_backend_loggers():
    """Cleanup all registered backend loggers."""
    for logger in _backend_logger_registry.values():
        try:
            logger.cleanup_old_logs()
        except Exception as e:
            print(f"Error cleaning up backend logger: {e}")

    _backend_logger_registry.clear()


# Convenience functions for common backend logging operations
def log_api_request(endpoint: str, method: str, client_ip: str,
                   user_agent: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                   environment: str = "local"):
    """Log an API request."""
    import sys
    print(f"🔍 DEBUG: log_api_request called for {method} {endpoint}", file=sys.stderr)
    try:
        logger = get_backend_logger(environment)
        print(f"🔍 DEBUG: Got logger: {logger}", file=sys.stderr)
        if logger:
            logger.log_request(endpoint, method, client_ip, user_agent, metadata)
            print(f"✅ DEBUG: log_request completed", file=sys.stderr)
        else:
            print(f"❌ DEBUG: Logger is None", file=sys.stderr)
    except Exception as e:
        print(f"❌ DEBUG: Exception in log_api_request: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


def log_api_response(endpoint: str, method: str, status_code: int, response_time_ms: float,
                    metadata: Optional[Dict[str, Any]] = None, environment: str = "local"):
    """Log an API response."""
    logger = get_backend_logger(environment)
    logger.log_response(endpoint, method, status_code, response_time_ms, metadata)


def log_agent_operation(agent_id: str, operation: str, task_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None, environment: str = "local"):
    """Log agent operation."""
    logger = get_backend_logger(environment)
    logger.log_agent_interaction(agent_id, operation, task_id, metadata)


def log_backend_error(operation: str, error: Exception, metadata: Optional[Dict[str, Any]] = None,
                     environment: str = "local"):
    """Log backend error."""
    logger = get_backend_logger(environment)
    logger.log_error(operation, error, metadata)


def log_system_event(event_type: str, message: str, metadata: Optional[Dict[str, Any]] = None,
                    environment: str = "local"):
    """Log system event."""
    logger = get_backend_logger(environment)
    logger.log_system_event(event_type, message, metadata)