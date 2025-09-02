import React, { useState, useEffect, useRef } from 'react'
import {
  Paper,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  Card,
  CardContent,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  CheckCircle as CompleteIcon,
  Schedule as PendingIcon
} from '@mui/icons-material'
import * as d3 from 'd3'

interface WorkflowVisualizationProps {
  workflows: any[]
  agents: any[]
}

interface WorkflowNode {
  id: string
  name: string
  type: 'agent' | 'action'
  group: number
  x?: number
  y?: number
}

interface WorkflowLink {
  source: string
  target: string
  value: number
}

const WorkflowVisualization: React.FC<WorkflowVisualizationProps> = ({ workflows, agents }) => {
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (selectedWorkflow && svgRef.current) {
      renderWorkflowDiagram(selectedWorkflow)
    }
  }, [selectedWorkflow])

  const renderWorkflowDiagram = (workflow: any) => {
    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const width = 800
    const height = 400
    const margin = { top: 20, right: 20, bottom: 20, left: 20 }

    // Create nodes and links from workflow steps
    const nodes: WorkflowNode[] = []
    const links: WorkflowLink[] = []
    const agentNodes = new Set<string>()

    // Add workflow start node
    nodes.push({
      id: 'start',
      name: 'Start',
      type: 'action',
      group: 0
    })

    // Process workflow steps
    workflow.steps?.forEach((step: any, index: number) => {
      const agentId = step.agent_id
      
      // Add agent node if not exists
      if (!agentNodes.has(agentId)) {
        nodes.push({
          id: agentId,
          name: agentId.split('_').slice(0, -1).join(' '),
          type: 'agent',
          group: 1
        })
        agentNodes.add(agentId)
      }

      // Add action node
      const actionId = `action_${index}`
      nodes.push({
        id: actionId,
        name: step.action || 'Process',
        type: 'action',
        group: 2
      })

      // Add links
      if (index === 0) {
        links.push({
          source: 'start',
          target: agentId,
          value: 1
        })
      }

      links.push({
        source: agentId,
        target: actionId,
        value: 1
      })

      // Link to next agent if exists
      if (index < workflow.steps.length - 1) {
        const nextAgent = workflow.steps[index + 1].agent_id
        if (nextAgent !== agentId) {
          links.push({
            source: actionId,
            target: nextAgent,
            value: 1
          })
        }
      }
    })

    // Add end node
    nodes.push({
      id: 'end',
      name: 'Complete',
      type: 'action',
      group: 3
    })

    // Link last action to end
    if (workflow.steps?.length > 0) {
      const lastAction = `action_${workflow.steps.length - 1}`
      links.push({
        source: lastAction,
        target: 'end',
        value: 1
      })
    }

    // Create force simulation
    const simulation = d3.forceSimulation<WorkflowNode>(nodes)
      .force('link', d3.forceLink<WorkflowNode, WorkflowLink>(links)
        .id(d => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('x', d3.forceX(width / 2).strength(0.1))
      .force('y', d3.forceY(height / 2).strength(0.1))

    // Create SVG elements
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Create arrow markers
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 15)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#666')

    // Create links
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .enter().append('line')
      .attr('stroke', '#666')
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrowhead)')

    // Create nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .enter().append('circle')
      .attr('r', d => d.type === 'agent' ? 25 : 15)
      .attr('fill', d => {
        switch (d.type) {
          case 'agent': return '#4f46e5'
          case 'action': return d.name === 'Start' ? '#10b981' : d.name === 'Complete' ? '#ef4444' : '#06b6d4'
          default: return '#666'
        }
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .call(d3.drag<SVGCircleElement, WorkflowNode>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))

    // Add labels
    const labels = g.append('g')
      .selectAll('text')
      .data(nodes)
      .enter().append('text')
      .text(d => d.name)
      .attr('text-anchor', 'middle')
      .attr('dy', '.35em')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('fill', 'white')
      .attr('pointer-events', 'none')

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as any).x)
        .attr('y1', d => (d.source as any).y)
        .attr('x2', d => (d.target as any).x)
        .attr('y2', d => (d.target as any).y)

      node
        .attr('cx', d => d.x!)
        .attr('cy', d => d.y!)

      labels
        .attr('x', d => d.x!)
        .attr('y', d => d.y!)
    })

    // Drag functions
    function dragstarted(event: any, d: WorkflowNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    }

    function dragged(event: any, d: WorkflowNode) {
      d.fx = event.x
      d.fy = event.y
    }

    function dragended(event: any, d: WorkflowNode) {
      if (!event.active) simulation.alphaTarget(0)
      d.fx = null
      d.fy = null
    }

    // Set SVG size
    svg.attr('width', width + margin.left + margin.right)
       .attr('height', height + margin.top + margin.bottom)
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  return (
    <Box className="fade-in">
      <Typography variant="h4" gutterBottom>
        Workflow Visualization
      </Typography>

      <Box sx={{ display: 'flex', gap: 3, height: 'calc(100vh - 200px)' }}>
        {/* Workflow List */}
        <Paper sx={{ width: 350, p: 2, overflow: 'auto' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Recent Workflows ({workflows.length})
            </Typography>
            <IconButton size="small">
              <RefreshIcon />
            </IconButton>
          </Box>

          <List>
            {workflows.slice(0, 20).map((workflow, index) => (
              <ListItem
                key={workflow.workflow_id}
                button
                selected={selectedWorkflow?.workflow_id === workflow.workflow_id}
                onClick={() => setSelectedWorkflow(workflow)}
                sx={{
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  mb: 1,
                  '&.Mui-selected': {
                    borderColor: 'primary.main',
                    bgcolor: 'primary.main',
                    color: 'primary.contrastText'
                  }
                }}
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" noWrap>
                        {workflow.workflow_id.split('_').pop()}
                      </Typography>
                      <Chip
                        size="small"
                        icon={workflow.completed_at ? <CompleteIcon /> : <PendingIcon />}
                        label={workflow.completed_at ? 'Complete' : 'Active'}
                        color={workflow.completed_at ? 'success' : 'warning'}
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="caption" display="block">
                        Started: {new Date(workflow.started_at).toLocaleTimeString()}
                      </Typography>
                      <Typography variant="caption" display="block">
                        Steps: {workflow.steps?.length || 0}
                      </Typography>
                      <Typography variant="caption" display="block">
                        First Agent: {workflow.first_agent}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>

        {/* Visualization Area */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {selectedWorkflow ? (
            <>
              {/* Workflow Header */}
              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Workflow: {selectedWorkflow.workflow_id}
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Chip
                    icon={<PlayIcon />}
                    label={`Started: ${new Date(selectedWorkflow.started_at).toLocaleString()}`}
                    variant="outlined"
                  />
                  {selectedWorkflow.completed_at && (
                    <Chip
                      icon={<CompleteIcon />}
                      label={`Completed: ${new Date(selectedWorkflow.completed_at).toLocaleString()}`}
                      color="success"
                      variant="outlined"
                    />
                  )}
                  <Chip
                    label={`${selectedWorkflow.steps?.length || 0} Steps`}
                    color="primary"
                    variant="outlined"
                  />
                </Box>
              </Paper>

              {/* Diagram */}
              <Paper sx={{ flex: 1, p: 2, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <svg ref={svgRef}></svg>
              </Paper>

              {/* Workflow Steps Details */}
              <Paper sx={{ p: 2, mt: 2, maxHeight: 200, overflow: 'auto' }}>
                <Typography variant="h6" gutterBottom>
                  Execution Steps
                </Typography>
                {selectedWorkflow.steps?.map((step: any, index: number) => (
                  <Box key={index} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2">
                        <strong>{index + 1}.</strong> {step.agent_id} → {step.action}
                      </Typography>
                      <Chip
                        size="small"
                        label={formatDuration(step.duration_ms)}
                        color="secondary"
                        variant="outlined"
                      />
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </Typography>
                    {index < selectedWorkflow.steps.length - 1 && <Divider sx={{ mt: 1 }} />}
                  </Box>
                ))}
              </Paper>
            </>
          ) : (
            <Paper sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="h6" color="text.secondary">
                Select a workflow to view its visualization
              </Typography>
            </Paper>
          )}
        </Box>
      </Box>
    </Box>
  )
}

export default WorkflowVisualization