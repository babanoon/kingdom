# Kingdom Management System - Complete Usage Guide

## 🚀 Quick Start (2 Minutes)

### Step 1: Start the Backend
```bash
cd /Users/ed/King/B2
python kingdom/management/management_server.py
```
✅ **Expected**: Server starts on port 8765, 8 agents initialize

### Step 2: Start the Frontend
```bash
cd /Users/ed/King/B2/kingdom/management/frontend
npm install  # First time only
npm run dev
```
✅ **Expected**: Frontend opens at http://localhost:3000

### Step 3: Test the System
1. Go to **Chat Tester** tab
2. Click "Math Question - Basic" 
3. Click **Send Message**
4. ✅ **Expected**: Get response from MathCalculator agent

## 📋 Complete System Overview

### What You Have
- ✅ **Backend API**: FastAPI server on port 8765
- ✅ **4 Agent Types**: GeneralReceiver, MathCalculator, Tester1, Tester2 (8 total agents)
- ✅ **React Frontend**: Full dashboard with real-time monitoring
- ✅ **D3.js Visualizations**: Interactive workflow diagrams
- ✅ **WebSocket Monitoring**: Live updates without refresh
- ✅ **External Integration Ready**: Rocket.Chat webhook support

## 🎯 Main Use Cases

### 1. External Platform Integration (Rocket.Chat)
**Setup Rocket.Chat webhook:**
- URL: `http://your-server:8765/api/chat`
- Format messages as JSON with sender, receiver, forum, message

**What happens:**
1. Message comes into `/api/chat` endpoint
2. GeneralReceiver processes it
3. Routes to MathCalculator if it's a math question
4. Response sent back to Rocket.Chat

### 2. Development & Testing
**Backend Testing (Postman):**
- Use examples in `API_TESTING_GUIDE.md`
- Test chat endpoint with different message types
- Monitor workflows and agent status

**Frontend Monitoring:**
- Real-time dashboard at http://localhost:3000
- See agent activity, workflow visualizations
- Test messages directly in Chat Tester

### 3. System Monitoring
**Dashboard Features:**
- Agent status: See which agents are busy/idle
- Task counts: Monitor workload distribution
- Workflow tracking: Visualize message routing
- Performance metrics: Response times, success rates

## 📁 File Structure & Documentation

```
kingdom/management/
├── management_server.py           # ✅ Main FastAPI server
├── test_management_system.py      # ✅ Complete test suite
├── requirements.txt               # ✅ Backend dependencies
├── API_TESTING_GUIDE.md          # ✅ Postman examples
├── FRONTEND_SETUP.md             # ✅ Frontend setup guide
├── COMPLETE_USAGE_GUIDE.md       # ✅ This file
└── frontend/                     # ✅ Complete React app
    ├── src/
    │   ├── components/           # Dashboard, AgentMonitor, etc.
    │   ├── services/             # API client, WebSocket
    │   └── App.tsx              # Main application
    └── package.json             # Frontend dependencies
```

## 🔧 Testing Your System

### Test 1: Backend Health Check
```bash
curl http://localhost:8765/health
```
**Expected Result:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-01T...",
  "kingdom_service_running": true
}
```

### Test 2: Agent Status
```bash
curl http://localhost:8765/api/agents
```
**Expected Result:** List of 8 agents with status "idle"

### Test 3: Chat Integration
**Postman POST** to `http://localhost:8765/api/chat`:
```json
{
  "sender": "test_user",
  "receiver": "kingdom", 
  "forum": "math_help",
  "message": "What is 15 + 25 * 2?"
}
```
**Expected Result:** Response from MathCalculator agent with solution

### Test 4: Frontend Dashboard
1. Open http://localhost:3000
2. Should see:
   - 8 agents in dashboard
   - Real-time connection status (green)
   - Working Chat Tester

### Test 5: Workflow Visualization
1. Send messages via Chat Tester
2. Go to Workflows tab
3. Click on workflow
4. Should see D3.js diagram showing agent interactions

## 🛠️ Customization & Extension

### Adding New Agents
1. Create agent folder: `kingdom/agents/your_agent/`
2. Add files: `agent.py`, `config.json`, `README.md`
3. Update `service_config.json` to include new agent type
4. Restart backend

### Modifying Frontend
- Components in `frontend/src/components/`
- API client in `frontend/src/services/api.ts`
- Add new views by updating `App.tsx`

### External Integration
- Backend provides REST API and WebSocket endpoints
- Use `/api/chat` for message processing
- Monitor via `/api/workflows` and `/ws/monitor`

## 📊 Performance & Scaling

### Current Capacity
- **8 concurrent agents** (2 of each type)
- **PostgreSQL database** for persistence
- **Async processing** with task queues
- **WebSocket** for real-time updates

### Scaling Options
- Increase `agents_per_type` in service_config.json
- Add more agent types
- Horizontal scaling with load balancers
- Database connection pooling already configured

## ⚠️ Troubleshooting

### Backend Issues
```bash
# Check if port 8765 is in use
lsof -i :8765

# Test database connection
PGPASSWORD=securepasswordkossher123 psql -h localhost -p 9876 -U kadmin -d general2613 -c "SELECT 1"

# Check logs
tail -f kingdom/logs/agent_service.log
```

### Frontend Issues
```bash
# Clear cache and reinstall
cd kingdom/management/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Agent Issues
```bash
# Run comprehensive test
python kingdom/management/test_management_system.py

# Check individual agent creation
python -c "from kingdom.agents.general_receiver.agent import GeneralReceiverAgent; agent = GeneralReceiverAgent('test', 'general_receiver'); print('✅ Agent created successfully')"
```

## 🔗 Integration Examples

### Rocket.Chat Webhook
```javascript
// Configure in Rocket.Chat admin
const webhookUrl = 'http://localhost:8765/api/chat'
const payload = {
  sender: user.username,
  receiver: 'kingdom',
  forum: channel.name,
  message: message.text
}
```

### External API Usage
```python
import requests

response = requests.post('http://localhost:8765/api/chat', json={
    'sender': 'python_client',
    'receiver': 'kingdom',
    'forum': 'api_test',
    'message': 'Calculate the square root of 144'
})

print(f"Response: {response.json()['response']}")
print(f"Workflow ID: {response.json()['workflow_id']}")
```

### Monitoring Integration
```javascript
// WebSocket monitoring
const ws = new WebSocket('ws://localhost:8765/ws/monitor')

ws.onmessage = function(event) {
    const data = JSON.parse(event.data)
    if (data.type === 'workflow_update') {
        console.log('New workflow:', data.data)
    }
}
```

## 📈 What's Working Now

### ✅ Fully Operational
- **Backend API**: All endpoints working
- **Agent System**: 8 agents processing tasks
- **Database Integration**: PostgreSQL connection active
- **WebSocket Monitoring**: Real-time updates
- **Frontend Dashboard**: Complete React application
- **Workflow Tracking**: Full audit trail
- **External Integration**: Ready for Rocket.Chat

### ✅ Test Results (Latest)
- **Management startup**: ✅ PASSED (8/8 agents)
- **API endpoints**: ✅ PASSED
- **Workflow tracking**: ✅ PASSED  
- **A2A communication**: ✅ OPERATIONAL

## 🎉 Success! Your Kingdom Management System is Complete

You now have a fully functional agent management system with:
- 🔥 **Real-time monitoring dashboard**
- 🤖 **AI-powered agent routing** (GeneralReceiver ↔ MathCalculator)
- 📊 **D3.js workflow visualizations**
- 🚀 **Production-ready APIs** for external integration
- 📡 **WebSocket live updates**
- 🧪 **Comprehensive testing suite**

**Next Steps:**
1. Deploy to production server
2. Configure Rocket.Chat integration
3. Add more specialized agents as needed
4. Scale horizontally with additional agent instances

All documentation is in place, system is tested and operational! 🏰✨