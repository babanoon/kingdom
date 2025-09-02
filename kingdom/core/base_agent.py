#!/usr/bin/env python3
"""
Base Agent Framework for the Kingdom Project (Deos System)

This module defines the core Agent class that all specialized agents inherit from.
Agents are complete AI entities with GenAI brains and code execution capabilities.
"""

import uuid
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum

# Import the brain and hands systems
from .genai_brain import GenAIBrain, create_agent_brain, ThinkingMode, GenAIProvider
from .agent_hands import AgentHands, ExecutionEnvironment, ExecutionResult
from .agent_logging import get_agent_logger, log_task_start, log_task_complete, log_error

class AgentStatus(Enum):
    """Agent lifecycle status"""
    CREATED = "created"
    INITIALIZING = "initializing"  
    READY = "ready"
    WORKING = "working"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"

class AgentType(Enum):
    """Categories of agents in the system"""
    ORCHESTRATOR = "orchestrator"      # Deos itself
    PERSONAL = "personal"              # Personal life agents
    SOCIAL = "social"                  # Friend/conversation agents  
    WORK = "work"                      # Work project agents
    SUB_AGENT = "sub_agent"            # Reusable task-specific agents
    UTILITY = "utility"                # System utility agents

class MessageType(Enum):
    """Types of inter-agent messages"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    INFORMATION = "information"
    COMMAND = "command"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"

@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication"""
    id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = 5  # 1=highest, 10=lowest
    requires_response: bool = False
    conversation_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'sender_id': self.sender_id, 
            'recipient_id': self.recipient_id,
            'message_type': self.message_type.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority,
            'requires_response': self.requires_response,
            'conversation_id': self.conversation_id
        }

@dataclass
class AgentCapability:
    """Defines what an agent can do"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required_permissions: List[str] = None

@dataclass
class AgentConfig:
    """Configuration for agent initialization"""
    agent_id: str
    name: str
    agent_type: AgentType
    description: str
    capabilities: List[AgentCapability]
    memory_config: Dict[str, Any]
    security_level: str = "standard"
    max_concurrent_tasks: int = 3
    communication_channels: List[str] = None
    reports_to: Optional[str] = None  # Agent ID this reports to
    environment: str = "local"  # "local" or "cloud" for logging
    # New GenAI and execution configuration
    personality_key: str = None  # Key for predefined personality
    genai_provider: GenAIProvider = GenAIProvider.OPENAI
    specialized_hands: str = None  # Type of specialized hands (e.g., "data_science", "developer")
    working_directory: str = None

class BaseAgent(ABC):
    """
    Base class for all agents in the Kingdom system.
    
    Every agent inherits from this class and implements the required abstract methods.
    Provides common functionality for communication, memory, logging, and lifecycle management.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = config.agent_id
        self.name = config.name
        self.agent_type = config.agent_type
        self.status = AgentStatus.CREATED
        self.creation_time = datetime.now()
        self.last_activity = datetime.now()
        
        # 🧠 Brain - GenAI thinking capabilities
        self.brain: GenAIBrain = None
        
        # ✋ Hands - Code execution capabilities  
        self.hands: AgentHands = None
        
        # 👂 Ears - Communication input
        self.message_queue = asyncio.Queue()
        self.active_conversations = {}
        self.communication_handlers = {}
        
        # 👅 Tongue - Communication output (handled by communication system)
        self.communication_system = None
        
        # 👀 Eyes - Self-assessment and monitoring
        self.performance_metrics = {}
        self.self_assessment_history = []
        
        # 🦵 Legs - Environment and deployment (managed by system)
        self.execution_environment = None
        
        # 🦷 Teeth - Security (injected by security system)
        self.security_context = None
        
        # Task management
        self.active_tasks = {}
        self.task_history = []
        self.max_concurrent_tasks = config.max_concurrent_tasks
        
        # Memory and logging will be injected by the system
        self.memory_manager = None

        # Setup centralized logging system
        self.environment = config.environment or "local"  # Add environment to config if not exists
        self.agent_logger = get_agent_logger(self.agent_id, self.environment)

        # Keep compatibility with existing logger interface
        self.logger = logging.getLogger(f"agent.{self.name}")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} ({self.agent_id}) - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Sub-agents this agent manages (inheritance system)
        self.sub_agents = {}
        self.parent_agent = None
        
        # Agent this reports to (if any)
        self.supervisor = config.reports_to
        
        # Specialization components (data, prompts, code libraries, queries)
        self.specialized_data = {}
        self.custom_prompts = {}
        self.code_libraries = {}
        self.custom_queries = {}
        self.workflow_scripts = {}
        
    def log_activity(self, operation: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log agent activity using the centralized logging system"""
        self.agent_logger.log(operation, message, metadata)

    def log_task_start(self, task_id: str, task_type: str):
        """Log task start event"""
        log_task_start(self.agent_id, task_id, task_type, self.environment)

    def log_task_complete(self, task_id: str, result: Any):
        """Log task completion event"""
        log_task_complete(self.agent_id, task_id, result, self.environment)

    def log_error(self, operation: str, error: Exception):
        """Log error event"""
        log_error(self.agent_id, operation, error, self.environment)
    
    async def initialize(self, memory_manager=None, communication_system=None, security_context=None):
        """Initialize the agent with system dependencies"""
        self.status = AgentStatus.INITIALIZING
        self.logger.info(f"Initializing agent {self.name}")
        
        # Inject system dependencies
        self.memory_manager = memory_manager
        self.communication_system = communication_system
        self.security_context = security_context
        
        # Initialize 🧠 Brain (GenAI capabilities)
        await self._initialize_brain()
        
        # Initialize ✋ Hands (Code execution capabilities)
        await self._initialize_hands()
        
        # Load specialization components
        await self._load_specialization_components()
        
        # Initialize inherited capabilities from parent
        await self._inherit_parent_capabilities()
        
        # Agent-specific initialization
        await self.on_initialize()
        
        # Initialize 👀 Eyes (Self-assessment)
        await self._initialize_self_assessment()
        
        self.status = AgentStatus.READY
        self.logger.info(f"Agent {self.name} fully initialized with brain, hands, and specialization")
    
    async def _initialize_brain(self):
        """Initialize the GenAI brain for this agent"""
        try:
            if self.config.personality_key:
                self.brain = create_agent_brain(
                    self.agent_id, 
                    self.config.personality_key,
                    self.config.genai_provider
                )
            else:
                # Create generic brain
                from .genai_brain import AgentPersonality
                generic_personality = AgentPersonality(
                    name=self.name,
                    role="General AI Assistant",
                    personality_traits=["helpful", "analytical", "precise"],
                    expertise_areas=["general assistance"],
                    communication_style="clear and professional",
                    preferred_thinking_mode=ThinkingMode.ANALYTICAL,
                    system_prompt_template="You are {name}, a helpful AI assistant.",
                    temperature=0.7
                )
                self.brain = GenAIBrain(self.agent_id, generic_personality, self.config.genai_provider)
            
            self.logger.info(f"🧠 Brain initialized for {self.name}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize brain: {e}")
            raise
    
    async def _initialize_hands(self):
        """Initialize the code execution hands for this agent"""
        try:
            working_dir = self.config.working_directory or f"./kingdom/agents/{self.agent_id}/workspace"
            
            # Create specialized hands if specified
            if self.config.specialized_hands == "data_science":
                from .agent_hands import DataScienceHands
                self.hands = DataScienceHands(self.agent_id, working_dir)
            elif self.config.specialized_hands == "developer":
                from .agent_hands import DeveloperHands
                self.hands = DeveloperHands(self.agent_id, working_dir)
            else:
                # Generic hands
                self.hands = AgentHands(self.agent_id, working_dir)
            
            self.logger.info(f"✋ Hands initialized for {self.name}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize hands: {e}")
            raise
    
    async def _load_specialization_components(self):
        """Load agent's specialized data, prompts, code, and queries"""
        # This would load from files or databases
        # For now, placeholder implementation
        self.logger.info(f"📚 Loading specialization components for {self.name}")
        
        # Sub-classes can override this to load their specific components
        await self.load_custom_components()
    
    async def _inherit_parent_capabilities(self):
        """Inherit capabilities from parent agent"""
        if self.parent_agent:
            self.logger.info(f"👨‍👩‍👧‍👦 Inheriting capabilities from parent {self.parent_agent.name}")
            
            # Inherit specialized components
            self.specialized_data.update(self.parent_agent.specialized_data)
            self.custom_prompts.update(self.parent_agent.custom_prompts)
            self.code_libraries.update(self.parent_agent.code_libraries)
            self.custom_queries.update(self.parent_agent.custom_queries)
            self.workflow_scripts.update(self.parent_agent.workflow_scripts)
            
            # Child agents can override or extend inherited capabilities
    
    async def _initialize_self_assessment(self):
        """Initialize self-assessment and monitoring capabilities"""
        self.performance_metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'average_task_time': 0.0,
            'brain_api_calls': 0,
            'hands_executions': 0,
            'self_assessments': 0
        }
        self.logger.info(f"👀 Self-assessment initialized for {self.name}")
    
    @abstractmethod
    async def load_custom_components(self):
        """Load agent-specific components - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def on_initialize(self):
        """Agent-specific initialization logic - must be implemented by subclasses"""
        pass
    
    async def start(self):
        """Start the agent's main processing loop"""
        if self.status != AgentStatus.READY:
            raise RuntimeError(f"Agent {self.name} not ready to start (status: {self.status})")
        
        self.logger.info(f"Starting agent {self.name}")
        
        # Start message processing loop
        asyncio.create_task(self._message_processing_loop())
        
        # Agent-specific startup
        await self.on_start()
    
    @abstractmethod
    async def on_start(self):
        """Agent-specific startup logic - must be implemented by subclasses"""
        pass
    
    async def stop(self):
        """Stop the agent gracefully"""
        self.logger.info(f"Stopping agent {self.name}")
        self.status = AgentStatus.STOPPED
        
        # Stop all active tasks
        for task_id in list(self.active_tasks.keys()):
            await self.cancel_task(task_id)
        
        # Agent-specific cleanup
        await self.on_stop()
    
    @abstractmethod  
    async def on_stop(self):
        """Agent-specific cleanup logic - must be implemented by subclasses"""
        pass
    
    async def _message_processing_loop(self):
        """Main message processing loop"""
        while self.status != AgentStatus.STOPPED:
            try:
                # Get message from queue (with timeout)
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._handle_message(message)
                self.last_activity = datetime.now()
            except asyncio.TimeoutError:
                # No message received, continue loop
                continue
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
    
    async def _handle_message(self, message: AgentMessage):
        """Handle incoming message"""
        self.logger.info(f"Received {message.message_type.value} from {message.sender_id}")
        
        # Update conversation tracking
        if message.conversation_id:
            if message.conversation_id not in self.active_conversations:
                self.active_conversations[message.conversation_id] = []
            self.active_conversations[message.conversation_id].append(message)
        
        # Route to appropriate handler
        handler = self.communication_handlers.get(message.message_type)
        if handler:
            try:
                response = await handler(message)
                if response and message.requires_response:
                    await self.send_message(message.sender_id, MessageType.TASK_RESPONSE, response, 
                                          conversation_id=message.conversation_id)
            except Exception as e:
                self.logger.error(f"Error handling {message.message_type.value}: {e}")
                if message.requires_response:
                    await self.send_message(message.sender_id, MessageType.ERROR_REPORT, 
                                          {"error": str(e)}, conversation_id=message.conversation_id)
        else:
            # Default handling
            await self.on_message_received(message)
    
    @abstractmethod
    async def on_message_received(self, message: AgentMessage):
        """Handle messages not handled by specific handlers - must be implemented by subclasses"""
        pass
    
    async def send_message(self, recipient_id: str, message_type: MessageType, 
                         content: Dict[str, Any], priority: int = 5, 
                         requires_response: bool = False, conversation_id: str = None) -> str:
        """Send message to another agent"""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(),
            priority=priority,
            requires_response=requires_response,
            conversation_id=conversation_id or str(uuid.uuid4())
        )
        
        self.logger.info(f"Sending {message_type.value} to {recipient_id}")
        
        if self.communication_system:
            await self.communication_system.route_message(message)
        
        return message.conversation_id
    
    async def execute_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Execute a specific task using brain for thinking and hands for doing"""
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            raise RuntimeError(f"Agent {self.name} at max capacity ({self.max_concurrent_tasks} tasks)")
        
        self.status = AgentStatus.WORKING
        self.active_tasks[task_id] = {
            'data': task_data,
            'started_at': datetime.now(),
            'status': 'running'
        }
        
        try:
            self.logger.info(f"Executing task {task_id}")
            
            # 🧠 Think about the task first
            thinking_result = await self.think_about_task(task_id, task_data)
            
            # ✋ Execute the task using hands if needed
            execution_result = await self.execute_with_hands(task_id, task_data, thinking_result)
            
            # 👀 Self-assess the results
            assessment = await self.assess_task_performance(task_id, thinking_result, execution_result)
            
            # Combine results
            result = {
                'thinking': thinking_result,
                'execution': execution_result,
                'self_assessment': assessment,
                'task_id': task_id
            }
            
            # Mark task as completed
            self.active_tasks[task_id]['status'] = 'completed'
            self.active_tasks[task_id]['completed_at'] = datetime.now()
            self.active_tasks[task_id]['result'] = result
            
            # Update performance metrics
            self._update_performance_metrics('completed', (datetime.now() - self.active_tasks[task_id]['started_at']).total_seconds())
            
            # Move to history
            self.task_history.append(self.active_tasks[task_id])
            del self.active_tasks[task_id]
            
            # Update status
            if not self.active_tasks:
                self.status = AgentStatus.READY
            
            self.logger.info(f"Task {task_id} completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {e}")
            self.active_tasks[task_id]['status'] = 'failed'
            self.active_tasks[task_id]['error'] = str(e)
            self.active_tasks[task_id]['failed_at'] = datetime.now()
            
            # Update performance metrics
            self._update_performance_metrics('failed', (datetime.now() - self.active_tasks[task_id]['started_at']).total_seconds())
            
            # Move to history
            self.task_history.append(self.active_tasks[task_id])
            del self.active_tasks[task_id]
            
            if not self.active_tasks:
                self.status = AgentStatus.READY
                
            raise
    
    async def think_about_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use brain to think about and plan the task"""
        if not self.brain:
            return {"error": "No brain initialized"}
        
        # Create thinking prompt
        thinking_prompt = f"""
        I need to work on the following task:
        
        Task ID: {task_id}
        Task Data: {json.dumps(task_data, indent=2)}
        
        Please help me:
        1. Understand what exactly needs to be done
        2. Plan the approach and steps
        3. Identify what tools/code I might need
        4. Consider potential challenges or issues
        5. Suggest success criteria
        
        Think step by step and provide a structured plan.
        """
        
        # Think about it
        thought_process = await self.brain.think(
            thinking_prompt,
            context={"agent_capabilities": [cap.name for cap in self.config.capabilities]},
            thinking_mode=ThinkingMode.ANALYTICAL,
            structured_output_schema={
                "understanding": "string",
                "approach": "string", 
                "steps": "array",
                "tools_needed": "array",
                "challenges": "array",
                "success_criteria": "array"
            }
        )
        
        # Update metrics
        self.performance_metrics['brain_api_calls'] += 1
        
        return {
            "thought_process": thought_process,
            "plan": thought_process.structured_output,
            "confidence": thought_process.confidence
        }
    
    async def execute_with_hands(self, task_id: str, task_data: Dict[str, Any], thinking_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using hands (code execution) based on brain's plan"""
        if not self.hands:
            return {"error": "No hands initialized"}
        
        # Check if the task requires code execution
        plan = thinking_result.get('plan', {})
        tools_needed = plan.get('tools_needed', [])
        
        execution_results = []
        
        # Execute based on what the brain planned
        for tool in tools_needed:
            if 'python' in tool.lower():
                # Generate Python code based on the plan
                code = await self._generate_code_for_task(task_data, thinking_result)
                if code:
                    result = await self.hands.execute_python(code)
                    execution_results.append(result)
            elif 'sql' in tool.lower():
                # Generate SQL query based on the plan  
                query = await self._generate_sql_for_task(task_data, thinking_result)
                if query:
                    result = await self.hands.execute_sql(query)
                    execution_results.append(result)
            elif 'bash' in tool.lower() or 'command' in tool.lower():
                # Generate bash command based on the plan
                command = await self._generate_command_for_task(task_data, thinking_result)
                if command:
                    result = await self.hands.execute_bash(command)
                    execution_results.append(result)
        
        # If no code execution needed, call the agent's custom task execution
        if not execution_results:
            custom_result = await self.on_execute_task(task_id, task_data)
            return {"custom_execution": custom_result}
        
        # Update metrics
        self.performance_metrics['hands_executions'] += len(execution_results)
        
        return {
            "execution_results": execution_results,
            "total_executions": len(execution_results)
        }
    
    async def assess_task_performance(self, task_id: str, thinking_result: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Self-assess task performance using eyes (monitoring)"""
        if not self.brain:
            return {"error": "No brain for self-assessment"}
        
        # Create self-assessment prompt
        assessment_prompt = f"""
        I just completed a task. Please help me assess my performance:
        
        Task ID: {task_id}
        
        My thinking process:
        - Confidence: {thinking_result.get('confidence', 'N/A')}
        - Plan quality: {len(thinking_result.get('plan', {}).get('steps', []))} steps planned
        
        My execution results:
        - Executions performed: {execution_result.get('total_executions', 0)}
        - Any errors: {any('error' in str(result) for result in execution_result.get('execution_results', []))}
        
        Please assess:
        1. How well did I understand and plan the task?
        2. How well did I execute the plan?
        3. What could I improve?
        4. What did I do well?
        5. Overall performance score (1-10)
        """
        
        assessment = await self.brain.think(
            assessment_prompt,
            thinking_mode=ThinkingMode.REFLECTIVE,
            structured_output_schema={
                "understanding_score": "number",
                "execution_score": "number", 
                "improvements": "array",
                "strengths": "array",
                "overall_score": "number"
            }
        )
        
        # Store assessment in history
        self.self_assessment_history.append({
            "task_id": task_id,
            "timestamp": datetime.now(),
            "assessment": assessment.structured_output
        })
        
        # Update metrics
        self.performance_metrics['self_assessments'] += 1
        
        return {
            "assessment": assessment.structured_output,
            "confidence": assessment.confidence,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_code_for_task(self, task_data: Dict[str, Any], thinking_result: Dict[str, Any]) -> Optional[str]:
        """Generate Python code based on task requirements and brain's plan"""
        if not self.brain:
            return None
        
        code_prompt = f"""
        Based on my analysis of this task:
        {json.dumps(thinking_result.get('plan', {}), indent=2)}
        
        Generate Python code to accomplish this task:
        {json.dumps(task_data, indent=2)}
        
        Requirements:
        - Use only safe, standard libraries
        - Include error handling
        - Add comments explaining the code
        - Return the result or save it appropriately
        
        Provide only the Python code, no explanations.
        """
        
        code_response = await self.brain.think(code_prompt, thinking_mode=ThinkingMode.PRACTICAL)
        
        # Extract code from response (simple extraction)
        code_lines = []
        in_code_block = False
        for line in code_response.raw_response.split('\n'):
            if '```python' in line or '```' in line:
                in_code_block = not in_code_block
                continue
            if in_code_block:
                code_lines.append(line)
        
        return '\n'.join(code_lines) if code_lines else None
    
    async def _generate_sql_for_task(self, task_data: Dict[str, Any], thinking_result: Dict[str, Any]) -> Optional[str]:
        """Generate SQL query based on task requirements"""
        # Placeholder - would implement SQL generation logic
        return None
    
    async def _generate_command_for_task(self, task_data: Dict[str, Any], thinking_result: Dict[str, Any]) -> Optional[str]:
        """Generate bash command based on task requirements"""  
        # Placeholder - would implement command generation logic
        return None
    
    def _update_performance_metrics(self, result: str, duration: float):
        """Update performance metrics"""
        if result == 'completed':
            self.performance_metrics['tasks_completed'] += 1
        else:
            self.performance_metrics['tasks_failed'] += 1
        
        # Update average task time
        total_tasks = self.performance_metrics['tasks_completed'] + self.performance_metrics['tasks_failed']
        current_avg = self.performance_metrics['average_task_time']
        self.performance_metrics['average_task_time'] = ((current_avg * (total_tasks - 1)) + duration) / total_tasks
    
    @abstractmethod
    async def on_execute_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Execute agent-specific task - must be implemented by subclasses"""
        pass
    
    async def cancel_task(self, task_id: str):
        """Cancel an active task"""
        if task_id in self.active_tasks:
            self.logger.info(f"Canceling task {task_id}")
            self.active_tasks[task_id]['status'] = 'cancelled'
            self.active_tasks[task_id]['cancelled_at'] = datetime.now()
            
            # Move to history
            self.task_history.append(self.active_tasks[task_id])
            del self.active_tasks[task_id]
            
            # Agent-specific cancellation logic
            await self.on_task_cancelled(task_id)
            
            if not self.active_tasks:
                self.status = AgentStatus.READY
    
    async def on_task_cancelled(self, task_id: str):
        """Handle task cancellation - can be overridden by subclasses"""
        pass
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a handler for specific message types"""
        self.communication_handlers[message_type] = handler
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'type': self.agent_type.value,
            'status': self.status.value,
            'creation_time': self.creation_time.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'active_tasks': len(self.active_tasks),
            'total_tasks_completed': len([t for t in self.task_history if t['status'] == 'completed']),
            'active_conversations': len(self.active_conversations),
            'sub_agents': len(self.sub_agents),
            'supervisor': self.supervisor
        }
    
    def add_sub_agent(self, sub_agent: 'BaseAgent'):
        """Add a sub-agent under this agent's management"""
        self.sub_agents[sub_agent.agent_id] = sub_agent
        self.logger.info(f"Added sub-agent {sub_agent.name} ({sub_agent.agent_id})")
    
    def remove_sub_agent(self, agent_id: str):
        """Remove a sub-agent"""
        if agent_id in self.sub_agents:
            agent = self.sub_agents[agent_id]
            del self.sub_agents[agent_id]
            self.logger.info(f"Removed sub-agent {agent.name} ({agent_id})")
    
    async def delegate_task(self, sub_agent_id: str, task_id: str, task_data: Dict[str, Any]):
        """Delegate a task to a sub-agent"""
        if sub_agent_id not in self.sub_agents:
            raise ValueError(f"Sub-agent {sub_agent_id} not found")
        
        sub_agent = self.sub_agents[sub_agent_id]
        self.logger.info(f"Delegating task {task_id} to sub-agent {sub_agent.name}")
        
        return await sub_agent.execute_task(task_id, task_data)
    
    def __str__(self) -> str:
        return f"Agent({self.name}, {self.agent_type.value}, {self.status.value})"
    
    def __repr__(self) -> str:
        return f"<Agent id={self.agent_id} name='{self.name}' type={self.agent_type.value} status={self.status.value}>"