# Kingdom Management Frontend Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/ed/King/B2/kingdom/management/frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

The frontend will be available at: **http://localhost:3000**

### 3. Start Backend (Required)
In a separate terminal:
```bash
cd /Users/ed/King/B2
python kingdom/management/management_server.py
```

Backend runs on: **http://localhost:8765**

## Features

### 🎯 Dashboard
- **Real-time System Overview**: Agent counts, task statistics, workflow summaries
- **Interactive Charts**: Agent type distribution, task activity using Recharts
- **Status Cards**: Live metrics with color-coded indicators
- **Recent Activity**: Latest workflows and agent interactions

### 🤖 Agent Monitor
- **Live Agent Status**: Real-time monitoring of all 8 agents
- **Agent Type Cards**: Overview by agent type (GeneralReceiver, MathCalculator, etc.)
- **Detailed Table**: Sortable by ID, type, task count, uptime
- **Visual Indicators**: Status icons, activity bars, performance metrics

### 📊 Workflow Visualization
- **D3.js Interactive Diagrams**: Visual workflow representation
- **Step-by-Step Breakdown**: Detailed execution timeline
- **Agent Flow Tracking**: See how requests move between agents
- **Performance Metrics**: Duration, timestamps, success rates

### 💬 Chat Tester
- **Live API Testing**: Send test messages to backend
- **Predefined Templates**: Common test scenarios (math, general, help)
- **Real-time Responses**: See agent responses immediately
- **Postman Integration**: Copy request format for external testing

### 📡 Real-time Features
- **WebSocket Connection**: Live updates without refresh
- **Auto-refresh Data**: Agent status and workflow updates
- **Connection Status**: Visual indicator for backend connectivity
- **System Health**: Backend status monitoring

## Architecture

### Tech Stack
- **React 18** with TypeScript
- **Material-UI v5** for components
- **D3.js** for workflow visualizations
- **Recharts** for statistical charts
- **Axios** for API communication
- **Vite** for fast development

### Project Structure
```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Dashboard.tsx    # Main dashboard
│   │   ├── AgentMonitor.tsx # Agent status table
│   │   ├── WorkflowVisualization.tsx # D3.js diagrams
│   │   ├── ChatTester.tsx   # API testing interface
│   │   └── SystemHealth.tsx # Status indicators
│   ├── services/            # API and WebSocket services
│   │   ├── api.ts          # REST API client
│   │   └── websocket.ts    # WebSocket service
│   ├── App.tsx             # Main application
│   └── main.tsx            # Entry point
├── package.json            # Dependencies
└── vite.config.ts         # Build configuration
```

## Development

### Available Scripts
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### API Proxy Configuration
The frontend automatically proxies API calls to the backend:
- `/api/*` → `http://localhost:8765/api/*`
- `/ws/*` → `ws://localhost:8765/ws/*`

### Environment Setup
No additional environment variables needed. The app connects to:
- Backend: `http://localhost:8765`
- WebSocket: `ws://localhost:8765/ws/monitor`

## Usage Examples

### Testing Chat Integration
1. Start both backend and frontend
2. Go to "Chat Tester" tab
3. Try predefined messages:
   - **General**: "Hello! How are you today?"
   - **Math**: "What is 15 + 25 * 2?"
   - **Complex**: "Can you solve: 2x + 5 = 15?"

### Monitoring Workflows
1. Send messages via Chat Tester
2. Go to "Workflows" tab
3. Click on any workflow to see:
   - D3.js visualization of agent interactions
   - Step-by-step execution timeline
   - Performance metrics

### Agent Monitoring
1. Go to "Agent Monitor" tab
2. View real-time status of all 8 agents
3. Sort by different criteria
4. Monitor task counts and uptime

## Troubleshooting

### Frontend Won't Start
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### API Connection Issues
1. Verify backend is running on port 8765
2. Check browser console for CORS errors
3. Ensure no firewall blocking localhost:8765

### WebSocket Connection Problems
1. Check WebSocket connection status (top right)
2. Verify backend WebSocket endpoint is active
3. Try refreshing the page

### Build Issues
```bash
# Check TypeScript compilation
npx tsc --noEmit

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

## Production Deployment

### Build for Production
```bash
npm run build
```

### Serve Static Files
```bash
npm run preview
# Or use any static file server
```

### Environment Configuration
Update API endpoints in `src/services/api.ts` for production:
```typescript
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8765'
```

## Integration with Backend

### REST API Endpoints Used
- `GET /health` - System health check
- `GET /api/agents` - Agent status list
- `GET /api/workflows` - Workflow history
- `POST /api/chat` - Send chat messages

### WebSocket Events
- `agent_status_update` - Real-time agent status
- `workflow_update` - Live workflow progress
- `system_alert` - System notifications

The frontend automatically handles reconnection and provides visual feedback for connection status.