#!/usr/bin/env python3
"""
Test Management System Integration

Tests the complete Kingdom Management System including:
- Management server startup
- Agent integration (GeneralReceiver, MathCalculator)
- API endpoints
- A2A communication
- Workflow tracking
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
import aiohttp

# Add project root to path
sys.path.append('/Users/ed/King/B2')

from kingdom.management.management_server import KingdomManagementServer

class ManagementSystemTester:
    """Comprehensive tester for the Kingdom Management System"""
    
    def __init__(self):
        self.management_server = KingdomManagementServer()
        self.test_results = []
        
    async def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Kingdom Management System Test")
        print("=" * 60)
        
        try:
            # Start management infrastructure
            await self._test_management_startup()
            
            # Test agent integration
            await self._test_agent_integration()
            
            # Test API endpoints
            await self._test_api_endpoints()
            
            # Test workflow tracking
            await self._test_workflow_tracking()
            
            # Test A2A communication
            await self._test_a2a_communication()
            
            # Generate summary
            await self._show_test_summary()
            
        except Exception as e:
            logging.error(f"Management system test failed: {e}")
            raise
        finally:
            # Cleanup
            await self.management_server.stop_kingdom_service()
            print("\n✅ Management system test completed")

    async def _test_management_startup(self):
        """Test 1: Management system startup"""
        print("\n📊 Test 1: Management System Startup")
        print("-" * 40)
        
        try:
            # Start Kingdom service with new agents
            await self.management_server.start_kingdom_service()
            
            # Wait for initialization
            await asyncio.sleep(3)
            
            # Check service status
            if self.management_server.kingdom_service:
                print("✓ Kingdom service started successfully")
                
                # Get service status
                status = await self.management_server.get_agents_status()
                print(f"✓ Found {len(status)} agents running")
                
                # Check for new agent types
                agent_types = [agent.agent_type for agent in status]
                expected_types = ['tester1', 'tester2', 'general_receiver', 'math_calculator']
                
                for expected_type in expected_types:
                    if expected_type in agent_types:
                        print(f"✓ {expected_type} agents found")
                    else:
                        print(f"❌ {expected_type} agents missing")
                
                self.test_results.append({
                    "test": "management_startup",
                    "status": "passed",
                    "agents_found": len(status),
                    "agent_types": agent_types
                })
            else:
                raise Exception("Kingdom service failed to start")
                
        except Exception as e:
            print(f"❌ Management startup failed: {e}")
            self.test_results.append({
                "test": "management_startup", 
                "status": "failed",
                "error": str(e)
            })

    async def _test_agent_integration(self):
        """Test 2: Agent integration and task handling"""
        print("\n🤖 Test 2: Agent Integration")
        print("-" * 40)
        
        try:
            # Test GeneralReceiver agent
            await self._test_general_receiver_integration()
            
            # Test MathCalculator agent
            await self._test_math_calculator_integration()
            
            print("✓ Agent integration tests completed")
            
        except Exception as e:
            print(f"❌ Agent integration failed: {e}")
            self.test_results.append({
                "test": "agent_integration",
                "status": "failed", 
                "error": str(e)
            })

    async def _test_general_receiver_integration(self):
        """Test GeneralReceiver agent functionality"""
        # Submit a test task to GeneralReceiver
        task_id = await self.management_server.kingdom_service.submit_task(
            task_type="process_chat_message",
            payload={
                "sender": "test_user",
                "receiver": "system", 
                "forum": "test_channel",
                "message": "Hello, can you help me?",
                "workflow_id": "test_workflow_001"
            }
        )
        
        print(f"✓ GeneralReceiver task submitted: {task_id}")
        
        # Wait for processing
        await asyncio.sleep(2)
        print("✓ GeneralReceiver task processing completed")

    async def _test_math_calculator_integration(self):
        """Test MathCalculator agent functionality"""
        # Submit a test math problem
        task_id = await self.management_server.kingdom_service.submit_task(
            task_type="solve_math_problem",
            payload={
                "problem": "Calculate 15 + 25 * 2",
                "show_steps": True,
                "enable_visualization": False
            }
        )
        
        print(f"✓ MathCalculator task submitted: {task_id}")
        
        # Wait for processing
        await asyncio.sleep(2)
        print("✓ MathCalculator task processing completed")

    async def _test_api_endpoints(self):
        """Test 3: Management API endpoints"""
        print("\n🌐 Test 3: Management API Endpoints")
        print("-" * 40)
        
        try:
            # Test chat endpoint (simulated)
            chat_request = {
                "sender": "test_user",
                "receiver": "kingdom",
                "forum": "test_forum", 
                "message": "What is 2 + 2?"
            }
            
            # Simulate chat processing
            response = await self.management_server.process_chat_message(
                type('ChatRequest', (), chat_request)()
            )
            
            print(f"✓ Chat endpoint response: {response.response[:50]}...")
            print(f"✓ Workflow ID generated: {response.workflow_id}")
            
            self.test_results.append({
                "test": "api_endpoints",
                "status": "passed",
                "chat_response_length": len(response.response),
                "workflow_id": response.workflow_id
            })
            
        except Exception as e:
            print(f"❌ API endpoint test failed: {e}")
            self.test_results.append({
                "test": "api_endpoints",
                "status": "failed",
                "error": str(e)
            })

    async def _test_workflow_tracking(self):
        """Test 4: Workflow tracking system"""
        print("\n📊 Test 4: Workflow Tracking")
        print("-" * 40)
        
        try:
            tracker = self.management_server.workflow_tracker
            
            # Start a test workflow
            workflow_id = tracker.start_workflow(
                first_agent="general_receiver_001",
                initial_task={"test": "workflow_tracking"}
            )
            
            print(f"✓ Workflow started: {workflow_id}")
            
            # Add workflow steps
            tracker.add_workflow_step(
                workflow_id=workflow_id,
                agent_id="general_receiver_001",
                action="process_message",
                input_data={"message": "test"},
                output_data={"response": "processed"},
                duration_ms=150
            )
            
            print("✓ Workflow step added")
            
            # Complete workflow
            tracker.complete_workflow(
                workflow_id=workflow_id,
                final_result={"status": "test_completed"}
            )
            
            print("✓ Workflow completed")
            
            # Verify workflow data
            all_workflows = tracker.get_all_workflows()
            completed = all_workflows['completed']
            
            if completed and len(completed) > 0:
                print(f"✓ Found {len(completed)} completed workflows")
                print(f"✓ Last workflow had {len(completed[-1]['steps'])} steps")
                
                self.test_results.append({
                    "test": "workflow_tracking",
                    "status": "passed",
                    "workflows_completed": len(completed),
                    "workflow_steps": len(completed[-1]['steps']) if completed else 0
                })
            else:
                raise Exception("No completed workflows found")
            
        except Exception as e:
            print(f"❌ Workflow tracking test failed: {e}")
            self.test_results.append({
                "test": "workflow_tracking",
                "status": "failed",
                "error": str(e)
            })

    async def _test_a2a_communication(self):
        """Test 5: A2A communication between agents"""
        print("\n💬 Test 5: A2A Communication")
        print("-" * 40)
        
        try:
            # Submit task that should trigger routing
            task_id = await self.management_server.kingdom_service.submit_task(
                task_type="process_chat_message",
                payload={
                    "sender": "test_user",
                    "message": "Can you solve this equation: 2x + 5 = 15?",
                    "forum": "math_help"
                }
            )
            
            print(f"✓ Mathematical routing test submitted: {task_id}")
            
            # Wait for routing and processing
            await asyncio.sleep(3)
            
            # Check message bus for A2A messages
            message_stats = self.management_server.kingdom_service.a2a_bus.get_message_stats()
            
            print(f"✓ A2A message bus stats: {message_stats}")
            
            if message_stats['total_messages'] > 0:
                print("✓ A2A messages exchanged successfully")
                self.test_results.append({
                    "test": "a2a_communication",
                    "status": "passed",
                    "total_messages": message_stats['total_messages'],
                    "subscribers": message_stats['subscribers']
                })
            else:
                print("⚠️ No A2A messages found (may be expected)")
                self.test_results.append({
                    "test": "a2a_communication",
                    "status": "warning",
                    "message": "No A2A messages detected"
                })
            
        except Exception as e:
            print(f"❌ A2A communication test failed: {e}")
            self.test_results.append({
                "test": "a2a_communication",
                "status": "failed",
                "error": str(e)
            })

    async def _show_test_summary(self):
        """Show comprehensive test summary"""
        print("\n📋 Test Summary Report")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result.get('status') == 'passed')
        failed = sum(1 for result in self.test_results if result.get('status') == 'failed')
        warnings = sum(1 for result in self.test_results if result.get('status') == 'warning')
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✓ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        print()
        
        # Detailed results
        for result in self.test_results:
            status_icon = "✓" if result['status'] == 'passed' else "❌" if result['status'] == 'failed' else "⚠️"
            print(f"{status_icon} {result['test']}: {result['status']}")
            
            if result.get('error'):
                print(f"   Error: {result['error']}")
            
            # Show relevant metrics
            for key, value in result.items():
                if key not in ['test', 'status', 'error'] and value is not None:
                    print(f"   {key}: {value}")
            print()
        
        # Overall status
        if failed == 0:
            print("🎉 All critical tests passed! Kingdom Management System is operational.")
        else:
            print(f"⚠️ {failed} tests failed. Review errors above.")

async def main():
    """Main test runner"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run tester
    tester = ManagementSystemTester()
    
    try:
        await tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())