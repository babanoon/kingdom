#!/usr/bin/env python3
"""
Test Runner for Kingdom Tester Agents

Demonstrates:
- Parallel agent execution
- Database operations (CRUD)
- A2A communication between agents
- Task queue management
- Service monitoring
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append('/Users/ed/King/B2')

from kingdom.service.agent_service import KingdomAgentService, TaskMessage

class TestRunner:
    """Test runner for demonstrating agent capabilities"""
    
    def __init__(self):
        self.service = KingdomAgentService()
        self.test_results = []
        
    async def run_comprehensive_test(self):
        """Run comprehensive test of all agent capabilities"""
        print("🚀 Starting Kingdom Tester Agent Service Test")
        print("=" * 60)
        
        try:
            # Start the service
            await self.service.start_service()
            
            # Wait for agents to initialize
            await asyncio.sleep(2)
            
            # Run test phases
            await self._test_phase_1_database_operations()
            await self._test_phase_2_a2a_communication()
            await self._test_phase_3_parallel_tasks()
            await self._test_phase_4_google_adk()
            
            # Wait for all tasks to complete
            await asyncio.sleep(3)
            
            # Get final service status
            await self._show_final_status()
            
        except Exception as e:
            logging.error(f"Test runner failed: {e}")
            raise
        finally:
            # Stop the service
            await self.service.stop_service()
            print("\n✅ Test completed - Service stopped")

    async def _test_phase_1_database_operations(self):
        """Test Phase 1: Database CRUD operations"""
        print("\n📊 Phase 1: Database Operations Testing")
        print("-" * 40)
        
        # Test 1: Insert data
        insert_task_id = await self.service.submit_task(
            task_type="db_insert",
            payload={"data": {"test_name": "phase1_insert", "value": 42}},
            agent_id="tester1_001"
        )
        print(f"✓ Submitted database insert task: {insert_task_id}")
        
        # Test 2: Read data  
        await asyncio.sleep(1)  # Let insert complete
        read_task_id = await self.service.submit_task(
            task_type="db_read",
            payload={"limit": 5},
            agent_id="tester1_001"
        )
        print(f"✓ Submitted database read task: {read_task_id}")
        
        # Test 3: Insert more data for testing
        insert_task_id_2 = await self.service.submit_task(
            task_type="db_insert", 
            payload={"data": {"test_name": "phase1_insert_2", "batch": "test_batch_1"}},
            agent_id="tester1_002"  # Different agent
        )
        print(f"✓ Submitted second database insert task: {insert_task_id_2}")

    async def _test_phase_2_a2a_communication(self):
        """Test Phase 2: Agent-to-Agent Communication"""
        print("\n💬 Phase 2: A2A Communication Testing") 
        print("-" * 40)
        
        # Test 1: Tester1 sends message to Tester2
        a2a_task_id_1 = await self.service.submit_task(
            task_type="send_test_message",
            payload={
                "recipient_id": "tester2_001",
                "message": "Hello from Tester1! Testing A2A communication."
            },
            agent_id="tester1_001"
        )
        print(f"✓ Submitted A2A message task (tester1→tester2): {a2a_task_id_1}")
        
        # Test 2: Tester2 initiates communication test
        await asyncio.sleep(0.5)  # Small delay
        a2a_task_id_2 = await self.service.submit_task(
            task_type="test_a2a_communication",
            payload={
                "target_agent": "tester1_002",
                "message": "Communication validation test from Tester2"
            },
            agent_id="tester2_001"
        )
        print(f"✓ Submitted A2A communication test: {a2a_task_id_2}")
        
        # Test 3: Broadcast test
        broadcast_task_id = await self.service.submit_task(
            task_type="send_broadcast_test",
            payload={
                "target_agents": ["tester1_001", "tester1_002"],
                "message": "Broadcast test message from Tester2"
            },
            agent_id="tester2_002"
        )
        print(f"✓ Submitted broadcast test: {broadcast_task_id}")

    async def _test_phase_3_parallel_tasks(self):
        """Test Phase 3: Parallel task execution"""
        print("\n⚡ Phase 3: Parallel Task Execution Testing")
        print("-" * 40)
        
        # Submit multiple tasks simultaneously to test parallel execution
        parallel_tasks = []
        
        # Multiple database operations
        for i in range(5):
            task_id = await self.service.submit_task(
                task_type="db_insert",
                payload={"data": {"parallel_test": f"task_{i}", "batch": "parallel_batch"}},
                priority=3
            )
            parallel_tasks.append(task_id)
        
        # Multiple A2A messages
        for i in range(3):
            task_id = await self.service.submit_task(
                task_type="send_test_message",
                payload={
                    "recipient_id": f"tester2_00{(i % 2) + 1}",
                    "message": f"Parallel message {i}"
                }
            )
            parallel_tasks.append(task_id)
        
        print(f"✓ Submitted {len(parallel_tasks)} parallel tasks")

    async def _test_phase_4_google_adk(self):
        """Test Phase 4: Google ADK Testing"""
        print("\n🔧 Phase 4: Google ADK Integration Testing")
        print("-" * 40)
        
        # Test Google ADK functionality
        adk_task_id = await self.service.submit_task(
            task_type="test_google_adk",
            payload={"test_type": "integration_test"},
            agent_id="tester1_001"
        )
        print(f"✓ Submitted Google ADK test: {adk_task_id}")
        
        # Test communication validation
        validation_task_id = await self.service.submit_task(
            task_type="validate_communication",
            payload={},
            agent_id="tester2_001"
        )
        print(f"✓ Submitted communication validation: {validation_task_id}")

    async def _show_final_status(self):
        """Show final service and agent status"""
        print("\n📋 Final Status Report")
        print("=" * 60)
        
        status = await self.service.get_service_status()
        
        print(f"Service Status: {status['service_status']}")
        print(f"Task Queue: {status['task_queue']}")
        print(f"A2A Messages: {status['a2a_messages']}")
        
        print("\nAgent Status:")
        for agent_id, agent_status in status['agents'].items():
            print(f"  {agent_id}: {agent_status['status']} "
                  f"({agent_status['task_count']} tasks completed, "
                  f"{agent_status['uptime_seconds']:.1f}s uptime)")

async def main():
    """Main test runner function"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run test
    test_runner = TestRunner()
    
    try:
        await test_runner.run_comprehensive_test()
        print("\n🎉 All tests completed successfully!")
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())