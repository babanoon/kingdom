export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting'

export class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private messageHandlers: ((data: any) => void)[] = []
  private connectionHandlers: ((status: ConnectionStatus) => void)[] = []

  constructor(url: string) {
    this.url = url
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.updateConnectionStatus('connecting')
    
    try {
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = () => {
        console.log('WebSocket connected to Kingdom Management System')
        this.reconnectAttempts = 0
        this.updateConnectionStatus('connected')
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.messageHandlers.forEach(handler => handler(data))
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        this.updateConnectionStatus('disconnected')
        this.handleReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.updateConnectionStatus('disconnected')
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.updateConnectionStatus('disconnected')
      this.handleReconnect()
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      setTimeout(() => {
        this.connect()
      }, delay)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  onMessage(handler: (data: any) => void) {
    this.messageHandlers.push(handler)
    
    // Return cleanup function
    return () => {
      const index = this.messageHandlers.indexOf(handler)
      if (index > -1) {
        this.messageHandlers.splice(index, 1)
      }
    }
  }

  onConnection(handler: (status: ConnectionStatus) => void) {
    this.connectionHandlers.push(handler)
    
    // Return cleanup function
    return () => {
      const index = this.connectionHandlers.indexOf(handler)
      if (index > -1) {
        this.connectionHandlers.splice(index, 1)
      }
    }
  }

  private updateConnectionStatus(status: ConnectionStatus) {
    this.connectionHandlers.forEach(handler => handler(status))
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected. Cannot send message:', data)
    }
  }

  getReadyState(): number | null {
    return this.ws?.readyState || null
  }
}