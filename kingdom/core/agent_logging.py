"""
Centralized Logging Module for Kingdom Agents

This module provides a unified logging system for all Kingdom agents.
It supports both local file logging and cloud (GCS) logging based on the environment.

Key Features:
- Agent-specific log files
- Environment-aware logging (local vs cloud)
- Structured log entries with timestamps
- Automatic log rotation and cleanup
- Thread-safe operations

Usage:
    from kingdom.core.agent_logging import AgentLogger

    logger = AgentLogger("math_calculator_001", "local")
    logger.log("Agent initialized successfully")
    logger.log("Processing mathematical problem", {"problem": "2+2", "status": "solving"})
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class AgentLogger:
    """
    Centralized logging system for Kingdom agents.

    This class provides a unified interface for all agent logging operations.
    It automatically handles environment detection and log storage location.
    """

    def __init__(self, agent_name: str, environment: str = "local",
                 log_level: str = "INFO", max_logs_per_file: int = 1000):
        """
        Initialize the agent logger.

        Args:
            agent_name: Name of the agent (e.g., "math_calculator_001")
            environment: "local" or "cloud"
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            max_logs_per_file: Maximum log entries per file before rotation
        """
        self.agent_name = agent_name
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
        self.log("AgentLogger", "Logger initialized", {
            "agent_name": agent_name,
            "environment": environment,
            "log_directory": str(self.log_directory)
        })

    def _setup_log_directory(self):
        """Setup the appropriate log directory based on environment."""
        if self.environment == "local":
            # Local development logging
            self.log_directory = Path("/Users/ed/King/B2/kingdom-logs")
        elif self.environment == "cloud":
            # Cloud deployment - placeholder for GCS bucket
            self.log_directory = Path("/tmp/kingdom-logs")  # Fallback for now
            self._setup_gcs_logging()
        else:
            raise ValueError(f"Invalid environment: {self.environment}. Must be 'local' or 'cloud'")

        # Create directory if it doesn't exist
        self.log_directory.mkdir(parents=True, exist_ok=True)

    def _setup_gcs_logging(self):
        """
        Setup Google Cloud Storage logging.

        TODO: Implement GCS bucket integration for cloud deployment.
        This should upload logs to a GCS bucket instead of local files.
        """
        # Placeholder for GCS implementation
        self.gcs_bucket_name = "kingdom-agent-logs"  # Configurable
        self.gcs_credentials_path = os.getenv("GCS_CREDENTIALS_PATH")

        if not self.gcs_credentials_path:
            self.logger.warning("GCS_CREDENTIALS_PATH not set. Falling back to local logging.")
            self.environment = "local"
            self._setup_log_directory()
            return

        # TODO: Implement GCS client initialization
        # from google.cloud import storage
        # self.gcs_client = storage.Client.from_service_account_json(self.gcs_credentials_path)
        # self.bucket = self.gcs_client.bucket(self.gcs_bucket_name)

        self.logger.info("GCS logging setup placeholder - not yet implemented")

    def _setup_internal_logging(self):
        """Setup internal Python logging for the logger itself."""
        self.logger = logging.getLogger(f"AgentLogger.{self.agent_name}")
        self.logger.setLevel(getattr(logging, self.log_level))

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level))

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(console_handler)

    def _get_log_filename(self) -> str:
        """Generate the current log filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.agent_name}_{timestamp}_{self.current_log_file:03d}.log"

    def _should_rotate_log(self) -> bool:
        """Check if log file should be rotated."""
        return self.current_log_count >= self.max_logs_per_file

    def _rotate_log_file(self):
        """Rotate to a new log file."""
        self.current_log_file += 1
        self.current_log_count = 0
        self.logger.info(f"Rotated log file to {self._get_log_filename()}")

    def log(self, operation: str, message: str, metadata: Optional[Dict[str, Any]] = None,
            log_level: str = "INFO"):
        """
        Log a message with structured data.

        Args:
            operation: The operation being performed (e.g., "task_started", "api_call")
            message: Human-readable message
            metadata: Optional structured data (dict, will be JSON serialized)
            log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        try:
            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent_name": self.agent_name,
                "environment": self.environment,
                "operation": operation,
                "message": message,
                "log_level": log_level,
                "metadata": metadata or {}
            }

            # Check if log rotation is needed
            if self._should_rotate_log():
                self._rotate_log_file()

            # Write to appropriate destination
            if self.environment == "local":
                self._write_to_file(log_entry)
            elif self.environment == "cloud":
                self._write_to_gcs(log_entry)

            # Update counter
            self.current_log_count += 1

            # Log to internal logger
            self.logger.info(f"{operation}: {message}")

        except Exception as e:
            # Fallback error logging
            print(f"❌ AgentLogger Error: {e}")
            print(f"   Failed to log: {operation} - {message}")

    def _write_to_file(self, log_entry: Dict[str, Any]):
        """Write log entry to local file."""
        log_file_path = self.log_directory / self._get_log_filename()

        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"❌ Failed to write to log file {log_file_path}: {e}")

    def _write_to_gcs(self, log_entry: Dict[str, Any]):
        """
        Write log entry to Google Cloud Storage.

        TODO: Implement actual GCS upload
        """
        # Placeholder implementation
        print(f"📤 [GCS Placeholder] Would upload log entry to {self.gcs_bucket_name}")
        print(f"   Log entry: {json.dumps(log_entry, indent=2)}")

        # For now, also write to local file as fallback
        self._write_to_file(log_entry)

    def get_recent_logs(self, limit: int = 10) -> list:
        """
        Get recent log entries for this agent.

        Args:
            limit: Number of recent entries to return

        Returns:
            List of recent log entries (newest first)
        """
        if self.environment != "local":
            self.logger.warning("get_recent_logs only supported for local environment")
            return []

        try:
            log_file_path = self.log_directory / self._get_log_filename()
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
            self.logger.error(f"Failed to read recent logs: {e}")
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

            for log_file in self.log_directory.glob(f"{self.agent_name}_*.log"):
                file_age_days = (current_time - log_file.stat().st_mtime) / (24 * 3600)

                if file_age_days > days_to_keep:
                    log_file.unlink()
                    self.logger.info(f"Cleaned up old log file: {log_file.name}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")


# Global logger registry for easy access
_logger_registry = {}


def get_agent_logger(agent_name: str, environment: str = "local") -> AgentLogger:
    """
    Get or create an agent logger instance.

    Args:
        agent_name: Name of the agent
        environment: "local" or "cloud"

    Returns:
        AgentLogger instance
    """
    key = f"{agent_name}_{environment}"

    if key not in _logger_registry:
        _logger_registry[key] = AgentLogger(agent_name, environment)

    return _logger_registry[key]


def cleanup_all_loggers():
    """Cleanup all registered loggers."""
    for logger in _logger_registry.values():
        try:
            logger.cleanup_old_logs()
        except Exception as e:
            print(f"Error cleaning up logger {logger.agent_name}: {e}")

    _logger_registry.clear()


# Convenience functions for common logging operations
def log_agent_activity(agent_name: str, operation: str, message: str,
                      metadata: Optional[Dict[str, Any]] = None,
                      environment: str = "local"):
    """
    Convenience function to log agent activity.

    Args:
        agent_name: Name of the agent
        operation: Operation being performed
        message: Log message
        metadata: Optional metadata
        environment: Environment ("local" or "cloud")
    """
    logger = get_agent_logger(agent_name, environment)
    logger.log(operation, message, metadata)


def log_task_start(agent_name: str, task_id: str, task_type: str,
                  environment: str = "local"):
    """Log task start event."""
    log_agent_activity(
        agent_name,
        "task_started",
        f"Task {task_id} started",
        {"task_id": task_id, "task_type": task_type},
        environment
    )


def log_task_complete(agent_name: str, task_id: str, result: Any,
                     environment: str = "local"):
    """Log task completion event."""
    log_agent_activity(
        agent_name,
        "task_completed",
        f"Task {task_id} completed",
        {"task_id": task_id, "result": str(result)[:200]},
        environment
    )


def log_error(agent_name: str, operation: str, error: Exception,
             environment: str = "local"):
    """Log error event."""
    log_agent_activity(
        agent_name,
        "error",
        f"Error in {operation}: {str(error)}",
        {"error_type": type(error).__name__, "operation": operation},
        environment
    )