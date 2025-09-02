import axios from 'axios'

const API_BASE_URL = 'http://localhost:8765'

export interface Agent {
  agent_id: string
  agent_type: string
  status: string
  task_count: number
  uptime_seconds: number
}

export interface Workflow {
  workflow_id: string
  started_at: string
  completed_at?: string
  first_agent: string
  status: string
  steps: WorkflowStep[]
  final_result?: any
}

export interface WorkflowStep {
  agent_id: string
  action: string
  timestamp: string
  duration_ms: number
  input_data?: any
  output_data?: any
}

export interface ChatRequest {
  sender: string
  receiver: string
  forum: string
  message: string
}

export interface ChatResponse {
  response: string
  workflow_id: string
  timestamp: string
  agent_used: string
}

export interface SystemHealth {
  status: string
  timestamp: string
  kingdom_service_running: boolean
}

export class KingdomAPI {
  private static client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  static async getHealth(): Promise<SystemHealth> {
    const response = await this.client.get('/health')
    return response.data
  }

  static async getAgents(): Promise<Agent[]> {
    const response = await this.client.get('/api/agents')
    return response.data
  }

  static async getWorkflows(): Promise<{ active: Workflow[], completed: Workflow[] }> {
    const response = await this.client.get('/api/workflows')
    return response.data
  }

  static async getWorkflow(workflowId: string): Promise<Workflow> {
    const response = await this.client.get(`/api/workflows/${workflowId}`)
    return response.data
  }

  static async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post('/api/chat', request)
    return response.data
  }

  static async getSystemStats() {
    try {
      const [health, agents, workflows] = await Promise.all([
        this.getHealth(),
        this.getAgents(),
        this.getWorkflows()
      ])

      return {
        health,
        agents,
        workflows,
        stats: {
          total_agents: agents.length,
          active_agents: agents.filter(a => a.status !== 'error').length,
          busy_agents: agents.filter(a => a.status === 'busy').length,
          total_workflows: workflows.completed.length,
          active_workflows: workflows.active.length,
          agent_types: [...new Set(agents.map(a => a.agent_type))],
          total_tasks: agents.reduce((sum, agent) => sum + agent.task_count, 0)
        }
      }
    } catch (error) {
      console.error('Failed to fetch system stats:', error)
      throw error
    }
  }
}