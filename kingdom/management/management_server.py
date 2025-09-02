#!/usr/bin/env python3
"""
Kingdom Management Server

FastAPI-based management server that provides:
- REST API endpoints for external integrations (Rocket.Chat, etc.)
- WebSocket connections for real-time monitoring
- Integration with Kingdom agent service
- Workflow tracking and visualization support
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import uvicorn

# Add project root to path for Kingdom imports
import sys
sys.path.append('/Users/ed/King/B2')

from kingdom.service.agent_service import KingdomAgentService, TaskMessage
from kingdom.management.backend_logging import get_backend_logger, log_api_request, log_api_response, log_agent_operation, log_backend_error, log_system_event

# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    sender: str
    receiver: str
    forum: str
    message: str
    
class ChatResponse(BaseModel):
    response: str
    workflow_id: str
    timestamp: str
    agent_used: str

class AgentInfo(BaseModel):
    agent_id: str
    agent_type: str
    status: str
    task_count: int
    uptime_seconds: float

class WorkflowStep(BaseModel):
    step_id: str
    agent_id: str
    action: str
    timestamp: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    duration_ms: int

class WorkflowInfo(BaseModel):
    workflow_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    total_duration_ms: Optional[int]
    steps: List[WorkflowStep]
    first_agent: str
    agents_involved: List[str]

@dataclass
class ActiveWorkflow:
    workflow_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    steps: List[Dict[str, Any]]
    first_agent: str
    agents_involved: List[str]
    
    def to_dict(self):
        return {
            'workflow_id': self.workflow_id,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_duration_ms': int((self.completed_at - self.started_at).total_seconds() * 1000) if self.completed_at else None,
            'steps': self.steps,
            'first_agent': self.first_agent,
            'agents_involved': self.agents_involved
        }

class WorkflowTracker:
    """Tracks agent workflows for visualization and monitoring"""
    
    def __init__(self):
        self.active_workflows: Dict[str, ActiveWorkflow] = {}
        self.completed_workflows: Dict[str, ActiveWorkflow] = {}
        self.workflow_subscribers: List[WebSocket] = []
    
    def start_workflow(self, first_agent: str, initial_task: Dict[str, Any]) -> str:
        """Start tracking a new workflow"""
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        workflow = ActiveWorkflow(
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.now(),
            completed_at=None,
            steps=[],
            first_agent=first_agent,
            agents_involved=[first_agent]
        )
        
        # Add initial step
        self.add_workflow_step(
            workflow_id=workflow_id,
            agent_id=first_agent,
            action="workflow_start",
            input_data=initial_task,
            output_data={"status": "started"}
        )
        
        self.active_workflows[workflow_id] = workflow
        
        # Notify WebSocket subscribers
        asyncio.create_task(self._notify_workflow_update(workflow))
        
        return workflow_id
    
    def add_workflow_step(self, workflow_id: str, agent_id: str, action: str, 
                         input_data: Dict[str, Any], output_data: Dict[str, Any],
                         duration_ms: int = 0):
        """Add a step to an existing workflow"""
        if workflow_id not in self.active_workflows:
            logging.warning(f"Workflow {workflow_id} not found for step addition")
            return
        
        workflow = self.active_workflows[workflow_id]
        
        step = {
            'step_id': f"step_{len(workflow.steps) + 1}",
            'agent_id': agent_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'input_data': input_data,
            'output_data': output_data,
            'duration_ms': duration_ms
        }
        
        workflow.steps.append(step)
        
        if agent_id not in workflow.agents_involved:
            workflow.agents_involved.append(agent_id)
        
        # Notify WebSocket subscribers
        asyncio.create_task(self._notify_workflow_update(workflow))
    
    def complete_workflow(self, workflow_id: str, final_result: Dict[str, Any]):
        """Mark workflow as completed"""
        if workflow_id not in self.active_workflows:
            return
        
        workflow = self.active_workflows[workflow_id]
        workflow.status = "completed"
        workflow.completed_at = datetime.now()
        
        # Add completion step
        self.add_workflow_step(
            workflow_id=workflow_id,
            agent_id=workflow.first_agent,
            action="workflow_complete",
            input_data={},
            output_data=final_result
        )
        
        # Move to completed workflows
        self.completed_workflows[workflow_id] = workflow
        del self.active_workflows[workflow_id]
        
        # Notify WebSocket subscribers
        asyncio.create_task(self._notify_workflow_update(workflow))
    
    async def _notify_workflow_update(self, workflow: ActiveWorkflow):
        """Notify WebSocket subscribers of workflow updates"""
        if not self.workflow_subscribers:
            return
        
        message = {
            'type': 'workflow_update',
            'data': workflow.to_dict()
        }
        
        disconnected_clients = []
        for websocket in self.workflow_subscribers:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected_clients.append(websocket)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.workflow_subscribers.remove(client)
    
    def subscribe_to_workflows(self, websocket: WebSocket):
        """Subscribe to workflow updates"""
        self.workflow_subscribers.append(websocket)
    
    def get_workflow(self, workflow_id: str) -> Optional[ActiveWorkflow]:
        """Get workflow by ID"""
        return self.active_workflows.get(workflow_id) or self.completed_workflows.get(workflow_id)
    
    def get_all_workflows(self) -> Dict[str, Any]:
        """Get all workflows (active and completed)"""
        return {
            'active': [w.to_dict() for w in self.active_workflows.values()],
            'completed': [w.to_dict() for w in self.completed_workflows.values()]
        }

class KingdomManagementServer:
    """Main management server for Kingdom system"""
    
    def __init__(self):
        self.kingdom_service: Optional[KingdomAgentService] = None
        self.workflow_tracker = WorkflowTracker()
        self.active_connections: List[WebSocket] = []

        # Setup backend logging
        self.environment = os.getenv("KINGDOM_ENV", "local")
        self.backend_logger = get_backend_logger(self.environment)

        # Log server initialization
        log_system_event("server_startup", "Kingdom Management Server initialized", {
            "environment": self.environment,
            "timestamp": datetime.now().isoformat()
        })
        
    async def start_kingdom_service(self):
        """Start the underlying Kingdom agent service"""
        try:
            if not self.kingdom_service:
                log_system_event("service_startup", "Initializing Kingdom Agent Service")
                self.kingdom_service = KingdomAgentService()
                await self.kingdom_service.start_service()
                log_system_event("service_startup", "Kingdom Agent Service started successfully", {
                    "service_status": "running"
                })
                logging.info("Kingdom Agent Service started successfully")
        except Exception as e:
            log_backend_error("start_kingdom_service", e, {"operation": "service_startup"})
            logging.error(f"Failed to start Kingdom service: {e}")
            raise
    
    async def stop_kingdom_service(self):
        """Stop the underlying Kingdom agent service"""
        try:
            if self.kingdom_service:
                log_system_event("service_shutdown", "Stopping Kingdom Agent Service")
                await self.kingdom_service.stop_service()
                self.kingdom_service = None
                log_system_event("service_shutdown", "Kingdom Agent Service stopped successfully", {
                    "service_status": "stopped"
                })
                logging.info("Kingdom Agent Service stopped")
        except Exception as e:
            log_backend_error("stop_kingdom_service", e, {"operation": "service_shutdown"})
            logging.error(f"Error stopping Kingdom service: {e}")
    
    async def process_chat_message(self, request: ChatRequest, client_ip: str = "unknown",
                                   user_agent: str = "unknown") -> ChatResponse:
        """Process a chat message through the Kingdom system"""
        start_time = datetime.now()

        # Log API request
        self.backend_logger.log_request(
            endpoint="/api/chat",
            method="POST",
            client_ip=client_ip,
            user_agent=user_agent,
            metadata={
                "sender": request.sender,
                "receiver": request.receiver,
                "forum": request.forum,
                "message_length": len(request.message),
                "request_timestamp": start_time.isoformat()
            }
        )

        if not self.kingdom_service:
            # Log service unavailable error
            log_backend_error(
                "process_chat_message",
                Exception("Kingdom service not available"),
                {"error_type": "service_unavailable"}
            )
            raise HTTPException(status_code=503, detail="Kingdom service not available")

        # Start workflow tracking
        workflow_id = self.workflow_tracker.start_workflow(
            first_agent="general_receiver",
            initial_task={
                "sender": request.sender,
                "receiver": request.receiver,
                "forum": request.forum,
                "message": request.message
            }
        )

        # Log workflow creation
        self.backend_logger.log(
            "workflow_created",
            f"Workflow {workflow_id} created for chat message",
            {
                "workflow_id": workflow_id,
                "sender": request.sender,
                "forum": request.forum,
                "message_preview": request.message[:100]
            },
            "INFO",
            "system"
        )
        
        try:
            # Submit task to Kingdom service - let the service assign an available agent
            task_submission_start = datetime.now()
            task_id = await self.kingdom_service.submit_task(
                task_type="process_chat_message",
                payload={
                    "sender": request.sender,
                    "receiver": request.receiver,
                    "forum": request.forum,
                    "message": request.message,
                    "workflow_id": workflow_id
                }
                # No specific agent_id - let Kingdom service route to available general_receiver agent
            )
            task_submission_time = (datetime.now() - task_submission_start).total_seconds() * 1000

            # Log task submission
            log_agent_operation(
                "kingdom_service",
                "task_submitted",
                task_id,
                {
                    "task_type": "process_chat_message",
                    "workflow_id": workflow_id,
                    "submission_time_ms": task_submission_time
                },
                self.environment
            )

            # Add workflow step
            self.workflow_tracker.add_workflow_step(
                workflow_id=workflow_id,
                agent_id="general_receiver_001",
                action="task_submitted",
                input_data={"task_id": task_id},
                output_data={"status": "processing"}
            )

            # Wait for actual task completion with real results
            task_completion_start = datetime.now()
            task_result = await self.kingdom_service.wait_for_task_completion(task_id, timeout=30.0)
            task_completion_time = (datetime.now() - task_completion_start).total_seconds() * 1000

            # Extract response from task result
            if isinstance(task_result, dict):
                response_text = task_result.get('response', task_result.get('answer', 'No response generated'))
                agent_used = task_result.get('agent_id', 'general_receiver_001')
            else:
                response_text = str(task_result) if task_result else 'Task completed without response'
                agent_used = 'general_receiver_001'

            # Log agent response
            log_agent_operation(
                agent_used,
                "task_completed",
                task_id,
                {
                    "workflow_id": workflow_id,
                    "response_length": len(response_text),
                    "completion_time_ms": task_completion_time
                },
                self.environment
            )

            # Complete workflow with actual result
            self.workflow_tracker.complete_workflow(
                workflow_id=workflow_id,
                final_result={"response": response_text, "agent_used": agent_used}
            )

            # Calculate total processing time
            total_processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Log API response
            self.backend_logger.log_response(
                endpoint="/api/chat",
                method="POST",
                status_code=200,
                response_time_ms=total_processing_time,
                metadata={
                    "workflow_id": workflow_id,
                    "agent_used": agent_used,
                    "response_length": len(response_text),
                    "sender": request.sender
                }
            )

            return ChatResponse(
                response=response_text,
                workflow_id=workflow_id,
                timestamp=datetime.now().isoformat(),
                agent_used=agent_used
            )
            
        except Exception as e:
            # Log error with full context
            log_backend_error(
                "process_chat_message",
                e,
                {
                    "workflow_id": workflow_id if 'workflow_id' in locals() else None,
                    "sender": request.sender,
                    "forum": request.forum,
                    "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                }
            )

            # Log API error response
            total_error_time = (datetime.now() - start_time).total_seconds() * 1000
            self.backend_logger.log_response(
                endpoint="/api/chat",
                method="POST",
                status_code=500,
                response_time_ms=total_error_time,
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "sender": request.sender
                }
            )

            logging.error(f"Error processing chat message: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_agents_status(self) -> List[AgentInfo]:
        """Get status of all agents"""
        if not self.kingdom_service:
            return []
        
        try:
            status = await self.kingdom_service.get_service_status()
            agents = []
            
            for agent_id, agent_status in status['agents'].items():
                agents.append(AgentInfo(
                    agent_id=agent_id,
                    agent_type=agent_status['type'],
                    status=agent_status['status'],
                    task_count=agent_status['task_count'],
                    uptime_seconds=agent_status['uptime_seconds']
                ))
            
            return agents
            
        except Exception as e:
            logging.error(f"Error getting agents status: {e}")
            return []

# Global management server instance
management_server = KingdomManagementServer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    await management_server.start_kingdom_service()
    yield
    # Shutdown
    await management_server.stop_kingdom_service()

# Create FastAPI app
app = FastAPI(
    title="Kingdom Management System",
    description="Management API for Kingdom Agent System",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, req: Request):
    """Main chat endpoint for external integrations"""
    # Extract client information for logging
    client_ip = req.client.host if req.client else "unknown"
    user_agent = req.headers.get("user-agent", "unknown")

    return await management_server.process_chat_message(request, client_ip, user_agent)

@app.get("/api/agents", response_model=List[AgentInfo])
async def get_agents(req: Request):
    """Get list of all agents and their status"""
    start_time = datetime.now()
    client_ip = req.client.host if req.client else "unknown"

    # Log API request
    log_api_request(
        endpoint="/api/agents",
        method="GET",
        client_ip=client_ip,
        user_agent=req.headers.get("user-agent", "unknown"),
        environment=management_server.environment
    )

    try:
        agents = await management_server.get_agents_status()

        # Log API response
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_response(
            endpoint="/api/agents",
            method="GET",
            status_code=200,
            response_time_ms=response_time,
            metadata={"agents_count": len(agents)},
            environment=management_server.environment
        )

        return agents

    except Exception as e:
        # Log error
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_backend_error("get_agents_endpoint", e)
        log_api_response(
            endpoint="/api/agents",
            method="GET",
            status_code=500,
            response_time_ms=response_time,
            metadata={"error": str(e)},
            environment=management_server.environment
        )
        raise

@app.get("/api/workflows")
async def get_workflows():
    """Get all workflows (active and completed)"""
    return management_server.workflow_tracker.get_all_workflows()

@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get specific workflow details"""
    workflow = management_server.workflow_tracker.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.to_dict()

@app.get("/")
async def dashboard():
    """Serve the main dashboard (placeholder for now)"""
    return HTMLResponse("""
    <html>
        <head>
            <title>Kingdom Management Dashboard</title>
        </head>
        <body>
            <h1>Kingdom Management Dashboard</h1>
            <p>Dashboard will be implemented here.</p>
            <p>API endpoints available:</p>
            <ul>
                <li><strong>POST /api/chat</strong> - Chat endpoint</li>
                <li><strong>GET /api/agents</strong> - Get agents status</li>
                <li><strong>GET /api/workflows</strong> - Get workflows</li>
                <li><strong>WebSocket /ws/monitor</strong> - Real-time monitoring</li>
            </ul>
        </body>
    </html>
    """)

@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring"""
    await websocket.accept()
    management_server.workflow_tracker.subscribe_to_workflows(websocket)
    management_server.active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        management_server.active_connections.remove(websocket)
        if websocket in management_server.workflow_tracker.workflow_subscribers:
            management_server.workflow_tracker.workflow_subscribers.remove(websocket)

@app.get("/health")
async def health_check(req: Request):
    """Health check endpoint"""
    start_time = datetime.now()
    client_ip = req.client.host if req.client else "unknown"

    # Log health check request
    log_api_request(
        endpoint="/health",
        method="GET",
        client_ip=client_ip,
        user_agent=req.headers.get("user-agent", "unknown"),
        environment=management_server.environment
    )

    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "kingdom_service_running": management_server.kingdom_service is not None,
            "active_workflows": len(management_server.workflow_tracker.active_workflows),
            "completed_workflows": len(management_server.workflow_tracker.completed_workflows)
        }

        # Log health check response
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_response(
            endpoint="/health",
            method="GET",
            status_code=200,
            response_time_ms=response_time,
            metadata={
                "kingdom_service_running": health_data["kingdom_service_running"],
                "active_workflows": health_data["active_workflows"]
            },
            environment=management_server.environment
        )

        return health_data

    except Exception as e:
        # Log error
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_backend_error("health_check_endpoint", e)
        log_api_response(
            endpoint="/health",
            method="GET",
            status_code=500,
            response_time_ms=response_time,
            metadata={"error": str(e)},
            environment=management_server.environment
        )
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def run_management_server():
    """Run the Kingdom Management Server"""
    logging.basicConfig(level=logging.INFO)
    # Allow overriding via env var; default to a non-standard, likely-free port
    port = int(os.getenv("KINGDOM_MGMT_PORT", "8876"))
    logging.info(f"Starting Kingdom Management Server on port {port}")

    uvicorn.run(
        "management_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True
    )

if __name__ == "__main__":
    run_management_server()