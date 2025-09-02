#!/usr/bin/env python3
"""
Kingdom Agent Service

A service infrastructure for running multiple agents concurrently with
task queues, database pooling, and inter-agent communication.
"""

import asyncio
import json
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor

class ServiceStatus(Enum):
    """Service lifecycle status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class TaskMessage:
    """Standard task message format"""
    task_id: str
    agent_id: Optional[str]  # None means any available agent
    task_type: str
    payload: Dict[str, Any]
    priority: int = 5
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass 
class AgentStatus:
    """Agent status tracking"""
    agent_id: str
    agent_type: str
    status: str  # idle, busy, error
    last_task: Optional[str]
    task_count: int
    uptime: datetime
    
class TaskQueue:
    """Simple in-memory task queue for agent communication"""
    
    def __init__(self):
        self.tasks = asyncio.Queue()
        self.completed_tasks = {}
        self.failed_tasks = {}
        
    async def put_task(self, task: TaskMessage):
        """Add task to queue"""
        await self.tasks.put(task)
        logging.info(f"Task queued: {task.task_id} ({task.task_type})")
    
    async def get_task(self, timeout: float = 1.0) -> Optional[TaskMessage]:
        """Get next task from queue"""
        try:
            task = await asyncio.wait_for(self.tasks.get(), timeout=timeout)
            return task
        except asyncio.TimeoutError:
            return None
    
    async def complete_task(self, task_id: str, result: Any):
        """Mark task as completed"""
        self.completed_tasks[task_id] = {
            'result': result,
            'completed_at': datetime.now()
        }
    
    async def fail_task(self, task_id: str, error: str):
        """Mark task as failed"""
        self.failed_tasks[task_id] = {
            'error': error,
            'failed_at': datetime.now()
        }
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        return {
            'pending': self.tasks.qsize(),
            'completed': len(self.completed_tasks),
            'failed': len(self.failed_tasks)
        }

class A2AMessageBus:
    """Agent-to-Agent message bus for inter-agent communication"""
    
    def __init__(self):
        self.subscribers = {}  # agent_id -> queue
        self.message_history = []
        
    async def subscribe(self, agent_id: str):
        """Subscribe agent to message bus"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = asyncio.Queue()
            logging.info(f"Agent {agent_id} subscribed to A2A message bus")
    
    async def unsubscribe(self, agent_id: str):
        """Unsubscribe agent from message bus"""
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]
            logging.info(f"Agent {agent_id} unsubscribed from A2A message bus")
    
    async def send_message(self, sender_id: str, recipient_id: str, message: Dict[str, Any]):
        """Send message between agents"""
        message_envelope = {
            'message_id': f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            'sender': sender_id,
            'recipient': recipient_id,
            'payload': message,
            'timestamp': datetime.now().isoformat()
        }

        logging.info(f"🔍 DEBUG A2A: Sending message {sender_id} -> {recipient_id}")
        logging.info(f"🔍 DEBUG A2A: Subscribers: {list(self.subscribers.keys())}")
        logging.info(f"🔍 DEBUG A2A: Recipient in subscribers: {recipient_id in self.subscribers}")
        logging.info(f"🔍 DEBUG A2A: Message payload keys: {list(message.keys()) if message else 'None'}")
        print(f"🔍 DEBUG A2A: Sending message {sender_id} -> {recipient_id}")
        print(f"🔍 DEBUG A2A: Subscribers: {list(self.subscribers.keys())}")
        print(f"🔍 DEBUG A2A: Recipient in subscribers: {recipient_id in self.subscribers}")
        print(f"🔍 DEBUG A2A: Message payload keys: {list(message.keys()) if message else 'None'}")

        if recipient_id in self.subscribers:
            await self.subscribers[recipient_id].put(message_envelope)
            self.message_history.append(message_envelope)
            logging.info(f"A2A message sent: {sender_id} -> {recipient_id}")
            print(f"✅ DEBUG A2A: Message queued successfully for {recipient_id}")
            print(f"🔍 DEBUG A2A: Queue size after send: {self.subscribers[recipient_id].qsize()}")
        else:
            logging.warning(f"Recipient {recipient_id} not subscribed to message bus")
            print(f"❌ DEBUG A2A: Recipient {recipient_id} not subscribed!")
    
    async def get_message(self, agent_id: str, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Get message for specific agent"""
        if agent_id not in self.subscribers:
            return None
        
        try:
            message = await asyncio.wait_for(
                self.subscribers[agent_id].get(), 
                timeout=timeout
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    def get_message_stats(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        return {
            'subscribers': len(self.subscribers),
            'total_messages': len(self.message_history),
            'subscriber_ids': list(self.subscribers.keys())
        }

class ServiceAgent:
    """
    Base class for agents that run as part of the Kingdom service.
    Much simpler than the full BaseAgent - focused on service integration.
    """
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = "created"
        
        # Service dependencies (injected during initialization)
        self.task_queue = None
        self.a2a_bus = None
        self.db_pool = None
        
        # Agent state
        self.task_count = 0
        self.running = False
        self.current_task = None
        
        # Logging
        self.logger = logging.getLogger(f"agent.{self.agent_id}")
    
    async def initialize_for_service(self, task_queue, a2a_bus, db_pool):
        """Initialize agent with service dependencies"""
        self.task_queue = task_queue
        self.a2a_bus = a2a_bus
        self.db_pool = db_pool
        
        # Subscribe to A2A message bus
        await self.a2a_bus.subscribe(self.agent_id)
        
        self.status = "initialized"
        self.logger.info(f"Agent {self.agent_id} initialized for service")
    
    async def run_service_loop(self):
        """Main service loop - continuously process tasks"""
        self.running = True
        self.status = "idle"
        
        self.logger.info(f"Agent {self.agent_id} starting service loop")
        
        while self.running:
            try:
                # Check for tasks
                task = await self.task_queue.get_task(timeout=1.0)
                if task:
                    await self._process_task(task)
                
                # Check for A2A messages  
                message = await self.a2a_bus.get_message(self.agent_id, timeout=0.1)
                if message:
                    await self._process_a2a_message(message)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in service loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_task(self, task):
        """Process a task from the queue"""
        # Check if task is for this agent specifically
        if task.agent_id and task.agent_id != self.agent_id:
            # Put task back in queue for correct agent
            await self.task_queue.put_task(task)
            return
        
        self.current_task = task.task_id
        self.status = "busy"
        self.task_count += 1
        
        self.logger.info(f"Processing task: {task.task_id} ({task.task_type})")
        
        try:
            # Route to appropriate handler
            result = await self._handle_task(task)
            
            # Mark task as completed
            await self.task_queue.complete_task(task.task_id, result)
            self.logger.info(f"Task completed: {task.task_id}")
            
        except Exception as e:
            # Mark task as failed
            await self.task_queue.fail_task(task.task_id, str(e))
            self.logger.error(f"Task failed: {task.task_id} - {e}")
        
        finally:
            self.current_task = None
            self.status = "idle"
    
    async def _handle_task(self, task) -> Any:
        """Handle specific task - to be overridden by subclasses"""
        return {"message": "Task processed by base ServiceAgent"}
    
    async def _process_a2a_message(self, message):
        """Process A2A message"""
        self.logger.info(f"Received A2A message from {message['sender']}: {message['message_id']}")
        
        # Route to handler
        await self._handle_a2a_message(message)
    
    async def _handle_a2a_message(self, message):
        """Handle A2A message - to be overridden by subclasses"""
        pass
    
    async def send_a2a_message(self, recipient_id: str, payload: Dict[str, Any]):
        """Send A2A message to another agent"""
        await self.a2a_bus.send_message(self.agent_id, recipient_id, payload)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'status': self.status,
            'task_count': self.task_count,
            'current_task': self.current_task
        }
    
    async def stop(self):
        """Stop the agent"""
        self.running = False
        await self.a2a_bus.unsubscribe(self.agent_id)
        self.status = "stopped"
        self.logger.info(f"Agent {self.agent_id} stopped")

class DatabasePool:
    """Database connection pool for agents"""
    
    def __init__(self, db_config: Dict[str, Any], pool_size: int = 10):
        self.db_config = db_config
        self.pool_size = pool_size
        self.connections = asyncio.Queue(maxsize=pool_size)
        self.stats = {'connections_created': 0, 'connections_used': 0}
        
    async def initialize(self):
        """Initialize connection pool"""
        import psycopg2
        for _ in range(self.pool_size):
            try:
                conn = psycopg2.connect(**self.db_config)
                await self.connections.put(conn)
                self.stats['connections_created'] += 1
            except Exception as e:
                logging.error(f"Failed to create database connection: {e}")
    
    async def get_connection(self):
        """Get connection from pool"""
        conn = await self.connections.get()
        self.stats['connections_used'] += 1
        return conn
    
    async def return_connection(self, conn):
        """Return connection to pool"""
        await self.connections.put(conn)
    
    async def close_all(self):
        """Close all connections"""
        while not self.connections.empty():
            conn = await self.connections.get()
            conn.close()

class KingdomAgentService:
    """
    Main service for running multiple Kingdom agents concurrently.
    
    Provides task queuing, A2A communication, database pooling, and
    service management for scalable agent deployment.
    """
    
    def __init__(self, config_path: str = "./kingdom/service/service_config.json"):
        self.config = self._load_config(config_path)
        self.status = ServiceStatus.STOPPED
        
        # Core service components
        self.task_queue = TaskQueue()
        self.a2a_bus = A2AMessageBus()
        self.db_pool = None
        
        # Agent management
        self.agents = {}  # agent_id -> agent_instance
        self.agent_tasks = {}  # agent_id -> current_task
        self.agent_stats = {}  # agent_id -> AgentStatus
        
        # Service management
        self.executor = ThreadPoolExecutor(max_workers=self.config.get('max_workers', 20))
        self.shutdown_event = asyncio.Event()
        
        # Logging
        self._setup_logging()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load service configuration"""
        default_config = {
            "service_name": "Kingdom Agent Service",
            "max_workers": 20,
            "database": {
                "host": "localhost",
                "port": 9876,
                "database": "general2613", 
                "user": "kadmin",
                "password": "securepasswordkossher123"
            },
            "db_pool_size": 10,
            "agent_types": ["tester1", "tester2"],
            "agents_per_type": 2,
            "task_timeout": 300,
            "log_level": "INFO"
        }
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
        except FileNotFoundError:
            logging.warning(f"Config file not found: {config_path}, using defaults")
            return default_config
    
    def _setup_logging(self):
        """Setup service logging"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('./kingdom/logs/agent_service.log')
            ]
        )
        
    async def start_service(self):
        """Start the agent service"""
        if self.status != ServiceStatus.STOPPED:
            logging.warning("Service already running")
            return
            
        logging.info("🚀 Starting Kingdom Agent Service")
        self.status = ServiceStatus.STARTING
        
        try:
            # Initialize database pool
            self.db_pool = DatabasePool(self.config['database'], self.config['db_pool_size'])
            await self.db_pool.initialize()
            
            # Start agent instances
            await self._start_agents()
            
            # Start service monitoring
            asyncio.create_task(self._service_monitor())
            
            self.status = ServiceStatus.RUNNING
            logging.info("✅ Kingdom Agent Service started successfully")
            
        except Exception as e:
            self.status = ServiceStatus.ERROR
            logging.error(f"❌ Failed to start service: {e}")
            raise
    
    async def _start_agents(self):
        """Start configured agent instances"""
        from ..agents.tester_agents import TesterAgent1, TesterAgent2
        from ..agents.general_receiver.agent import GeneralReceiverAgent
        from ..agents.math_calculator.agent import MathCalculatorAgent
        
        agent_classes = {
            'tester1': TesterAgent1,
            'tester2': TesterAgent2,
            'general_receiver': GeneralReceiverAgent,
            'math_calculator': MathCalculatorAgent
        }
        
        for agent_type in self.config['agent_types']:
            agents_count = self.config['agents_per_type']
            
            if agent_type not in agent_classes:
                logging.warning(f"Unknown agent type: {agent_type}")
                continue
                
            for i in range(agents_count):
                agent_id = f"{agent_type}_{i+1:03d}"
                
                try:
                    # Create agent instance
                    agent_class = agent_classes[agent_type]
                    agent = agent_class(agent_id, agent_type)
                    
                    # Initialize agent with service dependencies
                    await agent.initialize_for_service(
                        task_queue=self.task_queue,
                        a2a_bus=self.a2a_bus,
                        db_pool=self.db_pool
                    )
                    
                    # Start agent
                    asyncio.create_task(agent.run_service_loop())
                    
                    # Register agent
                    self.agents[agent_id] = agent
                    self.agent_stats[agent_id] = AgentStatus(
                        agent_id=agent_id,
                        agent_type=agent_type,
                        status="idle",
                        last_task=None,
                        task_count=0,
                        uptime=datetime.now()
                    )
                    
                    logging.info(f"Started agent: {agent_id}")
                    
                except Exception as e:
                    logging.error(f"Failed to start agent {agent_id}: {e}")
    
    async def _service_monitor(self):
        """Monitor service health and agent status"""
        while self.status == ServiceStatus.RUNNING:
            try:
                # Update agent stats
                for agent_id, agent in self.agents.items():
                    if hasattr(agent, 'get_status'):
                        status_info = await agent.get_status()
                        if agent_id in self.agent_stats:
                            self.agent_stats[agent_id].status = status_info.get('status', 'unknown')
                            self.agent_stats[agent_id].task_count = status_info.get('task_count', 0)
                
                # Log service status periodically
                if datetime.now().second == 0:  # Every minute
                    await self._log_service_status()
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logging.error(f"Error in service monitor: {e}")
                await asyncio.sleep(5)
    
    async def _log_service_status(self):
        """Log current service status"""
        task_stats = self.task_queue.get_stats()
        message_stats = self.a2a_bus.get_message_stats()
        
        active_agents = len([a for a in self.agent_stats.values() if a.status != 'error'])
        
        logging.info(
            f"Service Status - Agents: {active_agents}/{len(self.agents)}, "
            f"Tasks: {task_stats['pending']} pending, {task_stats['completed']} completed, "
            f"Messages: {message_stats['total_messages']} total"
        )

    async def submit_task(self, task_type: str, payload: Dict[str, Any],
                         agent_id: Optional[str] = None, priority: int = 5) -> str:
        """Submit task to the service"""
        # Auto-route tasks to appropriate agent types if no specific agent_id provided
        if agent_id is None:
            agent_id = self._route_task_to_agent(task_type, payload)

        task = TaskMessage(
            task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            agent_id=agent_id,
            task_type=task_type,
            payload=payload,
            priority=priority
        )

        await self.task_queue.put_task(task)
        logging.info(f"Task submitted: {task.task_id} ({task_type}) -> {agent_id}")
        return task.task_id

    def _route_task_to_agent(self, task_type: str, payload: Dict[str, Any]) -> str:
        """Route task to appropriate agent based on task type"""
        # Define task routing rules
        task_routing = {
            'process_chat_message': 'general_receiver',
            'solve_math_problem': 'math_calculator',
            'db_insert': 'tester1',
            'db_read': 'tester1',
            'db_update': 'tester1',
            'db_delete': 'tester1',
            'test_a2a_communication': 'tester2',
            'send_broadcast_test': 'tester2',
            'validate_communication': 'tester2'
        }

        # Get target agent type
        target_type = task_routing.get(task_type, 'tester1')  # Default to tester1

        # Find available agent of the target type
        available_agents = []
        for agent_id, stats in self.agent_stats.items():
            if stats.agent_type == target_type and stats.status == 'idle':
                available_agents.append(agent_id)

        if available_agents:
            # Return first available agent (could implement load balancing later)
            return available_agents[0]
        else:
            # If no idle agents, return first agent of that type
            for agent_id, stats in self.agent_stats.items():
                if stats.agent_type == target_type:
                    return agent_id

        # Fallback to any available agent
        if self.agent_stats:
            return list(self.agent_stats.keys())[0]

        raise ValueError(f"No agents available for task type: {task_type}")

    async def wait_for_task_completion(self, task_id: str, timeout: float = 60.0) -> Optional[Any]:
        """Wait for a task to complete and return its result"""
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < timeout:
            # Check if task completed successfully
            if task_id in self.task_queue.completed_tasks:
                result = self.task_queue.completed_tasks[task_id]['result']
                logging.info(f"Task {task_id} completed successfully")
                return result

            # Check if task failed
            if task_id in self.task_queue.failed_tasks:
                error = self.task_queue.failed_tasks[task_id]['error']
                logging.error(f"Task {task_id} failed: {error}")
                raise Exception(f"Task failed: {error}")

            # Nudge agents' service loops by yielding frequently
            await asyncio.sleep(0.05)

        # Timeout
        logging.warning(f"Task {task_id} timed out after {timeout} seconds")
        raise Exception(f"Task {task_id} timed out after {timeout} seconds")
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        return {
            'service_status': self.status.value,
            'agents': {
                agent_id: {
                    'type': stats.agent_type,
                    'status': stats.status,
                    'task_count': stats.task_count,
                    'uptime_seconds': (datetime.now() - stats.uptime).total_seconds()
                } 
                for agent_id, stats in self.agent_stats.items()
            },
            'task_queue': self.task_queue.get_stats(),
            'a2a_messages': self.a2a_bus.get_message_stats(),
            'database_pool': {
                'pool_size': self.config['db_pool_size'],
                'connections_created': self.db_pool.stats['connections_created'] if self.db_pool else 0
            }
        }
    
    async def stop_service(self):
        """Stop the agent service gracefully"""
        logging.info("🛑 Stopping Kingdom Agent Service")
        self.status = ServiceStatus.STOPPING
        
        # Stop all agents
        for agent_id, agent in self.agents.items():
            try:
                if hasattr(agent, 'stop'):
                    await agent.stop()
                logging.info(f"Stopped agent: {agent_id}")
            except Exception as e:
                logging.error(f"Error stopping agent {agent_id}: {e}")
        
        # Close database pool
        if self.db_pool:
            await self.db_pool.close_all()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.status = ServiceStatus.STOPPED
        logging.info("✅ Kingdom Agent Service stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            logging.info(f"Received signal {sig}, shutting down...")
            asyncio.create_task(self.stop_service())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

# Service runner functions
async def run_service():
    """Run the Kingdom Agent Service"""
    service = KingdomAgentService()
    service.setup_signal_handlers()
    
    try:
        await service.start_service()
        
        # Keep service running
        while service.status == ServiceStatus.RUNNING:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
    finally:
        await service.stop_service()

if __name__ == "__main__":
    asyncio.run(run_service())