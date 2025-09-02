#!/usr/bin/env python3
"""Test script to check service task processing"""

import os
import asyncio
import sys
sys.path.append('/Users/ed/King/B2')

from kingdom.service.agent_service import KingdomAgentService

async def test_service_task():
    """Test service task processing"""
    print("🔧 Testing Service Task Processing...")

    # Create service
    service = KingdomAgentService()
    print("✅ Service created")

    # Start service
    await service.start_service()
    print("✅ Service started")

    try:
        # Submit a simple task
        task_id = await service.submit_task(
            task_type="process_chat_message",
            payload={
                "sender": "test_user",
                "receiver": "kingdom",
                "forum": "general_help",
                "message": "Hello",
                "workflow_id": "test_workflow"
            }
        )
        print(f"✅ Task submitted: {task_id}")

        # Wait for completion
        result = await service.wait_for_task_completion(task_id, timeout=10.0)
        print("✅ Task completed!")
        print(f"Result: {result}")

    except Exception as e:
        print(f"❌ Task processing failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Stop service
        await service.stop_service()

if __name__ == "__main__":
    asyncio.run(test_service_task())