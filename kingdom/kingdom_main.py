#!/usr/bin/env python3
"""
Kingdom Main System - Deos Orchestrator

This is the main entry point and orchestrator for the Kingdom agent system.
It initializes all components, starts agents, and manages the overall system lifecycle.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Kingdom system imports
from .core.agent_registry import get_registry, initialize_kingdom, shutdown_kingdom
from .core.base_agent import AgentType, AgentConfig, AgentCapability
from .core.logging_system import get_kingdom_logger, initialize_logging_system
from .security.agent_security import get_security_manager, initialize_security_system
from .memory.database_memory import DatabaseMemoryManager, AgentMemoryInterface
from .communication.markdown_system import MarkdownCommunicationSystem
from .agents.vazir_agent import VazirAgent

# Database config from existing B2 system
from pathlib import Path
import json

class KingdomSystem:
    """
    Main Kingdom System Orchestrator (Deos)
    
    This is the central orchestrator that manages all agents, systems, and operations
    in the Kingdom project. It represents "Deos" - the super system that orchestrates
    all other agents and maintains the second brain functionality.
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "./kingdom/config/kingdom_config.json"
        self.config = self._load_config()
        
        # Core system components
        self.agent_registry = None
        self.kingdom_logger = None
        self.security_manager = None
        self.memory_manager = None
        self.communication_system = None
        
        # System state
        self.system_started = False
        self.startup_time = None
        self.active_agents = {}
        
        print("🏰 Kingdom System (Deos) initializing...")
    
    def _load_config(self) -> Dict:
        """Load Kingdom system configuration"""
        default_config = {
            "system_name": "Kingdom (Deos)",
            "version": "1.0.0",
            "database": {
                "host": "localhost",
                "port": 9876,
                "database": "general2613",
                "user": "kadmin", 
                "password": "securepasswordkossher123"
            },
            "agents": {
                "auto_start": ["vazir"],
                "max_agents": 50
            },
            "communication": {
                "workspace_path": "./kingdom/workspace",
                "enable_markdown": True,
                "enable_rocketchat": True
            },
            "security": {
                "default_level": "standard",
                "audit_logging": True
            },
            "memory": {
                "enable_vector_search": True,
                "cache_size": 1000
            }
        }
        
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                    elif isinstance(value, dict) and isinstance(loaded_config[key], dict):
                        # Merge nested dictionaries
                        for subkey, subvalue in value.items():
                            if subkey not in loaded_config[key]:
                                loaded_config[key][subkey] = subvalue
                
                return loaded_config
            else:
                # Create default config file
                config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                print(f"📋 Created default config file: {self.config_path}")
                
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
        
        return default_config
    
    async def initialize(self):
        """Initialize all Kingdom system components"""
        print("🚀 Initializing Kingdom system components...")
        
        # Initialize logging first
        self.kingdom_logger = await initialize_logging_system()
        await self.kingdom_logger.info("Kingdom System", "Deos initialization started", "deos_001")
        
        # Initialize security system
        self.security_manager = await initialize_security_system()
        
        # Initialize memory manager
        self.memory_manager = DatabaseMemoryManager(self.config["database"])
        await self.memory_manager.connect()
        
        # Initialize communication system
        if self.config["communication"]["enable_markdown"]:
            self.communication_system = MarkdownCommunicationSystem(
                self.config["communication"]["workspace_path"]
            )
            await self.communication_system.start_monitoring()
        
        # Initialize agent registry
        self.agent_registry = await initialize_kingdom()
        
        print("✅ All Kingdom system components initialized")
    
    async def start(self):
        """Start the Kingdom system"""
        if self.system_started:
            print("⚠️  Kingdom system already started")
            return
        
        print("🏰 Starting Kingdom system...")
        self.startup_time = datetime.now()
        
        # Start core agents
        await self.start_core_agents()
        
        # Start system monitoring
        asyncio.create_task(self.system_monitoring_loop())
        
        self.system_started = True
        
        await self.kingdom_logger.info("Kingdom System", "Deos system started successfully", "deos_001")
        print("✅ Kingdom system started successfully")
        
        return True
    
    async def start_core_agents(self):
        """Start the core agents defined in configuration"""
        auto_start_agents = self.config["agents"].get("auto_start", [])
        
        print(f"🤖 Starting {len(auto_start_agents)} core agents...")
        
        for agent_name in auto_start_agents:
            try:
                if agent_name.lower() == "vazir":
                    await self.create_and_start_vazir()
                else:
                    print(f"⚠️  Unknown agent type: {agent_name}")
                    
            except Exception as e:
                print(f"❌ Error starting agent {agent_name}: {e}")
                await self.kingdom_logger.error("Agent Startup", f"Failed to start {agent_name}", "deos_001", exception=e)
    
    async def create_and_start_vazir(self):
        """Create and start Vazir agent"""
        print("🧙 Creating Vazir (Strategic Planning Agent)...")
        
        # Create Vazir agent
        vazir = VazirAgent()
        
        # Create memory interface for Vazir
        memory_interface = AgentMemoryInterface(vazir.agent_id, self.memory_manager)
        
        # Create security context
        security_context = await self.security_manager.create_security_context(
            vazir.agent_id, vazir.config.security_level
        )
        
        # Initialize Vazir with system dependencies
        await vazir.initialize(
            memory_manager=memory_interface,
            communication_system=self.communication_system
        )
        
        # Register Vazir with the system
        await self.agent_registry.register_agent(vazir)
        
        # Start Vazir
        await vazir.start()
        
        # Track active agent
        self.active_agents[vazir.agent_id] = {
            "agent": vazir,
            "memory_interface": memory_interface,
            "security_context": security_context,
            "started_at": datetime.now()
        }
        
        print("✅ Vazir agent created and started successfully")
        await self.kingdom_logger.info("Agent Management", "Vazir agent started", "deos_001", 
                                      details={"agent_id": vazir.agent_id, "type": "strategic_planning"})
    
    async def system_monitoring_loop(self):
        """Main system monitoring and health check loop"""
        while self.system_started:
            try:
                # Run system health checks every 5 minutes
                await asyncio.sleep(300)
                await self.run_health_checks()
                
            except Exception as e:
                print(f"❌ Error in system monitoring: {e}")
                await self.kingdom_logger.error("System Monitoring", "Monitoring loop error", "deos_001", exception=e)
                await asyncio.sleep(60)  # Wait before retry
    
    async def run_health_checks(self):
        """Run comprehensive system health checks"""
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "system_uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
            "active_agents": len(self.active_agents),
            "agent_registry_status": self.agent_registry.get_system_status() if self.agent_registry else "not_initialized",
            "memory_manager_status": "connected" if self.memory_manager.connection else "disconnected",
            "communication_system_status": self.communication_system.get_system_stats() if self.communication_system else "disabled",
            "security_status": self.security_manager.get_security_report() if self.security_manager else "not_initialized",
            "logging_status": self.kingdom_logger.get_system_health() if self.kingdom_logger else "not_initialized"
        }
        
        # Check individual agent health
        agent_health = {}
        for agent_id, agent_info in self.active_agents.items():
            agent = agent_info["agent"]
            agent_health[agent_id] = {
                "status": agent.status.value,
                "active_tasks": len(agent.active_tasks),
                "last_activity": agent.last_activity.isoformat(),
                "uptime_seconds": (datetime.now() - agent_info["started_at"]).total_seconds()
            }
        
        health_report["agents"] = agent_health
        
        # Log health report (only if significant issues detected)
        issues = []
        if health_report["active_agents"] == 0:
            issues.append("No active agents")
        if health_report["memory_manager_status"] != "connected":
            issues.append("Memory manager not connected")
        
        if issues:
            await self.kingdom_logger.warning("System Health", f"Health issues detected: {', '.join(issues)}", "deos_001", 
                                            details=health_report)
        else:
            # Log summary health info every hour
            if int((datetime.now() - self.startup_time).total_seconds()) % 3600 < 300:  # Within 5 minutes of hour mark
                await self.kingdom_logger.info("System Health", "System healthy", "deos_001", 
                                             details={"uptime": health_report["system_uptime_seconds"], 
                                                    "active_agents": health_report["active_agents"]})
    
    async def shutdown(self):
        """Shutdown the Kingdom system gracefully"""
        print("🛑 Shutting down Kingdom system...")
        
        await self.kingdom_logger.info("Kingdom System", "Shutdown initiated", "deos_001")
        
        # Stop all active agents
        for agent_id, agent_info in self.active_agents.items():
            try:
                agent = agent_info["agent"]
                await agent.stop()
                print(f"✅ Stopped agent: {agent.name}")
            except Exception as e:
                print(f"❌ Error stopping agent {agent_id}: {e}")
        
        # Shutdown system components
        if self.communication_system:
            await self.communication_system.stop_monitoring()
        
        if self.memory_manager:
            await self.memory_manager.disconnect()
        
        if self.agent_registry:
            await shutdown_kingdom()
        
        if self.kingdom_logger:
            await self.kingdom_logger.stop_logging()
        
        self.system_started = False
        print("✅ Kingdom system shutdown complete")
    
    async def interact_with_vazir(self, message: str, request_type: str = "general_guidance") -> Dict:
        """Direct interaction with Vazir agent"""
        if "vazir_001" not in self.active_agents:
            return {"error": "Vazir agent not active"}
        
        vazir = self.active_agents["vazir_001"]["agent"]
        
        # Create task for Vazir
        task_data = {
            "type": request_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if request_type == "strategic_plan":
            task_data.update({
                "scope": "general_life",
                "time_horizon": "5_years",
                "focus_areas": ["personal", "professional", "financial", "health"]
            })
        elif request_type == "decision_analysis":
            task_data.update({
                "title": "Decision Analysis Request",
                "context": {"user_message": message},
                "options": [{"name": "Option to analyze", "description": message}],
                "criteria": ["impact", "feasibility", "risk", "alignment"]
            })
        
        try:
            task_id = f"user_request_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            result = await vazir.execute_task(task_id, task_data)
            
            return {
                "success": True,
                "agent": "Vazir",
                "task_id": task_id,
                "response": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        if not self.system_started:
            return {"status": "stopped"}
        
        return {
            "status": "running",
            "startup_time": self.startup_time.isoformat() if self.startup_time else None,
            "active_agents": {
                agent_id: {
                    "name": info["agent"].name,
                    "type": info["agent"].agent_type.value,
                    "status": info["agent"].status.value,
                    "active_tasks": len(info["agent"].active_tasks)
                }
                for agent_id, info in self.active_agents.items()
            },
            "system_components": {
                "agent_registry": bool(self.agent_registry),
                "memory_manager": bool(self.memory_manager),
                "communication_system": bool(self.communication_system),
                "security_manager": bool(self.security_manager),
                "logging_system": bool(self.kingdom_logger)
            }
        }


async def main():
    """Main entry point for Kingdom system"""
    print("🏰 Kingdom System (Deos) Starting...")
    
    # Create and initialize the system
    kingdom = KingdomSystem()
    
    try:
        # Initialize all components
        await kingdom.initialize()
        
        # Start the system
        await kingdom.start()
        
        # Interactive mode for testing
        print("\n🧙 Vazir is ready for strategic guidance!")
        print("Commands: 'help', 'status', 'plan', 'decide', 'quit'")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n🤔 Ask Vazir: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    print("""
Available commands:
- 'help': Show this help message
- 'status': Show system status
- 'plan': Ask for strategic planning help
- 'decide': Ask for decision analysis help
- 'quit': Exit the system
- Or just type your question/message for general guidance
                    """)
                elif user_input.lower() == 'status':
                    status = kingdom.get_system_status()
                    print(f"\n📊 System Status: {json.dumps(status, indent=2)}")
                elif user_input.lower() == 'plan':
                    response = await kingdom.interact_with_vazir(
                        "Help me create a strategic plan for my life",
                        "strategic_plan"
                    )
                    print(f"\n🧙 Vazir's Response:\n{json.dumps(response, indent=2)}")
                elif user_input.lower() == 'decide':
                    response = await kingdom.interact_with_vazir(
                        "Help me analyze an important decision",
                        "decision_analysis"
                    )
                    print(f"\n🧙 Vazir's Response:\n{json.dumps(response, indent=2)}")
                elif user_input:
                    response = await kingdom.interact_with_vazir(user_input, "general_guidance")
                    if response.get("success"):
                        result = response["response"]
                        print(f"\n🧙 Vazir's Wisdom: {result.get('wisdom', 'General guidance provided')}")
                        if "reflection_questions" in result:
                            print("\n🤔 Questions for reflection:")
                            for q in result["reflection_questions"]:
                                print(f"   • {q}")
                    else:
                        print(f"\n❌ Error: {response.get('error', 'Unknown error')}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    except Exception as e:
        print(f"❌ System error: {e}")
    finally:
        # Graceful shutdown
        await kingdom.shutdown()
        print("👋 Kingdom system shutdown complete")


if __name__ == "__main__":
    # Run the Kingdom system
    asyncio.run(main())