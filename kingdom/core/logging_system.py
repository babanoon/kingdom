#!/usr/bin/env python3
"""
Comprehensive Logging System for Kingdom Agents

This module provides structured logging, monitoring, and observability
for all agent activities in the Kingdom system.
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import traceback

class LogLevel(Enum):
    """Log levels for agent activities"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(Enum):
    """Categories of logs for organization"""
    SYSTEM = "system"              # System-level operations
    AGENT = "agent"                # Agent lifecycle and operations
    COMMUNICATION = "communication" # Inter-agent communication
    MEMORY = "memory"              # Memory operations
    SECURITY = "security"          # Security events
    TASK = "task"                  # Task execution
    ERROR = "error"                # Error and exception handling
    PERFORMANCE = "performance"    # Performance metrics

@dataclass
class LogEntry:
    """Standard log entry structure"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    agent_id: Optional[str]
    message: str
    details: Dict[str, Any]
    context: Dict[str, Any]
    trace_id: Optional[str] = None
    error_info: Optional[Dict[str, Any]] = None

class KingdomLogger:
    """
    Advanced logging system for Kingdom agents.
    
    Provides structured logging with multiple outputs, log rotation,
    performance monitoring, and distributed tracing capabilities.
    """
    
    def __init__(self, log_dir: str = "./kingdom/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log storage
        self.log_entries: List[LogEntry] = []
        self.max_memory_logs = 10000  # Keep last N logs in memory
        
        # File handlers for different categories
        self.file_handlers: Dict[LogCategory, logging.Logger] = {}
        self.setup_file_handlers()
        
        # Console handler
        self.console_logger = self.setup_console_logger()
        
        # Performance tracking
        self.performance_metrics: Dict[str, List[float]] = {}
        self.operation_timings: Dict[str, datetime] = {}
        
        # Error tracking
        self.error_counts: Dict[str, int] = {}
        self.last_errors: List[LogEntry] = []
        
        # Distributed tracing
        self.active_traces: Dict[str, Dict[str, Any]] = {}
        
        # Async logging queue
        self.log_queue = asyncio.Queue()
        self.logging_active = False
        
        print(f"📊 Kingdom Logging System initialized - logs dir: {self.log_dir}")
    
    def setup_file_handlers(self):
        """Setup file handlers for different log categories"""
        for category in LogCategory:
            logger = logging.getLogger(f"kingdom.{category.value}")
            logger.setLevel(logging.DEBUG)
            
            # File handler with rotation
            log_file = self.log_dir / f"{category.value}.log"
            handler = logging.FileHandler(str(log_file))
            
            # JSON formatter for structured logs
            formatter = self.JSONFormatter()
            handler.setFormatter(formatter)
            
            logger.addHandler(handler)
            self.file_handlers[category] = logger
    
    def setup_console_logger(self) -> logging.Logger:
        """Setup console logger for real-time monitoring"""
        logger = logging.getLogger("kingdom.console")
        logger.setLevel(logging.INFO)
        
        # Console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def start_logging(self):
        """Start async logging processor"""
        self.logging_active = True
        asyncio.create_task(self._process_log_queue())
        print("📊 Async logging processor started")
    
    async def stop_logging(self):
        """Stop async logging processor"""
        self.logging_active = False
        
        # Process remaining logs
        while not self.log_queue.empty():
            try:
                log_entry = self.log_queue.get_nowait()
                await self._write_log_entry(log_entry)
            except asyncio.QueueEmpty:
                break
        
        print("📊 Logging processor stopped")
    
    async def log(self, level: LogLevel, category: LogCategory, message: str,
                 agent_id: str = None, details: Dict[str, Any] = None,
                 context: Dict[str, Any] = None, trace_id: str = None,
                 error_info: Dict[str, Any] = None):
        """Log an entry asynchronously"""
        
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category,
            agent_id=agent_id,
            message=message,
            details=details or {},
            context=context or {},
            trace_id=trace_id,
            error_info=error_info
        )
        
        # Queue for async processing
        await self.log_queue.put(log_entry)
    
    async def _process_log_queue(self):
        """Process log queue asynchronously"""
        while self.logging_active:
            try:
                # Wait for log entry with timeout
                log_entry = await asyncio.wait_for(self.log_queue.get(), timeout=1.0)
                await self._write_log_entry(log_entry)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                # Log processor error to console
                print(f"❌ Error in log processor: {e}")
    
    async def _write_log_entry(self, entry: LogEntry):
        """Write log entry to appropriate destinations"""
        # Add to memory storage
        self.log_entries.append(entry)
        if len(self.log_entries) > self.max_memory_logs:
            self.log_entries.pop(0)
        
        # Write to file handler
        file_logger = self.file_handlers.get(entry.category)
        if file_logger:
            log_data = asdict(entry)
            # Convert datetime to string for JSON serialization
            log_data['timestamp'] = entry.timestamp.isoformat()
            file_logger.log(self._get_logging_level(entry.level), json.dumps(log_data))
        
        # Write to console for important messages
        if entry.level in [LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]:
            agent_str = f"[{entry.agent_id}] " if entry.agent_id else ""
            self.console_logger.log(
                self._get_logging_level(entry.level),
                f"{agent_str}{entry.message}"
            )
        
        # Track errors
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.error_counts[entry.category.value] = self.error_counts.get(entry.category.value, 0) + 1
            self.last_errors.append(entry)
            if len(self.last_errors) > 100:
                self.last_errors.pop(0)
    
    def _get_logging_level(self, level: LogLevel) -> int:
        """Convert LogLevel to logging module level"""
        mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        return mapping.get(level, logging.INFO)
    
    # Convenience methods for different log levels
    async def debug(self, category: LogCategory, message: str, agent_id: str = None, **kwargs):
        await self.log(LogLevel.DEBUG, category, message, agent_id, **kwargs)
    
    async def info(self, category: LogCategory, message: str, agent_id: str = None, **kwargs):
        await self.log(LogLevel.INFO, category, message, agent_id, **kwargs)
    
    async def warning(self, category: LogCategory, message: str, agent_id: str = None, **kwargs):
        await self.log(LogLevel.WARNING, category, message, agent_id, **kwargs)
    
    async def error(self, category: LogCategory, message: str, agent_id: str = None, 
                   exception: Exception = None, **kwargs):
        error_info = None
        if exception:
            error_info = {
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            }
        await self.log(LogLevel.ERROR, category, message, agent_id, error_info=error_info, **kwargs)
    
    async def critical(self, category: LogCategory, message: str, agent_id: str = None, **kwargs):
        await self.log(LogLevel.CRITICAL, category, message, agent_id, **kwargs)
    
    # Performance monitoring methods
    async def start_operation(self, operation_name: str, agent_id: str = None, trace_id: str = None):
        """Start timing an operation"""
        operation_key = f"{operation_name}_{agent_id}_{trace_id}"
        self.operation_timings[operation_key] = datetime.now()
        
        await self.debug(LogCategory.PERFORMANCE, f"Started operation: {operation_name}", 
                        agent_id, details={'operation': operation_name}, trace_id=trace_id)
    
    async def end_operation(self, operation_name: str, agent_id: str = None, 
                          trace_id: str = None, details: Dict[str, Any] = None):
        """End timing an operation"""
        operation_key = f"{operation_name}_{agent_id}_{trace_id}"
        start_time = self.operation_timings.get(operation_key)
        
        if start_time:
            duration = (datetime.now() - start_time).total_seconds()
            
            # Track performance metrics
            if operation_name not in self.performance_metrics:
                self.performance_metrics[operation_name] = []
            self.performance_metrics[operation_name].append(duration)
            
            # Keep only last 1000 measurements
            if len(self.performance_metrics[operation_name]) > 1000:
                self.performance_metrics[operation_name].pop(0)
            
            # Log completion
            log_details = details or {}
            log_details.update({
                'operation': operation_name,
                'duration_seconds': duration
            })
            
            await self.info(LogCategory.PERFORMANCE, f"Completed operation: {operation_name}", 
                          agent_id, details=log_details, trace_id=trace_id)
            
            # Clean up
            del self.operation_timings[operation_key]
        else:
            await self.warning(LogCategory.PERFORMANCE, f"End operation called without start: {operation_name}",
                             agent_id, trace_id=trace_id)
    
    # Distributed tracing methods
    def start_trace(self, trace_name: str, agent_id: str = None) -> str:
        """Start a distributed trace"""
        import uuid
        trace_id = str(uuid.uuid4())
        
        self.active_traces[trace_id] = {
            'name': trace_name,
            'agent_id': agent_id,
            'start_time': datetime.now(),
            'spans': []
        }
        
        return trace_id
    
    async def add_trace_span(self, trace_id: str, span_name: str, details: Dict[str, Any] = None):
        """Add a span to an active trace"""
        if trace_id in self.active_traces:
            span = {
                'name': span_name,
                'timestamp': datetime.now(),
                'details': details or {}
            }
            self.active_traces[trace_id]['spans'].append(span)
            
            await self.debug(LogCategory.SYSTEM, f"Trace span: {span_name}", 
                           details={'span': span}, trace_id=trace_id)
    
    async def end_trace(self, trace_id: str, result: str = "success"):
        """End a distributed trace"""
        if trace_id in self.active_traces:
            trace = self.active_traces[trace_id]
            trace['end_time'] = datetime.now()
            trace['duration'] = (trace['end_time'] - trace['start_time']).total_seconds()
            trace['result'] = result
            
            await self.info(LogCategory.SYSTEM, f"Trace completed: {trace['name']}", 
                          trace['agent_id'], details=trace, trace_id=trace_id)
            
            del self.active_traces[trace_id]
    
    # Query and analysis methods
    async def get_logs(self, level: LogLevel = None, category: LogCategory = None,
                      agent_id: str = None, since: datetime = None,
                      limit: int = 100) -> List[LogEntry]:
        """Query logs with filters"""
        filtered_logs = self.log_entries
        
        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]
        
        if category:
            filtered_logs = [log for log in filtered_logs if log.category == category]
        
        if agent_id:
            filtered_logs = [log for log in filtered_logs if log.agent_id == agent_id]
        
        if since:
            filtered_logs = [log for log in filtered_logs if log.timestamp > since]
        
        # Sort by timestamp (newest first) and limit
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered_logs[:limit]
    
    def get_performance_stats(self, operation_name: str = None) -> Dict[str, Any]:
        """Get performance statistics"""
        if operation_name:
            timings = self.performance_metrics.get(operation_name, [])
            if not timings:
                return {}
            
            return {
                'operation': operation_name,
                'count': len(timings),
                'avg_duration': sum(timings) / len(timings),
                'min_duration': min(timings),
                'max_duration': max(timings),
                'recent_avg': sum(timings[-10:]) / min(len(timings), 10)
            }
        else:
            # All operations
            stats = {}
            for op_name, timings in self.performance_metrics.items():
                stats[op_name] = {
                    'count': len(timings),
                    'avg_duration': sum(timings) / len(timings),
                    'min_duration': min(timings),
                    'max_duration': max(timings)
                }
            return stats
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'errors_by_category': dict(self.error_counts),
            'recent_errors': len([e for e in self.last_errors 
                                if e.timestamp > datetime.now() - timedelta(hours=24)]),
            'last_error_time': self.last_errors[-1].timestamp.isoformat() if self.last_errors else None
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        recent_logs = [log for log in self.log_entries 
                      if log.timestamp > datetime.now() - timedelta(hours=1)]
        
        error_logs = [log for log in recent_logs 
                     if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        return {
            'logs_in_last_hour': len(recent_logs),
            'errors_in_last_hour': len(error_logs),
            'error_rate': len(error_logs) / max(len(recent_logs), 1),
            'active_traces': len(self.active_traces),
            'performance_operations_tracked': len(self.performance_metrics),
            'memory_log_entries': len(self.log_entries),
            'logging_queue_size': self.log_queue.qsize()
        }
    
    class JSONFormatter(logging.Formatter):
        """JSON formatter for structured log files"""
        def format(self, record):
            # The record.msg should already be JSON from our log entries
            return record.msg


class AgentLoggerInterface:
    """
    Interface provided to agents for logging their activities.
    This wrapper provides agent-specific logging capabilities.
    """
    
    def __init__(self, agent_id: str, kingdom_logger: KingdomLogger):
        self.agent_id = agent_id
        self.logger = kingdom_logger
        self.active_operations: Dict[str, datetime] = {}
    
    async def debug(self, message: str, category: LogCategory = LogCategory.AGENT, **kwargs):
        await self.logger.debug(category, message, self.agent_id, **kwargs)
    
    async def info(self, message: str, category: LogCategory = LogCategory.AGENT, **kwargs):
        await self.logger.info(category, message, self.agent_id, **kwargs)
    
    async def warning(self, message: str, category: LogCategory = LogCategory.AGENT, **kwargs):
        await self.logger.warning(category, message, self.agent_id, **kwargs)
    
    async def error(self, message: str, exception: Exception = None, 
                   category: LogCategory = LogCategory.ERROR, **kwargs):
        await self.logger.error(category, message, self.agent_id, exception, **kwargs)
    
    async def critical(self, message: str, category: LogCategory = LogCategory.ERROR, **kwargs):
        await self.logger.critical(category, message, self.agent_id, **kwargs)
    
    async def log_task_start(self, task_id: str, task_data: Dict[str, Any]):
        """Log task execution start"""
        await self.logger.start_operation(f"task_{task_id}", self.agent_id)
        await self.info(f"Started task: {task_id}", LogCategory.TASK, 
                       details={'task_id': task_id, 'task_data': task_data})
    
    async def log_task_complete(self, task_id: str, result: Any, duration: float = None):
        """Log task execution completion"""
        await self.logger.end_operation(f"task_{task_id}", self.agent_id,
                                       details={'task_id': task_id, 'result': str(result)})
        await self.info(f"Completed task: {task_id}", LogCategory.TASK,
                       details={'task_id': task_id, 'duration': duration})
    
    async def log_communication(self, message_type: str, recipient: str = None, sender: str = None):
        """Log communication events"""
        await self.info(f"Communication: {message_type}", LogCategory.COMMUNICATION,
                       details={'type': message_type, 'recipient': recipient, 'sender': sender})
    
    async def log_memory_operation(self, operation: str, details: Dict[str, Any] = None):
        """Log memory operations"""
        await self.info(f"Memory operation: {operation}", LogCategory.MEMORY, details=details)
    
    def start_trace(self, trace_name: str) -> str:
        """Start a trace for this agent"""
        return self.logger.start_trace(trace_name, self.agent_id)
    
    async def add_span(self, trace_id: str, span_name: str, details: Dict[str, Any] = None):
        """Add span to trace"""
        await self.logger.add_trace_span(trace_id, span_name, details)
    
    async def end_trace(self, trace_id: str, result: str = "success"):
        """End trace"""
        await self.logger.end_trace(trace_id, result)


# Global logger instance
_kingdom_logger = None

def get_kingdom_logger() -> KingdomLogger:
    """Get the global Kingdom logger instance"""
    global _kingdom_logger
    if _kingdom_logger is None:
        _kingdom_logger = KingdomLogger()
    return _kingdom_logger

async def initialize_logging_system():
    """Initialize the Kingdom logging system"""
    logger = get_kingdom_logger()
    await logger.start_logging()
    print("📊 Kingdom Logging System initialized and started")
    return logger