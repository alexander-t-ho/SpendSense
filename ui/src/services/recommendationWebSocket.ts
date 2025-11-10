/**
 * WebSocket service for real-time recommendation updates
 */

// Use window location for WebSocket to work with Vite proxy in development
// const getWebSocketUrl = () => {
//   if (window.location.protocol === 'https:') {
//     return 'wss://' + window.location.host
//   }
//   // In development, use the same host/port as the page (Vite proxy handles it)
//   // In production, this would be the actual backend URL
//   const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
//   const host = window.location.hostname === 'localhost' 
//     ? 'localhost:8001' 
//     : window.location.host
//   return `${protocol}//${host}`
// }
// const WS_BASE_URL = getWebSocketUrl()

export interface RecommendationUpdate {
  type: 'recommendation_update'
  recommendation_id: string
  action: 'approved' | 'rejected' | 'flagged'
  data: {
    id: string
    user_id: string
    approved: boolean
    rejected: boolean
    flagged: boolean
    approved_at?: string | null
    rejected_at?: string | null
  }
  timestamp: string
}

export class RecommendationWebSocket {
  private ws: WebSocket | null = null
  private onUpdate: (update: RecommendationUpdate) => void
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(onUpdate: (update: RecommendationUpdate) => void) {
    this.onUpdate = onUpdate
  }

  connect(): void {
    try {
      // Use WebSocket URL that works with Vite proxy
      // Vite will proxy /ws/* to ws://127.0.0.1:8001/ws/*
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${wsProtocol}//${window.location.host}/ws/operator/recommendations`
      console.log('Connecting to Recommendation WebSocket:', wsUrl)
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('Recommendation WebSocket connected')
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('Recommendation WebSocket message received:', message)

          if (message.type === 'recommendation_update') {
            this.onUpdate(message as RecommendationUpdate)
          } else if (message.type === 'connected' || message.type === 'ack') {
            // Connection confirmation, ignore
          }
        } catch (error) {
          console.error('Error parsing Recommendation WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('Recommendation WebSocket error:', error)
      }

      this.ws.onclose = () => {
        console.log('Recommendation WebSocket disconnected')
        this.reconnect()
      }
    } catch (error) {
      console.error('Error connecting Recommendation WebSocket:', error)
      this.reconnect()
    }
  }

  private reconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Reconnecting Recommendation WebSocket (attempt ${this.reconnectAttempts})...`)
      setTimeout(() => {
        this.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('Max reconnection attempts reached for Recommendation WebSocket')
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

