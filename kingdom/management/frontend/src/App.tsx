import React, { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Badge,
  Alert,
  Snackbar
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Memory as AgentsIcon,
  Timeline as WorkflowsIcon,
  Chat as ChatIcon,
  Settings as SettingsIcon
} from '@mui/icons-material'

// Components
import Dashboard from './components/Dashboard'
import AgentMonitor from './components/AgentMonitor'
import WorkflowVisualization from './components/WorkflowVisualization'
import ChatTester from './components/ChatTester'
import SystemHealth from './components/SystemHealth'

// Services
import { KingdomAPI } from './services/api'
import { WebSocketService } from './services/websocket'

const drawerWidth = 240

function App() {
  const [systemHealth, setSystemHealth] = useState<any>(null)
  const [agents, setAgents] = useState<any[]>([])
  const [workflows, setWorkflows] = useState<any[]>([])
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected')
  const [notifications, setNotifications] = useState<string[]>([])
  const [currentView, setCurrentView] = useState('dashboard')

  useEffect(() => {
    // Initialize API connection
    initializeSystem()
    
    // Setup WebSocket connection
    const wsService = new WebSocketService('ws://localhost:8765/ws/monitor')
    wsService.connect()
    
    wsService.onMessage((data) => {
      handleRealtimeUpdate(data)
    })

    wsService.onConnection((status) => {
      setConnectionStatus(status)
    })

    // Cleanup
    return () => {
      wsService.disconnect()
    }
  }, [])

  const initializeSystem = async () => {
    try {
      setConnectionStatus('connecting')
      
      // Fetch initial data
      const [healthData, agentsData, workflowsData] = await Promise.all([
        KingdomAPI.getHealth(),
        KingdomAPI.getAgents(),
        KingdomAPI.getWorkflows()
      ])
      
      setSystemHealth(healthData)
      setAgents(agentsData)
      setWorkflows(workflowsData.completed || [])
      setConnectionStatus('connected')
      
    } catch (error) {
      console.error('Failed to initialize system:', error)
      setConnectionStatus('disconnected')
      addNotification('Failed to connect to Kingdom Management System')
    }
  }

  const handleRealtimeUpdate = (data: any) => {
    switch (data.type) {
      case 'agent_status_update':
        updateAgentStatus(data.data)
        break
      case 'workflow_update':
        updateWorkflowStatus(data.data)
        break
      case 'system_alert':
        addNotification(data.data.message)
        break
    }
  }

  const updateAgentStatus = (agentData: any) => {
    setAgents(prev => 
      prev.map(agent => 
        agent.agent_id === agentData.agent_id ? { ...agent, ...agentData } : agent
      )
    )
  }

  const updateWorkflowStatus = (workflowData: any) => {
    setWorkflows(prev => {
      const exists = prev.find(w => w.workflow_id === workflowData.workflow_id)
      if (exists) {
        return prev.map(w => 
          w.workflow_id === workflowData.workflow_id ? { ...w, ...workflowData } : w
        )
      } else {
        return [workflowData, ...prev.slice(0, 49)] // Keep last 50 workflows
      }
    })
  }

  const addNotification = (message: string) => {
    setNotifications(prev => [message, ...prev.slice(0, 4)])
    setTimeout(() => {
      setNotifications(prev => prev.slice(0, -1))
    }, 5000)
  }

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon />, badge: 0 },
    { id: 'agents', label: 'Agent Monitor', icon: <AgentsIcon />, badge: agents.filter(a => a.status === 'busy').length },
    { id: 'workflows', label: 'Workflows', icon: <WorkflowsIcon />, badge: workflows.filter(w => w.status === 'active').length },
    { id: 'chat', label: 'Chat Tester', icon: <ChatIcon />, badge: 0 },
  ]

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            🏰 Kingdom Management System
          </Typography>
          <SystemHealth 
            status={connectionStatus}
            systemHealth={systemHealth}
            agentCount={agents.length}
          />
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem 
                key={item.id}
                button
                selected={currentView === item.id}
                onClick={() => setCurrentView(item.id)}
              >
                <ListItemIcon>
                  <Badge badgeContent={item.badge} color="secondary">
                    {item.icon}
                  </Badge>
                </ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        
        {currentView === 'dashboard' && (
          <Dashboard 
            agents={agents}
            workflows={workflows}
            systemHealth={systemHealth}
          />
        )}
        
        {currentView === 'agents' && (
          <AgentMonitor 
            agents={agents}
            onRefresh={() => initializeSystem()}
          />
        )}
        
        {currentView === 'workflows' && (
          <WorkflowVisualization 
            workflows={workflows}
            agents={agents}
          />
        )}
        
        {currentView === 'chat' && (
          <ChatTester 
            onNewWorkflow={(workflow) => updateWorkflowStatus(workflow)}
          />
        )}
      </Box>

      {/* Notifications */}
      {notifications.map((notification, index) => (
        <Snackbar
          key={index}
          open={true}
          autoHideDuration={5000}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ mt: index * 7 }}
        >
          <Alert severity="info" sx={{ width: '100%' }}>
            {notification}
          </Alert>
        </Snackbar>
      ))}
    </Box>
  )
}

export default App