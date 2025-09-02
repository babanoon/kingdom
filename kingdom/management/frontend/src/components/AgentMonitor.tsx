import React, { useState } from 'react'
import {
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Card,
  CardContent,
  Grid,
  Avatar,
  LinearProgress,
  Tooltip,
  Badge
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  Memory as AgentIcon,
  CheckCircle as IdleIcon,
  PlayArrow as BusyIcon,
  Error as ErrorIcon,
  Schedule as ClockIcon
} from '@mui/icons-material'

interface AgentMonitorProps {
  agents: any[]
  onRefresh: () => void
}

const AgentMonitor: React.FC<AgentMonitorProps> = ({ agents, onRefresh }) => {
  const [sortBy, setSortBy] = useState<'agent_id' | 'agent_type' | 'task_count' | 'uptime_seconds'>('agent_type')

  const sortedAgents = [...agents].sort((a, b) => {
    switch (sortBy) {
      case 'agent_id':
        return a.agent_id.localeCompare(b.agent_id)
      case 'agent_type':
        return a.agent_type.localeCompare(b.agent_type)
      case 'task_count':
        return b.task_count - a.task_count
      case 'uptime_seconds':
        return b.uptime_seconds - a.uptime_seconds
      default:
        return 0
    }
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'idle':
        return <IdleIcon color="success" />
      case 'busy':
        return <BusyIcon color="warning" />
      case 'error':
        return <ErrorIcon color="error" />
      default:
        return <ClockIcon color="disabled" />
    }
  }

  const getStatusColor = (status: string): "default" | "success" | "warning" | "error" => {
    switch (status) {
      case 'idle':
        return 'success'
      case 'busy':
        return 'warning'
      case 'error':
        return 'error'
      default:
        return 'default'
    }
  }

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    } else {
      return `${secs}s`
    }
  }

  const getAgentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'general_receiver': '#4f46e5',
      'math_calculator': '#06b6d4',
      'tester1': '#10b981',
      'tester2': '#f59e0b'
    }
    return colors[type] || '#6b7280'
  }

  const agentStats = agents.reduce((acc, agent) => {
    acc[agent.agent_type] = acc[agent.agent_type] || { count: 0, idle: 0, busy: 0, error: 0, totalTasks: 0 }
    acc[agent.agent_type].count++
    acc[agent.agent_type][agent.status]++
    acc[agent.agent_type].totalTasks += agent.task_count
    return acc
  }, {} as Record<string, any>)

  return (
    <Box className="fade-in">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Agent Monitor
        </Typography>
        <IconButton onClick={onRefresh} sx={{ bgcolor: 'primary.main', color: 'white' }}>
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* Agent Type Overview Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {Object.entries(agentStats).map(([type, stats]) => (
          <Grid item xs={12} sm={6} md={3} key={type}>
            <Card sx={{ border: `2px solid ${getAgentTypeColor(type)}` }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h6" sx={{ textTransform: 'capitalize', color: getAgentTypeColor(type) }}>
                      {type.replace('_', ' ')}
                    </Typography>
                    <Typography variant="h4" sx={{ mt: 1 }}>
                      {stats.count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {stats.totalTasks} total tasks
                    </Typography>
                  </Box>
                  <Avatar sx={{ bgcolor: getAgentTypeColor(type), width: 56, height: 56 }}>
                    <AgentIcon />
                  </Avatar>
                </Box>
                
                <Box sx={{ mt: 2 }}>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Badge badgeContent={stats.idle} color="success" sx={{ '& .MuiBadge-badge': { fontSize: '0.65rem' } }}>
                      <Chip size="small" label="Idle" color="success" variant="outlined" />
                    </Badge>
                    <Badge badgeContent={stats.busy} color="warning" sx={{ '& .MuiBadge-badge': { fontSize: '0.65rem' } }}>
                      <Chip size="small" label="Busy" color="warning" variant="outlined" />
                    </Badge>
                    {stats.error > 0 && (
                      <Badge badgeContent={stats.error} color="error" sx={{ '& .MuiBadge-badge': { fontSize: '0.65rem' } }}>
                        <Chip size="small" label="Error" color="error" variant="outlined" />
                      </Badge>
                    )}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Agents Table */}
      <Paper>
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            All Agents ({agents.length})
          </Typography>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Sort by:
            </Typography>
            {(['agent_id', 'agent_type', 'task_count', 'uptime_seconds'] as const).map((field) => (
              <Chip
                key={field}
                label={field.replace('_', ' ')}
                size="small"
                variant={sortBy === field ? "filled" : "outlined"}
                onClick={() => setSortBy(field)}
                sx={{ ml: 1 }}
              />
            ))}
          </Box>
        </Box>
        
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Agent</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Tasks</TableCell>
                <TableCell align="right">Uptime</TableCell>
                <TableCell>Activity</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedAgents.map((agent) => (
                <TableRow key={agent.agent_id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ mr: 2, bgcolor: getAgentTypeColor(agent.agent_type), width: 32, height: 32 }}>
                        {agent.agent_id.slice(-1)}
                      </Avatar>
                      <Typography variant="body2" fontFamily="monospace">
                        {agent.agent_id}
                      </Typography>
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Chip
                      label={agent.agent_type.replace('_', ' ')}
                      size="small"
                      sx={{
                        bgcolor: getAgentTypeColor(agent.agent_type),
                        color: 'white',
                        textTransform: 'capitalize'
                      }}
                    />
                  </TableCell>
                  
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {getStatusIcon(agent.status)}
                      <Chip
                        label={agent.status}
                        size="small"
                        color={getStatusColor(agent.status)}
                        variant="outlined"
                        sx={{ ml: 1, textTransform: 'capitalize' }}
                      />
                    </Box>
                  </TableCell>
                  
                  <TableCell align="right">
                    <Typography variant="h6" color="primary.main">
                      {agent.task_count}
                    </Typography>
                  </TableCell>
                  
                  <TableCell align="right">
                    <Tooltip title={`${agent.uptime_seconds.toFixed(1)} seconds`}>
                      <Typography variant="body2">
                        {formatUptime(agent.uptime_seconds)}
                      </Typography>
                    </Tooltip>
                  </TableCell>
                  
                  <TableCell>
                    <Box sx={{ width: 100 }}>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min((agent.task_count / Math.max(...agents.map(a => a.task_count))) * 100, 100)}
                        color={agent.status === 'busy' ? 'warning' : 'primary'}
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        Activity level
                      </Typography>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  )
}

export default AgentMonitor