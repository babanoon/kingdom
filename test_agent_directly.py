#!/usr/bin/env python3
"""Test script to check agent functionality directly"""

import os
import asyncio
import sys
sys.path.append('/Users/ed/King/B2')

from kingdom.agents.general_receiver.agent import GeneralReceiverAgent

async def test_agent_directly():
    """Test the general_receiver agent directly"""
    print("🔧 Testing GeneralReceiver Agent directly...")

    # Create agent
    agent = GeneralReceiverAgent("test_agent_001", "general_receiver")
    print("✅ Agent created")

    # Initialize agent for service (mock dependencies)
    await agent.initialize_for_service(
        task_queue=None,
        a2a_bus=None,
        db_pool=None
    )
    print("✅ Agent initialized")

    # Create a simple task
    from kingdom.service.agent_service import TaskMessage
    task = TaskMessage(
        task_id="test_task_001",
        agent_id="test_agent_001",
        task_type="process_chat_message",
        payload={
            "sender": "test_user",
            "message": "Hello",
            "forum": "general",
            "workflow_id": "test_workflow"
        },
        priority=5
    )

    print("✅ Task created")

    try:
        # Process the task
        result = await agent._handle_task(task)
        print("✅ Task processed successfully!")
        print(f"Result: {result}")

    except Exception as e:
        print(f"❌ Task processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_directly())