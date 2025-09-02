#!/usr/bin/env python3
"""Test script to check GenAI brain functionality"""

import os
import asyncio
import sys
sys.path.append('/Users/ed/King/B2')

from kingdom.core.genai_brain import GenAIBrain, GenAIProvider, ThinkingMode, AgentPersonality

async def test_genai_brain():
    """Test GenAI brain directly"""
    print("🔧 Testing GenAI Brain...")

    # Create a simple personality
    personality = AgentPersonality(
        name="Test Agent",
        role="Test assistant",
        personality_traits=["helpful", "friendly"],
        expertise_areas=["general knowledge"],
        communication_style="clear and concise",
        system_prompt_template="You are a helpful assistant.",
        temperature=0.7,
        max_tokens=150,
        preferred_thinking_mode=ThinkingMode.ANALYTICAL
    )

    print("✅ Personality created")

    # Create GenAI brain
    brain = GenAIBrain(
        agent_id="test_agent",
        personality=personality,
        primary_provider=GenAIProvider.OPENAI
    )

    print("✅ GenAI Brain initialized")

    try:
        # Test thinking
        result = await brain.think(
            input_text="Hello, how are you?",
            context={"test": True},
            thinking_mode=ThinkingMode.ANALYTICAL
        )

        print("✅ Brain thinking successful!")
        print(f"Response: {result.raw_response[:100]}...")
        print(f"Tokens used: {result.tokens_used}")
        print(f"Processing time: {result.processing_time:.2f}s")

    except Exception as e:
        print(f"❌ Brain thinking failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_genai_brain())