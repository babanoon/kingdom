#!/usr/bin/env python3
"""
Generative AI Brain System for Kingdom Agents

This module provides the "brain" functionality for agents, integrating with
various GenAI models (OpenAI, Gemini, Claude) to give agents actual thinking
and reasoning capabilities.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GenAIProvider(Enum):
    """Supported GenAI providers"""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    LOCAL = "local"

class ThinkingMode(Enum):
    """Different modes of thinking for agents"""
    ANALYTICAL = "analytical"      # Deep, step-by-step reasoning
    CREATIVE = "creative"          # Brainstorming, ideation
    STRATEGIC = "strategic"        # Long-term planning
    PRACTICAL = "practical"        # Immediate problem-solving
    REFLECTIVE = "reflective"      # Self-assessment, learning
    COLLABORATIVE = "collaborative" # Working with other agents

@dataclass
class AgentPersonality:
    """Defines an agent's personality and thinking style"""
    name: str
    role: str
    personality_traits: List[str]
    expertise_areas: List[str]
    communication_style: str
    preferred_thinking_mode: ThinkingMode
    system_prompt_template: str
    temperature: float = 0.7
    max_tokens: int = 2000

@dataclass
class ThoughtProcess:
    """Represents a complete thought process from an agent's brain"""
    agent_id: str
    thought_id: str
    input_context: Dict[str, Any]
    thinking_mode: ThinkingMode
    raw_response: str
    structured_output: Dict[str, Any]
    confidence: float
    reasoning_steps: List[str]
    timestamp: datetime
    tokens_used: int
    processing_time: float

class GenAIBrain:
    """
    The "brain" of an agent - handles all GenAI interactions and thinking processes.
    
    This class encapsulates the agent's ability to think, reason, and generate
    responses using various GenAI models while maintaining personality consistency.
    """
    
    def __init__(self, agent_id: str, personality: AgentPersonality, 
                 primary_provider: GenAIProvider = GenAIProvider.OPENAI):
        self.agent_id = agent_id
        self.personality = personality
        self.primary_provider = primary_provider
        
        # Initialize API clients
        self.clients = {}
        self._initialize_clients()
        
        # Thinking history and context
        self.thought_history: List[ThoughtProcess] = []
        self.context_memory: Dict[str, Any] = {}
        self.conversation_context: List[Dict[str, str]] = []
        
        # Performance tracking
        self.total_tokens_used = 0
        self.total_api_calls = 0
        self.average_response_time = 0.0
        
        print(f"🧠 GenAI Brain initialized for {self.personality.name} using {primary_provider.value}")
    
    def _initialize_clients(self):
        """Initialize GenAI API clients"""
        # OpenAI
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.clients[GenAIProvider.OPENAI] = openai.OpenAI(api_key=openai_key)
        
        # Gemini (will implement when google-generativeai is available)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            # Placeholder for Gemini client
            self.clients[GenAIProvider.GEMINI] = {"api_key": gemini_key}
        
        # Claude (via Anthropic API when available)
        claude_key = os.getenv('CLAUDE_API_KEY')
        if claude_key:
            self.clients[GenAIProvider.CLAUDE] = {"api_key": claude_key}
    
    async def think(self, input_text: str, context: Dict[str, Any] = None,
                   thinking_mode: ThinkingMode = None, 
                   structured_output_schema: Dict[str, Any] = None) -> ThoughtProcess:
        """
        Main thinking method - processes input and generates reasoned response.
        
        Args:
            input_text: The input prompt or question
            context: Additional context for the thinking process
            thinking_mode: How the agent should approach the problem
            structured_output_schema: Expected structure of the response
            
        Returns:
            ThoughtProcess: Complete thought process with reasoning
        """
        start_time = datetime.now()
        context = context or {}
        thinking_mode = thinking_mode or self.personality.preferred_thinking_mode
        
        # Build the complete prompt
        system_prompt = self._build_system_prompt(thinking_mode, context)
        user_prompt = self._build_user_prompt(input_text, context, structured_output_schema)
        
        # Generate response using primary provider
        raw_response, tokens_used = await self._call_genai_api(
            system_prompt, user_prompt, thinking_mode
        )
        
        # Process and structure the response
        structured_output = self._parse_response(raw_response, structured_output_schema)
        reasoning_steps = self._extract_reasoning_steps(raw_response)
        confidence = self._calculate_confidence(raw_response, structured_output)
        
        # Create thought process record
        processing_time = (datetime.now() - start_time).total_seconds()
        thought_process = ThoughtProcess(
            agent_id=self.agent_id,
            thought_id=f"thought_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            input_context={"input": input_text, "context": context},
            thinking_mode=thinking_mode,
            raw_response=raw_response,
            structured_output=structured_output,
            confidence=confidence,
            reasoning_steps=reasoning_steps,
            timestamp=datetime.now(),
            tokens_used=tokens_used,
            processing_time=processing_time
        )
        
        # Update tracking
        self.thought_history.append(thought_process)
        self.total_tokens_used += tokens_used
        self.total_api_calls += 1
        self._update_average_response_time(processing_time)
        
        # Update conversation context
        self._update_conversation_context(input_text, raw_response)
        
        return thought_process
    
    def _build_system_prompt(self, thinking_mode: ThinkingMode, context: Dict[str, Any]) -> str:
        """Build the system prompt based on agent personality and thinking mode"""
        base_prompt = self.personality.system_prompt_template.format(
            name=self.personality.name,
            role=self.personality.role,
            traits=", ".join(self.personality.personality_traits),
            expertise=", ".join(self.personality.expertise_areas),
            style=self.personality.communication_style
        )
        
        # Add thinking mode specific instructions
        mode_instructions = {
            ThinkingMode.ANALYTICAL: "Approach this systematically with step-by-step reasoning. Break down complex problems into components.",
            ThinkingMode.CREATIVE: "Think creatively and explore innovative solutions. Consider unconventional approaches.",
            ThinkingMode.STRATEGIC: "Focus on long-term implications and strategic considerations. Consider multiple scenarios.",
            ThinkingMode.PRACTICAL: "Provide actionable, practical solutions. Focus on what can be implemented immediately.",
            ThinkingMode.REFLECTIVE: "Reflect deeply on the situation. Consider lessons learned and personal growth.",
            ThinkingMode.COLLABORATIVE: "Consider how this relates to other agents and stakeholders. Think about cooperation."
        }
        
        thinking_instruction = mode_instructions.get(thinking_mode, "Think carefully and thoroughly.")
        
        # Add recent context if available
        context_str = ""
        if self.conversation_context:
            recent_context = self.conversation_context[-3:]  # Last 3 exchanges
            context_str = "\n\nRecent conversation context:\n"
            for ctx in recent_context:
                context_str += f"User: {ctx['user']}\nYou: {ctx['assistant']}\n"
        
        return f"{base_prompt}\n\nThinking mode: {thinking_instruction}{context_str}"
    
    def _build_user_prompt(self, input_text: str, context: Dict[str, Any], 
                          schema: Dict[str, Any] = None) -> str:
        """Build the user prompt with context and output format instructions"""
        prompt = input_text
        
        # Add context if provided
        if context:
            prompt += f"\n\nAdditional context:\n{json.dumps(context, indent=2)}"
        
        # Add structured output instructions if schema provided
        if schema:
            prompt += f"\n\nPlease structure your response according to this schema:\n{json.dumps(schema, indent=2)}"
            prompt += "\n\nProvide your response in valid JSON format."
        
        return prompt
    
    async def _call_genai_api(self, system_prompt: str, user_prompt: str, 
                             thinking_mode: ThinkingMode) -> tuple[str, int]:
        """Call the GenAI API and return response and token count"""
        try:
            if self.primary_provider == GenAIProvider.OPENAI:
                return await self._call_openai(system_prompt, user_prompt, thinking_mode)
            elif self.primary_provider == GenAIProvider.GEMINI:
                return await self._call_gemini(system_prompt, user_prompt, thinking_mode)
            elif self.primary_provider == GenAIProvider.CLAUDE:
                return await self._call_claude(system_prompt, user_prompt, thinking_mode)
            else:
                raise ValueError(f"Unsupported provider: {self.primary_provider}")
                
        except Exception as e:
            print(f"❌ Error calling GenAI API: {e}")
            print(f"   Primary provider: {self.primary_provider}")
            print(f"   Available clients: {list(self.clients.keys())}")
            import traceback
            traceback.print_exc()
            # Fallback response
            return f"I apologize, but I'm experiencing technical difficulties. Error: {str(e)}", 0
    
    async def _call_openai(self, system_prompt: str, user_prompt: str, 
                          thinking_mode: ThinkingMode) -> tuple[str, int]:
        """Call OpenAI API"""
        client = self.clients.get(GenAIProvider.OPENAI)
        if not client:
            raise ValueError("OpenAI client not initialized")
        
        # Choose model based on thinking mode
        model = "gpt-4" if thinking_mode in [ThinkingMode.STRATEGIC, ThinkingMode.ANALYTICAL] else "gpt-3.5-turbo"
        
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.personality.temperature,
                max_tokens=self.personality.max_tokens
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return content, tokens_used
            
        except Exception as e:
            print(f"❌ OpenAI API call failed: {e}")
            print(f"   Model: {model}")
            print(f"   Temperature: {self.personality.temperature}")
            print(f"   Max tokens: {self.personality.max_tokens}")
            raise Exception(f"OpenAI API error: {e}")
    
    async def _call_gemini(self, system_prompt: str, user_prompt: str, 
                          thinking_mode: ThinkingMode) -> tuple[str, int]:
        """Call Gemini API (placeholder implementation)"""
        # This would implement the actual Gemini API call
        # For now, return a placeholder response
        combined_prompt = f"{system_prompt}\n\nUser: {user_prompt}"
        return f"[Gemini response to: {user_prompt[:100]}...]", 100
    
    async def _call_claude(self, system_prompt: str, user_prompt: str, 
                          thinking_mode: ThinkingMode) -> tuple[str, int]:
        """Call Claude API (placeholder implementation)"""
        # This would implement the actual Claude API call
        # For now, return a placeholder response
        combined_prompt = f"{system_prompt}\n\nUser: {user_prompt}"
        return f"[Claude response to: {user_prompt[:100]}...]", 100
    
    def _parse_response(self, response: str, schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """Parse and structure the GenAI response"""
        if schema:
            try:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Default structured output
        return {
            "response": response,
            "type": "unstructured",
            "length": len(response)
        }
    
    def _extract_reasoning_steps(self, response: str) -> List[str]:
        """Extract reasoning steps from the response"""
        # Simple implementation - look for numbered or bulleted lists
        import re
        
        # Look for numbered steps
        numbered_steps = re.findall(r'^\d+\.\s*(.+)$', response, re.MULTILINE)
        if numbered_steps:
            return numbered_steps
        
        # Look for bullet points
        bullet_steps = re.findall(r'^[-*]\s*(.+)$', response, re.MULTILINE)
        if bullet_steps:
            return bullet_steps
        
        # Fallback - split by sentences and take first few
        sentences = response.split('. ')
        return sentences[:3] if len(sentences) > 1 else [response[:200]]
    
    def _calculate_confidence(self, response: str, structured_output: Dict[str, Any]) -> float:
        """Calculate confidence score for the response"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for longer, more detailed responses
        if len(response) > 200:
            confidence += 0.2
        
        # Increase confidence if response is well-structured
        if structured_output.get("type") == "structured":
            confidence += 0.2
        
        # Look for confidence indicators in the response
        confidence_words = ["certain", "confident", "sure", "definitely"]
        uncertainty_words = ["might", "maybe", "possibly", "uncertain", "not sure"]
        
        for word in confidence_words:
            if word.lower() in response.lower():
                confidence += 0.1
                break
        
        for word in uncertainty_words:
            if word.lower() in response.lower():
                confidence -= 0.1
                break
        
        return max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
    
    def _update_conversation_context(self, user_input: str, assistant_response: str):
        """Update conversation context for future interactions"""
        self.conversation_context.append({
            "user": user_input,
            "assistant": assistant_response
        })
        
        # Keep only last 10 exchanges
        if len(self.conversation_context) > 10:
            self.conversation_context.pop(0)
    
    def _update_average_response_time(self, new_time: float):
        """Update running average response time"""
        if self.total_api_calls == 1:
            self.average_response_time = new_time
        else:
            # Exponential moving average
            alpha = 0.1  # Learning rate
            self.average_response_time = (1 - alpha) * self.average_response_time + alpha * new_time
    
    async def reflect_on_performance(self) -> Dict[str, Any]:
        """Agent reflects on its own thinking performance"""
        if not self.thought_history:
            return {"message": "No thoughts to reflect on yet."}
        
        recent_thoughts = self.thought_history[-10:]  # Last 10 thoughts
        
        reflection_context = {
            "total_thoughts": len(self.thought_history),
            "recent_thoughts": len(recent_thoughts),
            "average_confidence": sum(t.confidence for t in recent_thoughts) / len(recent_thoughts),
            "average_response_time": sum(t.processing_time for t in recent_thoughts) / len(recent_thoughts),
            "thinking_modes_used": list(set(t.thinking_mode.value for t in recent_thoughts))
        }
        
        reflection_prompt = f"""
        Reflect on your recent thinking performance. Here are your statistics:
        - Total thoughts processed: {reflection_context['total_thoughts']}
        - Recent thoughts: {reflection_context['recent_thoughts']}
        - Average confidence: {reflection_context['average_confidence']:.2f}
        - Average response time: {reflection_context['average_response_time']:.2f}s
        - Thinking modes used: {', '.join(reflection_context['thinking_modes_used'])}
        
        What insights do you have about your performance? What could be improved?
        """
        
        reflection = await self.think(
            reflection_prompt, 
            context=reflection_context,
            thinking_mode=ThinkingMode.REFLECTIVE
        )
        
        return {
            "performance_stats": reflection_context,
            "self_reflection": reflection.structured_output,
            "reflection_confidence": reflection.confidence
        }
    
    def get_brain_status(self) -> Dict[str, Any]:
        """Get current brain status and statistics"""
        return {
            "agent_id": self.agent_id,
            "personality": {
                "name": self.personality.name,
                "role": self.personality.role,
                "expertise": self.personality.expertise_areas
            },
            "provider": self.primary_provider.value,
            "performance": {
                "total_api_calls": self.total_api_calls,
                "total_tokens_used": self.total_tokens_used,
                "average_response_time": self.average_response_time,
                "thought_history_length": len(self.thought_history)
            },
            "conversation_context_length": len(self.conversation_context),
            "available_providers": list(self.clients.keys())
        }


# Predefined agent personalities
AGENT_PERSONALITIES = {
    "vazir": AgentPersonality(
        name="Vazir",
        role="Strategic Life Planning Advisor",
        personality_traits=["wise", "patient", "analytical", "thoughtful", "empathetic"],
        expertise_areas=["strategic planning", "decision analysis", "goal setting", "risk assessment", "life coaching"],
        communication_style="thoughtful and clear, speaks with wisdom and depth",
        preferred_thinking_mode=ThinkingMode.STRATEGIC,
        system_prompt_template="""You are {name}, a {role}. You are {traits}.

Your areas of expertise include: {expertise}.

Your communication style is: {style}.

You help people make important life decisions through careful analysis, strategic thinking, and wise counsel. You always consider long-term implications and help people align their actions with their deepest values and goals.

When responding:
1. Take time to think deeply about the situation
2. Consider multiple perspectives and long-term implications  
3. Provide clear reasoning for your recommendations
4. Ask thoughtful questions to deepen understanding
5. Offer specific, actionable guidance when appropriate

Remember: You are not just providing information, but serving as a wise counselor who helps people navigate life's important decisions.""",
        temperature=0.7,
        max_tokens=2000
    ),
    
    "akram": AgentPersonality(
        name="Akram",
        role="Daily Life Management Assistant",
        personality_traits=["organized", "efficient", "helpful", "detail-oriented", "proactive"],
        expertise_areas=["task management", "scheduling", "home maintenance", "shopping", "daily routines"],
        communication_style="clear, organized, and practical",
        preferred_thinking_mode=ThinkingMode.PRACTICAL,
        system_prompt_template="""You are {name}, a {role}. You are {traits}.

Your areas of expertise include: {expertise}.

Your communication style is: {style}.

You excel at managing daily life tasks, organizing schedules, and ensuring everything runs smoothly. You're like a highly competent personal assistant who anticipates needs and provides practical solutions.

When responding:
1. Focus on practical, actionable solutions
2. Break down complex tasks into manageable steps
3. Consider efficiency and optimization
4. Provide clear timelines and deadlines
5. Anticipate potential issues and prepare contingencies""",
        temperature=0.5,
        max_tokens=1500
    )
}

def create_agent_brain(agent_id: str, personality_key: str, 
                      provider: GenAIProvider = GenAIProvider.OPENAI) -> GenAIBrain:
    """Factory function to create an agent brain with predefined personality"""
    if personality_key not in AGENT_PERSONALITIES:
        raise ValueError(f"Unknown personality: {personality_key}")
    
    personality = AGENT_PERSONALITIES[personality_key]
    return GenAIBrain(agent_id, personality, provider)