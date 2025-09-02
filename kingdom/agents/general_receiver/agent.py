#!/usr/bin/env python3
"""
General Receiver Agent

A versatile AI agent that handles general questions and conversations using 
Gemini AI model. This agent serves as the primary entry point for external
communications and can route messages to specialized agents when needed.

Agent Architecture:
- 🧠 Brain: Google Gemini for general reasoning and conversation
- ✋ Hands: Basic text processing and response formatting
- 👂 Ears: Rocket.Chat integration, management API endpoints
- 👅 Tongue: Markdown responses, A2A messaging
- 👀 Eyes: Response quality validation
- 🦵 Legs: Lightweight deployment, fast response times
- 🦷 Teeth: Input sanitization and safety filters

Capabilities:
- General Q&A using Gemini AI
- Message routing to specialized agents
- Chat interface for external integrations
- A2A communication with other Kingdom agents
- Workflow tracking and logging
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add project root to path
import sys
sys.path.append('/Users/ed/King/B2')

from kingdom.core.base_agent import BaseAgent, AgentType, AgentMessage, MessageType
from kingdom.core.genai_brain import GenAIBrain, GenAIProvider, ThinkingMode, AgentPersonality
from kingdom.core.agent_logging import get_agent_logger, log_task_start, log_task_complete, log_error
from kingdom.service.agent_service import ServiceAgent

class GeneralReceiverAgent(ServiceAgent):
    """
    General Receiver Agent - Handles general Q&A and message routing
    
    This agent uses Google Gemini to provide intelligent responses to general
    questions and can route specialized requests to appropriate agents.
    """
    
    def __init__(self, agent_id: str, agent_type: str = "general_receiver"):
        super().__init__(agent_id, agent_type)
        
        # Agent configuration
        self.config = self._load_config()
        
        # Initialize GenAI brain with OpenAI (Gemini implementation is incomplete)
        self.brain = GenAIBrain(
            agent_id=agent_id,
            personality=self._get_personality(),
            primary_provider=GenAIProvider.OPENAI
        )
        
        # Conversation history for context
        self.conversation_history = []

        # Response templates
        self.response_templates = self._load_response_templates()

        # Routing rules for specialized agents
        self.routing_rules = self._load_routing_rules()

        # Pending routing requests (workflow_id -> response data)
        self.pending_routing_requests = {}

        # Setup centralized logging
        self.agent_logger = get_agent_logger(agent_id, "local")  # Assume local for now
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration"""
        try:
            with open('/Users/ed/King/B2/kingdom/agents/general_receiver/config.json', 'r') as f:
                config = json.load(f)
                print(f"✅ Loaded config from file: {config}")
                return config
        except FileNotFoundError:
            config = {
                "max_conversation_history": 10,
                "response_timeout": 30,
                "enable_routing": True,
                "safety_level": "medium"
            }
            print(f"✅ Using default config: {config}")
            return config
    
    def _get_personality(self) -> AgentPersonality:
        """Define agent personality for GenAI brain"""
        return AgentPersonality(
            name="GeneralReceiver",
            role="General Assistant and Message Router",
            personality_traits=[
                "Helpful and friendly",
                "Concise but informative",
                "Able to recognize when to route to specialists",
                "Professional yet approachable"
            ],
            expertise_areas=[
                "General knowledge",
                "Conversation management",
                "Message routing and delegation",
                "Information synthesis"
            ],
            communication_style="Clear, helpful, and contextually appropriate",
            preferred_thinking_mode=ThinkingMode.PRACTICAL,
            system_prompt_template="You are a helpful assistant and message router.",
            temperature=0.7,
            max_tokens=2000
        )
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load response templates"""
        return {
            "greeting": "Hello! I'm here to help you with any questions or tasks. What can I assist you with today?",
            "routing": "I'll route your request to our {specialist} agent who can better handle {request_type} questions.",
            "error": "I apologize, but I encountered an issue processing your request. Please try again or rephrase your question.",
            "clarification": "Could you please provide more details about {topic}? This will help me give you a better response."
        }
    
    def _load_routing_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load routing rules for specialized agents"""
        return {
            "mathematical": {
                "keywords": ["calculate", "math", "equation", "solve", "compute", "formula", "+", "-", "*", "/", "="],
                "target_agent": "math_calculator_001",
                "confidence_threshold": 0.3
            },
            "database": {
                "keywords": ["database", "sql", "query", "data", "table", "select"],
                "target_agent": "tester1_001",
                "confidence_threshold": 0.8
            },
            "testing": {
                "keywords": ["test", "validation", "check", "verify", "quality"],
                "target_agent": "tester2_001",
                "confidence_threshold": 0.8
            }
        }
    
    async def _handle_task(self, task) -> Any:
        """Handle tasks for GeneralReceiver agent"""
        task_type = task.task_type
        payload = task.payload

        # Log task start
        log_task_start(self.agent_id, task.task_id, task_type, "local")
        self.agent_logger.log("task_received", f"Processing {task_type} task", {
            "task_id": task.task_id,
            "payload_keys": list(payload.keys()) if payload else [],
            "message_preview": payload.get('message', '')[:100] if 'message' in payload else ""
        })

        try:
            if task_type == "process_chat_message":
                result = await self._handle_chat_message(payload)
            elif task_type == "general_question":
                result = await self._handle_general_question(payload)
            elif task_type == "route_message":
                result = await self._handle_message_routing(payload)
            else:
                result = {"error": f"Unknown task type: {task_type}"}

            # Log task completion
            log_task_complete(self.agent_id, task.task_id, result, "local")
            self.agent_logger.log("task_completed", f"Task {task_type} completed", {
                "task_id": task.task_id,
                "success": result.get('success', False) if isinstance(result, dict) else True,
                "response_length": len(result.get('response', '')) if isinstance(result, dict) and 'response' in result else 0
            })

            return result

        except Exception as e:
            # Log error
            log_error(self.agent_id, task_type, e, "local")
            self.agent_logger.log("task_error", f"Task {task_type} failed", {
                "task_id": task.task_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {"error": str(e), "success": False}
    
    async def _handle_chat_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming chat messages from external systems"""
        sender = payload.get('sender', 'unknown')
        message = payload.get('message', '')
        forum = payload.get('forum', 'general')
        workflow_id = payload.get('workflow_id')
        
        self.logger.info(f"Processing chat message from {sender} in {forum}: {message}")
        
        # Check if message should be routed to specialist
        routing_decision = await self._should_route_message(message)
        
        if routing_decision['should_route']:
            return await self._route_to_specialist(routing_decision, payload)
        
        # Process with GenAI brain
        try:
            # Prepare context for AI
            context = {
                "conversation_type": "chat_message",
                "sender": sender,
                "forum": forum,
                "previous_messages": self.conversation_history[-3:],  # Last 3 messages
                "workflow_id": workflow_id
            }
            
            # Get AI response
            ai_response = await self.brain.think(
                input_text=message,
                context=context,
                thinking_mode=ThinkingMode.ANALYTICAL  # Use ANALYTICAL instead of CONVERSATIONAL
            )

            # Store in conversation history
            self.conversation_history.append({
                "sender": sender,
                "message": message,
                "response": ai_response.raw_response,
                "timestamp": datetime.now().isoformat()
            })

            # Keep history manageable
            max_history = self.config.get('runtime_configuration', {}).get('max_conversation_history', 10)
            if len(self.conversation_history) > max_history:
                self.conversation_history = self.conversation_history[-max_history:]

            return {
                "success": True,
                "response": ai_response.raw_response,
                "agent_id": self.agent_id,
                "processing_time_ms": int(ai_response.processing_time * 1000),
                "workflow_id": workflow_id,
                "routed": False
            }
            
        except Exception as e:
            self.logger.error(f"Error processing chat message: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": self.response_templates["error"],
                "agent_id": self.agent_id
            }
    
    async def _handle_general_question(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general questions"""
        question = payload.get('question', '')
        context_data = payload.get('context', {})
        
        try:
            # Use GenAI brain for reasoning
            ai_response = await self.brain.think(
                input_text=question,
                context=context_data,
                thinking_mode=ThinkingMode.ANALYTICAL
            )

            return {
                "success": True,
                "answer": ai_response.raw_response,
                "confidence": ai_response.confidence,
                "agent_id": self.agent_id,
                "processing_time_ms": int(ai_response.processing_time * 1000)
            }
            
        except Exception as e:
            self.logger.error(f"Error handling general question: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    async def _should_route_message(self, message: str) -> Dict[str, Any]:
        """Determine if message should be routed to a specialist agent"""
        enable_routing = self.config.get('runtime_configuration', {}).get('enable_routing', True)
        if not enable_routing:
            return {"should_route": False}
        
        message_lower = message.lower()
        routing_scores = {}
        
        # Calculate routing scores based on keywords
        for category, rules in self.routing_rules.items():
            score = 0
            found_keywords = []
            for keyword in rules['keywords']:
                if keyword in message_lower:
                    score += 1
                    found_keywords.append(keyword)

            # For mathematical category, use a different scoring approach
            if category == "mathematical":
                # If we found any mathematical operators, boost the score
                if any(op in message_lower for op in ['+', '-', '*', '/', '=']):
                    score += 2  # Bonus for mathematical operators
                # Normalize score differently for math
                normalized_score = min(score / 3.0, 1.0)  # Cap at 1.0
            else:
                # Normalize score for other categories
                normalized_score = score / len(rules['keywords'])

            # Debug logging
            self.logger.info(f"Routing check for {category}: score={score}, normalized={normalized_score:.2f}, threshold={rules['confidence_threshold']}, found_keywords={found_keywords}")

            if normalized_score >= rules['confidence_threshold']:
                routing_scores[category] = {
                    "score": normalized_score,
                    "target_agent": rules['target_agent']
                }
        
        # Select best routing option
        if routing_scores:
            best_category = max(routing_scores.keys(), key=lambda k: routing_scores[k]['score'])
            return {
                "should_route": True,
                "category": best_category,
                "target_agent": routing_scores[best_category]['target_agent'],
                "confidence": routing_scores[best_category]['score']
            }
        
        return {"should_route": False}
    
    async def _route_to_specialist(self, routing_decision: Dict[str, Any],
                                 original_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route message to specialist agent"""
        target_agent = routing_decision['target_agent']
        category = routing_decision['category']
        workflow_id = original_payload.get('workflow_id')

        self.logger.info(f"Routing message to {target_agent} for {category} processing")

        # Prepare routing message
        routing_payload = {
            "original_message": original_payload.get('message', ''),
            "sender": original_payload.get('sender', ''),
            "forum": original_payload.get('forum', ''),
            "routing_reason": category,
            "routed_by": self.agent_id,
            "workflow_id": workflow_id
        }

        # Store this routing request for later response handling
        self.pending_routing_requests[workflow_id] = {
            "target_agent": target_agent,
            "category": category,
            "original_payload": original_payload,
            "routing_time": datetime.now().isoformat(),
            "status": "routing"
        }

        # Log routing action with detailed context for debugging
        self.agent_logger.log("routing_initiated", f"Routing to {target_agent} for {category}", {
            "target_agent": target_agent,
            "category": category,
            "workflow_id": workflow_id,
            "routing_payload_keys": list(routing_payload.keys()),
            "original_message_preview": (original_payload.get('message', '')[:120] if original_payload else ''),
            "pending_requests_count": len(self.pending_routing_requests)
        })

        # Send A2A message to specialist
        print(f"🔍 GENERAL DEBUG: Sending A2A message to {target_agent}")
        await self.send_a2a_message(target_agent, {
            "type": "routed_request",
            "payload": routing_payload,
            "return_address": self.agent_id
        })
        print(f"✅ GENERAL DEBUG: A2A message sent to {target_agent}")

        # Wait for the specialist response (with timeout)
        timeout = 60  # seconds (increased to avoid premature timeout)
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < timeout:
            # Proactively poll the A2A bus to ensure messages are processed while waiting
            try:
                message = await self.a2a_bus.get_message(self.agent_id, timeout=0.05)
                if message:
                    self.agent_logger.log("a2a_poll_tick", "Polled A2A message while waiting for specialist", {
                        "message_id": message.get('message_id'),
                        "sender": message.get('sender'),
                        "type": message.get('payload', {}).get('type')
                    })
                    await self._handle_a2a_message(message)
            except Exception:
                # Ignore polling errors and continue waiting
                pass

            if workflow_id in self.pending_routing_requests:
                pending_request = self.pending_routing_requests[workflow_id]
                if pending_request.get("routed") and "response" in pending_request:
                    # We got a response!
                    response_data = pending_request
                    del self.pending_routing_requests[workflow_id]  # Clean up
                    return response_data

            # Small sleep to yield control
            await asyncio.sleep(0.05)

        # Timeout - return error
        del self.pending_routing_requests[workflow_id]  # Clean up
        # Log timeout with context
        self.agent_logger.log("routing_timeout", f"Routing to {target_agent} timed out", {
            "workflow_id": workflow_id,
            "target_agent": target_agent,
            "waited_seconds": timeout
        })
        return {
            "success": False,
            "error": f"Routing to {target_agent} timed out after {timeout} seconds",
            "response": self.response_templates["error"],
            "routed": True,
            "target_agent": target_agent,
            "agent_id": self.agent_id
        }
    
    async def _handle_a2a_message(self, message):
        """Handle A2A messages from other agents"""
        payload = message['payload']
        message_type = payload.get('type', 'unknown')
        
        self.logger.info(f"Received A2A message type: {message_type} from {message['sender']}")
        
        if message_type == "specialist_response":
            await self._handle_specialist_response(message)
        elif message_type == "status_request":
            await self._handle_status_request(message)
        else:
            self.logger.warning(f"Unknown A2A message type: {message_type}")
    
    async def _handle_specialist_response(self, message):
        """Handle response from specialist agents"""
        sender = message['sender']
        response_data = message['payload']

        self.logger.info(f"Received specialist response from {sender}")

        # Check if we have a pending routing request waiting for this response
        workflow_id = response_data.get('workflow_id')
        if workflow_id and workflow_id in self.pending_routing_requests:
            # Complete the pending request
            pending_request = self.pending_routing_requests[workflow_id]

            # Extract the solution from the specialist response
            solution = response_data.get('solution', {})
            if isinstance(solution, dict):
                if 'success' in solution and solution['success']:
                    # MathCalculatorAgent response structure
                    if 'final_answer' in solution:
                        final_response = f"The answer is: {solution['final_answer']}"
                        if 'solution_steps' in solution and solution['solution_steps']:
                            final_response += f"\n\nSolution steps:\n" + "\n".join(solution['solution_steps'])
                    else:
                        final_response = f"Specialist {sender} solved the problem successfully"
                elif 'response' in solution:
                    # Generic response structure
                    final_response = solution['response']
                else:
                    final_response = f"Specialist {sender} processed your request"
            else:
                final_response = f"Specialist {sender} processed your request"

            # Update the pending request with the actual response
            pending_request.update({
                "response": final_response,
                "specialist_used": sender,
                "specialist_response": response_data,
                "routed": True
            })

            # Mark this workflow as completed
            self.pending_routing_requests[workflow_id] = pending_request
            self.logger.info(f"Completed routed request for workflow {workflow_id}")

        # Also log the response
        self.logger.info(f"Specialist response: {response_data}")
    
    async def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history for this agent"""
        return self.conversation_history.copy()
    
    async def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.logger.info("Conversation history cleared")
    
    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get detailed agent statistics"""
        base_stats = await self.get_status()
        
        return {
            **base_stats,
            "conversation_history_size": len(self.conversation_history),
            "routing_enabled": self.config.get('runtime_configuration', {}).get('enable_routing', True),
            "available_routing_categories": list(self.routing_rules.keys()),
            "genai_provider": "gemini",
            "response_templates_loaded": len(self.response_templates)
        }