import React from 'react'
import {
  Box,
  Chip,
  IconButton,
  Tooltip,
  Badge
} from '@mui/material'
import {
  Circle as StatusIcon,
  Refresh as RefreshIcon,
  Memory as AgentIcon
} from '@mui/icons-material'
import { ConnectionStatus } from '../services/websocket'

interface SystemHealthProps {
  status: ConnectionStatus
  systemHealth: any
  agentCount: number
}

const SystemHealth: React.FC<SystemHealthProps> = ({ status, systemHealth, agentCount }) => {
  const getStatusColor = (status: ConnectionStatus) => {
    switch (status) {
      case 'connected':
        return 'success'
      case 'connecting':
        return 'warning'
      case 'disconnected':
        return 'error'
      default:
        return 'default'
    }
  }

  const getStatusText = (status: ConnectionStatus) => {
    switch (status) {
      case 'connected':
        return 'Connected'
      case 'connecting':
        return 'Connecting...'
      case 'disconnected':
        return 'Disconnected'
      default:
        return 'Unknown'
    }
  }

  const handleRefresh = () => {
    window.location.reload()
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      {/* System Status */}
      <Tooltip title={`WebSocket ${getStatusText(status)}`}>
        <Chip
          icon={<StatusIcon />}
          label={getStatusText(status)}
          color={getStatusColor(status)}
          size="small"
          variant={status === 'connected' ? 'filled' : 'outlined'}
          className={status === 'connecting' ? 'pulse' : ''}
        />
      </Tooltip>

      {/* Agent Count */}
      <Tooltip title={`${agentCount} agents running`}>
        <Badge badgeContent={agentCount} color="primary">
          <AgentIcon color="action" />
        </Badge>
      </Tooltip>

      {/* Backend Health */}
      {systemHealth && (
        <Tooltip title={`Backend: ${systemHealth.status}`}>
          <Chip
            icon={<StatusIcon />}
            label="Backend"
            color={systemHealth.status === 'healthy' ? 'success' : 'error'}
            size="small"
            variant="outlined"
          />
        </Tooltip>
      )}

      {/* Refresh Button */}
      <Tooltip title="Refresh Dashboard">
        <IconButton
          size="small"
          onClick={handleRefresh}
          sx={{ color: 'white' }}
        >
          <RefreshIcon />
        </IconButton>
      </Tooltip>
    </Box>
  )
}

export default SystemHealth