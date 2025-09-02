#!/usr/bin/env python3
"""
Test script for the Kingdom agent system

This script tests the basic functionality of the Kingdom system
to ensure all components are working properly.
"""

import asyncio
import sys
from pathlib import Path

# Add kingdom to path
sys.path.append(str(Path(__file__).parent))

from kingdom.kingdom_main import KingdomSystem

async def test_kingdom_system():
    """Test the Kingdom system basic functionality"""
    print("🧪 Starting Kingdom System Test")
    print("=" * 50)
    
    kingdom = KingdomSystem()
    
    try:
        # Test initialization
        print("📋 Testing system initialization...")
        await kingdom.initialize()
        print("✅ System initialization successful")
        
        # Test system startup
        print("\n🚀 Testing system startup...")
        await kingdom.start()
        print("✅ System startup successful")
        
        # Test system status
        print("\n📊 Testing system status...")
        status = kingdom.get_system_status()
        print(f"System Status: {status['status']}")
        print(f"Active Agents: {len(status['active_agents'])}")
        for agent_id, agent_info in status['active_agents'].items():
            print(f"  - {agent_info['name']} ({agent_info['type']}): {agent_info['status']}")
        
        # Test Vazir interaction
        print("\n🧙 Testing Vazir interaction...")
        
        # Test general guidance
        response1 = await kingdom.interact_with_vazir(
            "What should I consider when making important life decisions?",
            "general_guidance"
        )
        
        if response1.get("success"):
            print("✅ General guidance test successful")
            result = response1["response"]
            if "wisdom" in result:
                print(f"Vazir's wisdom: {result['wisdom']}")
        else:
            print(f"❌ General guidance test failed: {response1.get('error')}")
        
        # Test strategic planning
        print("\n📈 Testing strategic planning...")
        response2 = await kingdom.interact_with_vazir(
            "Help me create a 5-year strategic plan",
            "strategic_plan"
        )
        
        if response2.get("success"):
            print("✅ Strategic planning test successful")
            result = response2["response"]
            if "strategic_objectives" in result:
                print(f"Strategic objectives created: {len(result['strategic_objectives'])}")
        else:
            print(f"❌ Strategic planning test failed: {response2.get('error')}")
        
        # Test decision analysis
        print("\n🤔 Testing decision analysis...")
        response3 = await kingdom.interact_with_vazir(
            "Should I change careers or stay in my current job?",
            "decision_analysis"
        )
        
        if response3.get("success"):
            print("✅ Decision analysis test successful")
            result = response3["response"]
            if "options_analysis" in result:
                print(f"Options analyzed: {len(result['options_analysis'])}")
        else:
            print(f"❌ Decision analysis test failed: {response3.get('error')}")
        
        print("\n🎉 All tests completed!")
        
        # Wait a moment to see system in action
        print("\n⏰ Waiting 10 seconds to observe system operation...")
        await asyncio.sleep(10)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean shutdown
        print("\n🛑 Shutting down system...")
        await kingdom.shutdown()
        print("✅ Test complete")

async def test_components_individually():
    """Test individual components"""
    print("\n🔧 Testing Individual Components")
    print("=" * 40)
    
    # Test database connection
    print("📊 Testing database connection...")
    try:
        from kingdom.memory.database_memory import DatabaseMemoryManager
        
        db_config = {
            "host": "localhost",
            "port": 9876,
            "database": "general2613",
            "user": "kadmin",
            "password": "securepasswordkossher123"
        }
        
        memory_manager = DatabaseMemoryManager(db_config)
        await memory_manager.connect()
        print("✅ Database connection successful")
        await memory_manager.disconnect()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    # Test logging system
    print("\n📝 Testing logging system...")
    try:
        from kingdom.core.logging_system import get_kingdom_logger, LogCategory, LogLevel
        
        logger = get_kingdom_logger()
        await logger.start_logging()
        
        await logger.info(LogCategory.SYSTEM, "Test log message", "test_agent")
        print("✅ Logging system test successful")
        
        await logger.stop_logging()
        
    except Exception as e:
        print(f"❌ Logging system test failed: {e}")
    
    # Test security system
    print("\n🔒 Testing security system...")
    try:
        from kingdom.security.agent_security import get_security_manager, SecurityLevel
        
        security_manager = get_security_manager()
        context = await security_manager.create_security_context("test_agent", SecurityLevel.STANDARD)
        print("✅ Security system test successful")
        
    except Exception as e:
        print(f"❌ Security system test failed: {e}")

if __name__ == "__main__":
    print("🏰 Kingdom System Test Suite")
    print("=" * 60)
    
    # Run component tests first
    asyncio.run(test_components_individually())
    
    # Then run full system test
    asyncio.run(test_kingdom_system())
    
    print("\n👋 Test suite complete!")