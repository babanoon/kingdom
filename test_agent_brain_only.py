#!/usr/bin/env python3
"""Test script to check agent brain functionality"""

import os
import asyncio
import sys
sys.path.append('/Users/ed/King/B2')

from kingdom.agents.general_receiver.agent import GeneralReceiverAgent

async def test_agent_brain():
    """Test just the agent's brain without full initialization"""
    print("🔧 Testing Agent Brain only...")

    # Create agent without full initialization
    agent = GeneralReceiverAgent("test_agent_001", "general_receiver")
    print("✅ Agent created")

    # The brain should already be initialized in __init__
    print("✅ Brain should be initialized")

    try:
        # Test the brain directly
        result = await agent.brain.think(
            input_text="Hello",
            context={"test": True},
            thinking_mode=agent.brain.personality.preferred_thinking_mode
        )

        print("✅ Brain thinking successful!")
        print(f"Response: {result.raw_response[:100]}...")
        print(f"Tokens used: {result.tokens_used}")

    except Exception as e:
        print(f"❌ Brain thinking failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_brain())