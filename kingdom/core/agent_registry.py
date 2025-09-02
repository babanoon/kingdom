#!/usr/bin/env python3
"""
Agent Registry and Discovery System for the Kingdom Project

This module manages agent lifecycle, registration, discovery, and orchestration.
It serves as the central coordination point for all agents in the Deos system.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict

from .base_agent import BaseAgent, AgentStatus, AgentType, AgentMessage, MessageType


class AgentRegistry:
    """
    Central registry for all agents in the Kingdom system.
    
    Manages agent lifecycle, discovery, communication routing, and system orchestration.
    This is where Deos maintains awareness of all agents and their capabilities.
    """
    
    def __init__(self):
        # Core registry data
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Hierarchical organization  
        self.agent_hierarchy: Dict[str, List[str]] = defaultdict(list)  # supervisor -> [subordinates]
        self.agent_supervisors: Dict[str, str] = {}  # agent -> supervisor
        
        # Capability index for discovery
        self.capability_index: Dict[str, Set[str]] = defaultdict(set)  # capability -> {agent_ids}
        
        # Type groupings
        self.agents_by_type: Dict[AgentType, Set[str]] = defaultdict(set)
        
        # Communication and routing
        self.message_router = MessageRouter()
        
        # System status
        self.registry_started = False
        self.startup_time = None
        
        # Event hooks
        self.event_handlers = defaultdict(list)
    
    async def start_registry(self):
        """Start the agent registry system"""
        if self.registry_started:
            return
        
        print("🏰 Starting Kingdom Agent Registry...")
        self.startup_time = datetime.now()
        self.registry_started = True
        
        # Start message router
        await self.message_router.start()
        
        print("✅ Agent Registry started successfully")
    
    async def stop_registry(self):
        """Stop the agent registry and all agents"""
        print("🛑 Stopping Kingdom Agent Registry...")
        
        # Stop all agents gracefully  
        for agent in self.agents.values():
            try:
                await agent.stop()
            except Exception as e:
                print(f"❌ Error stopping agent {agent.name}: {e}")
        
        # Stop message router
        await self.message_router.stop()
        
        self.registry_started = False
        print("✅ Agent Registry stopped")
    
    async def register_agent(self, agent: BaseAgent, supervisor_id: str = None) -> bool:
        """
        Register a new agent in the system.
        
        Args:
            agent: The agent instance to register
            supervisor_id: Optional ID of supervising agent
            
        Returns:
            bool: True if registration successful
        """
        agent_id = agent.agent_id
        
        if agent_id in self.agents:
            raise ValueError(f"Agent with ID {agent_id} already registered")
        
        # Register the agent
        self.agents[agent_id] = agent
        
        # Store metadata
        self.agent_metadata[agent_id] = {
            'name': agent.name,
            'type': agent.agent_type,
            'registered_at': datetime.now(),
            'capabilities': [cap.name for cap in agent.config.capabilities],
            'description': agent.config.description,
            'security_level': agent.config.security_level
        }
        
        # Update type groupings
        self.agents_by_type[agent.agent_type].add(agent_id)
        
        # Handle hierarchy
        if supervisor_id:
            if supervisor_id not in self.agents:
                raise ValueError(f"Supervisor agent {supervisor_id} not found")
            
            self.agent_supervisors[agent_id] = supervisor_id
            self.agent_hierarchy[supervisor_id].append(agent_id)
            
            # Add as sub-agent to supervisor
            supervisor = self.agents[supervisor_id]
            supervisor.add_sub_agent(agent)
        
        # Update capability index
        for capability in agent.config.capabilities:
            self.capability_index[capability.name].add(agent_id)
        
        # Set up communication routing
        self.message_router.register_agent(agent_id, agent)
        
        print(f"✅ Registered agent: {agent.name} ({agent.agent_type.value})")
        
        # Trigger event handlers
        await self._trigger_event('agent_registered', agent_id)
        
        return True
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the system.
        
        Args:
            agent_id: ID of agent to unregister
            
        Returns:
            bool: True if unregistration successful
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Stop the agent
        await agent.stop()
        
        # Remove from hierarchies
        if agent_id in self.agent_supervisors:
            supervisor_id = self.agent_supervisors[agent_id]
            if supervisor_id in self.agent_hierarchy:
                self.agent_hierarchy[supervisor_id].remove(agent_id)
            del self.agent_supervisors[agent_id]
        
        # Remove subordinates
        if agent_id in self.agent_hierarchy:
            for subordinate_id in self.agent_hierarchy[agent_id]:
                if subordinate_id in self.agent_supervisors:
                    del self.agent_supervisors[subordinate_id]
            del self.agent_hierarchy[agent_id]
        
        # Remove from capability index
        for capability in agent.config.capabilities:
            self.capability_index[capability.name].discard(agent_id)
        
        # Remove from type groupings
        self.agents_by_type[agent.agent_type].discard(agent_id)
        
        # Remove from communication routing
        self.message_router.unregister_agent(agent_id)
        
        # Clean up
        del self.agents[agent_id]
        del self.agent_metadata[agent_id]
        
        print(f"🗑️  Unregistered agent: {agent.name}")
        
        # Trigger event handlers
        await self._trigger_event('agent_unregistered', agent_id)
        
        return True
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def find_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        """Find all agents of a specific type"""
        agent_ids = self.agents_by_type.get(agent_type, set())
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def find_agents_by_capability(self, capability_name: str) -> List[BaseAgent]:
        """Find all agents with a specific capability"""
        agent_ids = self.capability_index.get(capability_name, set())
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def find_agents_by_status(self, status: AgentStatus) -> List[BaseAgent]:
        """Find all agents with a specific status"""
        return [agent for agent in self.agents.values() if agent.status == status]
    
    def get_agent_hierarchy(self, agent_id: str) -> Dict[str, Any]:
        """Get the hierarchy tree for an agent (subordinates)"""
        if agent_id not in self.agents:
            return {}
        
        agent = self.agents[agent_id]
        subordinates = self.agent_hierarchy.get(agent_id, [])
        
        hierarchy = {
            'agent': {
                'id': agent_id,
                'name': agent.name,
                'type': agent.agent_type.value,
                'status': agent.status.value
            },
            'subordinates': []
        }
        
        for sub_id in subordinates:
            if sub_id in self.agents:
                hierarchy['subordinates'].append(self.get_agent_hierarchy(sub_id))
        
        return hierarchy
    
    def get_supervision_chain(self, agent_id: str) -> List[str]:
        """Get the chain of command for an agent (up to top level)"""
        chain = []
        current_id = agent_id
        
        while current_id in self.agent_supervisors:
            supervisor_id = self.agent_supervisors[current_id]
            chain.append(supervisor_id)
            current_id = supervisor_id
            
            # Prevent infinite loops
            if len(chain) > 10:
                break
        
        return chain
    
    async def send_message(self, sender_id: str, recipient_id: str, 
                          message_type: MessageType, content: Dict[str, Any],
                          priority: int = 5, requires_response: bool = False) -> str:
        """Send a message between agents"""
        return await self.message_router.send_message(
            sender_id, recipient_id, message_type, content, priority, requires_response
        )
    
    async def broadcast_message(self, sender_id: str, message_type: MessageType, 
                              content: Dict[str, Any], 
                              target_type: AgentType = None,
                              target_capability: str = None) -> List[str]:
        """Broadcast message to multiple agents"""
        targets = []
        
        if target_type:
            targets.extend(self.find_agents_by_type(target_type))
        elif target_capability:
            targets.extend(self.find_agents_by_capability(target_capability))
        else:
            targets = list(self.agents.values())
        
        # Remove sender from targets
        targets = [agent for agent in targets if agent.agent_id != sender_id]
        
        conversation_ids = []
        for agent in targets:
            conv_id = await self.send_message(
                sender_id, agent.agent_id, message_type, content
            )
            conversation_ids.append(conv_id)
        
        return conversation_ids
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        if not self.registry_started:
            return {'status': 'stopped'}
        
        status_counts = defaultdict(int)
        type_counts = defaultdict(int)
        
        for agent in self.agents.values():
            status_counts[agent.status.value] += 1
            type_counts[agent.agent_type.value] += 1
        
        return {
            'status': 'running',
            'startup_time': self.startup_time.isoformat() if self.startup_time else None,
            'total_agents': len(self.agents),
            'agents_by_status': dict(status_counts),
            'agents_by_type': dict(type_counts),
            'active_capabilities': len(self.capability_index),
            'message_router_status': self.message_router.get_status()
        }
    
    def get_agent_list(self, include_sub_agents: bool = True) -> List[Dict[str, Any]]:
        """Get list of all registered agents with their info"""
        agents_info = []
        
        for agent_id, agent in self.agents.items():
            metadata = self.agent_metadata[agent_id]
            supervisor = self.agent_supervisors.get(agent_id)
            subordinates = self.agent_hierarchy.get(agent_id, [])
            
            agent_info = {
                'id': agent_id,
                'name': agent.name,
                'type': agent.agent_type.value,
                'status': agent.status.value,
                'registered_at': metadata['registered_at'].isoformat(),
                'capabilities': metadata['capabilities'],
                'security_level': metadata['security_level'],
                'supervisor': supervisor,
                'subordinate_count': len(subordinates),
                'active_tasks': len(agent.active_tasks),
                'last_activity': agent.last_activity.isoformat()
            }
            
            if include_sub_agents:
                agent_info['subordinates'] = subordinates
            
            agents_info.append(agent_info)
        
        return agents_info
    
    def register_event_handler(self, event_type: str, handler):
        """Register an event handler"""
        self.event_handlers[event_type].append(handler)
    
    async def _trigger_event(self, event_type: str, *args, **kwargs):
        """Trigger event handlers"""
        for handler in self.event_handlers[event_type]:
            try:
                await handler(*args, **kwargs)
            except Exception as e:
                print(f"❌ Error in event handler for {event_type}: {e}")


class MessageRouter:
    """Handles message routing between agents"""
    
    def __init__(self):
        self.agents = {}
        self.message_queue = asyncio.Queue()
        self.running = False
        self.stats = {
            'messages_routed': 0,
            'routing_errors': 0,
            'start_time': None
        }
    
    async def start(self):
        """Start the message router"""
        self.running = True
        self.stats['start_time'] = datetime.now()
        asyncio.create_task(self._routing_loop())
    
    async def stop(self):
        """Stop the message router"""
        self.running = False
    
    def register_agent(self, agent_id: str, agent: BaseAgent):
        """Register an agent for message routing"""
        self.agents[agent_id] = agent
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
    
    async def send_message(self, sender_id: str, recipient_id: str, 
                          message_type: MessageType, content: Dict[str, Any],
                          priority: int = 5, requires_response: bool = False) -> str:
        """Queue a message for routing"""
        if recipient_id not in self.agents:
            raise ValueError(f"Recipient agent {recipient_id} not found")
        
        sender_agent = self.agents.get(sender_id)
        if not sender_agent:
            raise ValueError(f"Sender agent {sender_id} not found")
        
        # Create and queue message
        conversation_id = await sender_agent.send_message(
            recipient_id, message_type, content, priority, requires_response
        )
        
        return conversation_id
    
    async def route_message(self, message: AgentMessage):
        """Route a message to its destination"""
        recipient = self.agents.get(message.recipient_id)
        if recipient:
            await recipient.message_queue.put(message)
            self.stats['messages_routed'] += 1
        else:
            print(f"❌ Cannot route message - recipient {message.recipient_id} not found")
            self.stats['routing_errors'] += 1
    
    async def _routing_loop(self):
        """Main routing loop"""
        while self.running:
            try:
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
            except Exception as e:
                print(f"❌ Error in routing loop: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get router status"""
        return {
            'running': self.running,
            'registered_agents': len(self.agents),
            'messages_routed': self.stats['messages_routed'],
            'routing_errors': self.stats['routing_errors'],
            'start_time': self.stats['start_time'].isoformat() if self.stats['start_time'] else None
        }


# Global registry instance (singleton pattern)
_global_registry = None

def get_registry() -> AgentRegistry:
    """Get the global agent registry instance"""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry

async def initialize_kingdom():
    """Initialize the Kingdom agent system"""
    registry = get_registry()
    await registry.start_registry()
    return registry

async def shutdown_kingdom():
    """Shutdown the Kingdom agent system"""
    registry = get_registry()
    await registry.stop_registry()