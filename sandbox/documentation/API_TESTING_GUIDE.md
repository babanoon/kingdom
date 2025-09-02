# Kingdom Management System - API Testing Guide

## Quick Start

### 1. Start the Backend Server
```bash
cd /Users/ed/King/B2
python kingdom/management/management_server.py
```

Server will start on: **http://localhost:8765**

### 2. API Documentation
Visit: **http://localhost:8765/docs** for interactive Swagger documentation

## Postman Testing Examples

### 1. Health Check
**GET** `http://localhost:8765/health`

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-01T17:49:15.123Z",
  "kingdom_service_running": true
}
```

### 2. Agent Status
**GET** `http://localhost:8765/api/agents`

**Expected Response:**
```json
[
  {
    "agent_id": "general_receiver_001",
    "agent_type": "general_receiver",
    "status": "idle",
    "task_count": 0,
    "uptime_seconds": 123.45
  },
  {
    "agent_id": "math_calculator_001",
    "agent_type": "math_calculator",
    "status": "idle",
    "task_count": 0,
    "uptime_seconds": 123.45
  }
]
```

### 3. Chat Endpoint (Main Integration Point)
**POST** `http://localhost:8765/api/chat`

**Headers:**
```
Content-Type: application/json
```

**Request Body - General Question:**
```json
{
  "sender": "user123",
  "receiver": "kingdom",
  "forum": "general_chat",
  "message": "Hello, how are you today?"
}
```

**Request Body - Math Question:**
```json
{
  "sender": "student",
  "receiver": "kingdom",
  "forum": "math_help",
  "message": "Can you solve the equation: 2x + 5 = 15?"
}
```

**Expected Response:**
```json
{
  "response": "I'll help you solve that equation...",
  "workflow_id": "workflow_20250901_123456_abc123",
  "timestamp": "2025-09-01T12:34:56.789Z",
  "agent_used": "general_receiver_001"
}
```

### 4. Workflow Tracking
**GET** `http://localhost:8765/api/workflows`

**Expected Response:**
```json
{
  "active": [],
  "completed": [
    {
      "workflow_id": "workflow_20250901_123456_abc123",
      "started_at": "2025-09-01T12:34:56.789Z",
      "completed_at": "2025-09-01T12:35:01.234Z",
      "first_agent": "general_receiver_001",
      "steps": [
        {
          "agent_id": "general_receiver_001",
          "action": "process_message",
          "timestamp": "2025-09-01T12:34:56.789Z",
          "duration_ms": 1500
        }
      ],
      "final_result": {"status": "completed"}
    }
  ]
}
```

### 5. WebSocket Monitoring
**WebSocket** `ws://localhost:8765/ws/monitor`

**Connection Test (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8765/ws/monitor');

ws.onopen = function() {
    console.log('Connected to Kingdom monitoring');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Real-time update:', data);
};
```

## Testing Workflow

### Step 1: Verify Server is Running
1. **GET** `http://localhost:8765/health`
2. Should return `{"status": "healthy"}`

### Step 2: Check Agents
1. **GET** `http://localhost:8765/api/agents`
2. Should show 8 agents (2 of each type)

### Step 3: Test General Chat
1. **POST** `http://localhost:8765/api/chat`
2. Use general question payload
3. Should get response from GeneralReceiver agent

### Step 4: Test Mathematical Routing
1. **POST** `http://localhost:8765/api/chat`
2. Use math question payload
3. Should route to MathCalculator agent (check logs)

### Step 5: Monitor Workflows
1. **GET** `http://localhost:8765/api/workflows`
2. Should show completed workflows from your tests

## Rocket.Chat Integration

### Webhook Configuration
Configure Rocket.Chat to send messages to:
**URL:** `http://localhost:8765/api/chat`

**Webhook Payload Mapping:**
```json
{
  "sender": "{{user_name}}",
  "receiver": "kingdom",
  "forum": "{{channel_name}}",
  "message": "{{text}}"
}
```

## Expected Logs

When testing, you should see logs like:
```
2025-09-01 17:49:06,891 - root - INFO - Task queued: task_20250901_174906_891413 (process_chat_message)
2025-09-01 17:49:06,891 - agent.general_receiver_001 - INFO - Processing task: task_20250901_174906_891413
2025-09-01 17:49:06,891 - agent.general_receiver_001 - INFO - Task completed: task_20250901_174906_891413
```

## Troubleshooting

### Server Won't Start
```bash
# Check if port 8765 is in use
lsof -i :8765

# Kill process if needed
kill -9 <PID>
```

### No Agents Found
```bash
# Check agent service logs
tail -f kingdom/logs/agent_service.log
```

### Database Connection Issues
```bash
# Test database connection
PGPASSWORD=securepasswordkossher123 psql -h localhost -p 9876 -U kadmin -d general2613 -c "SELECT 1"
```