import React from 'react'
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  Avatar
} from '@mui/material'
import {
  Memory as AgentIcon,
  Timeline as WorkflowIcon,
  Speed as PerformanceIcon,
  CheckCircle as SuccessIcon
} from '@mui/icons-material'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface DashboardProps {
  agents: any[]
  workflows: any[]
  systemHealth: any
}

const COLORS = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']

const Dashboard: React.FC<DashboardProps> = ({ agents, workflows, systemHealth }) => {
  const agentStats = agents.reduce((acc, agent) => {
    acc[agent.agent_type] = (acc[agent.agent_type] || 0) + 1
    return acc
  }, {})

  const agentStatusStats = agents.reduce((acc, agent) => {
    acc[agent.status] = (acc[agent.status] || 0) + 1
    return acc
  }, {})

  const agentTypeData = Object.entries(agentStats).map(([type, count]) => ({
    name: type,
    value: count as number
  }))

  const agentStatusData = Object.entries(agentStatusStats).map(([status, count]) => ({
    name: status,
    value: count as number
  }))

  const taskActivity = agents.map(agent => ({
    name: agent.agent_id,
    tasks: agent.task_count
  })).sort((a, b) => b.tasks - a.tasks).slice(0, 8)

  const totalTasks = agents.reduce((sum, agent) => sum + agent.task_count, 0)
  const averageUptime = agents.length > 0 ? 
    agents.reduce((sum, agent) => sum + agent.uptime_seconds, 0) / agents.length : 0

  const recentWorkflows = workflows
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())
    .slice(0, 5)

  return (
    <Box className="fade-in">
      {/* Header Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="white" gutterBottom variant="body2">
                    Total Agents
                  </Typography>
                  <Typography variant="h4" color="white">
                    {agents.length}
                  </Typography>
                </Box>
                <AgentIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
              </Box>
              <Typography variant="body2" color="rgba(255,255,255,0.8)" sx={{ mt: 1 }}>
                {agents.filter(a => a.status === 'idle').length} idle, {agents.filter(a => a.status === 'busy').length} busy
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="white" gutterBottom variant="body2">
                    Total Tasks
                  </Typography>
                  <Typography variant="h4" color="white">
                    {totalTasks}
                  </Typography>
                </Box>
                <PerformanceIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="white" gutterBottom variant="body2">
                    Workflows
                  </Typography>
                  <Typography variant="h4" color="white">
                    {workflows.length}
                  </Typography>
                </Box>
                <WorkflowIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="white" gutterBottom variant="body2">
                    Avg Uptime
                  </Typography>
                  <Typography variant="h4" color="white">
                    {Math.floor(averageUptime / 60)}m
                  </Typography>
                </Box>
                <SuccessIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 350 }}>
            <Typography variant="h6" gutterBottom>
              Agent Types Distribution
            </Typography>
            <ResponsiveContainer width="100%" height="85%">
              <PieChart>
                <Pie
                  data={agentTypeData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {agentTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 350 }}>
            <Typography variant="h6" gutterBottom>
              Task Activity by Agent
            </Typography>
            <ResponsiveContainer width="100%" height="85%">
              <BarChart data={taskActivity}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="tasks" fill="#4f46e5" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Details Row */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Workflows
            </Typography>
            <List>
              {recentWorkflows.map((workflow, index) => (
                <ListItem key={workflow.workflow_id} divider={index < recentWorkflows.length - 1}>
                  <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                    {workflow.steps?.length || 0}
                  </Avatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1">
                          Workflow {workflow.workflow_id.split('_').pop()}
                        </Typography>
                        <Chip 
                          size="small" 
                          label={workflow.status || 'completed'} 
                          color={workflow.status === 'completed' ? 'success' : 'primary'}
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Started by: {workflow.first_agent}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(workflow.started_at).toLocaleString()}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Agent Status Overview
            </Typography>
            <Box sx={{ mt: 2 }}>
              {Object.entries(agentStatusStats).map(([status, count]) => (
                <Box key={status} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                      {status}
                    </Typography>
                    <Typography variant="body2">
                      {count} agents
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(count as number) / agents.length * 100}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 4,
                        bgcolor: status === 'idle' ? 'success.main' : 
                                status === 'busy' ? 'warning.main' : 'error.main'
                      }
                    }}
                  />
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard