/**
 * WebSocket service for real-time recommendation feedback updates
 */

export interface RecommendationFeedbackUpdate {
  type: 'recommendation_feedback'
  recommendation_id: string
  user_id: string
  feedback: 'agreed' | 'rejected'
  timestamp: string
}

export class RecommendationFeedbackWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private onUpdate: (update: RecommendationFeedbackUpdate) => void

  constructor(userId: string, onUpdate: (update: RecommendationFeedbackUpdate) => void) {
    this.userId = userId
    this.onUpdate = onUpdate
  }

  private userId: string

  connect(): void {
    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${wsProtocol}//${window.location.host}/ws/user/${this.userId}/recommendations/feedback`
      console.log('Connecting to Recommendation Feedback WebSocket:', wsUrl)
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('Recommendation Feedback WebSocket connected for user:', this.userId)
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('Recommendation Feedback WebSocket message received:', message)

          if (message.type === 'recommendation_feedback') {
            this.onUpdate(message as RecommendationFeedbackUpdate)
          } else if (message.type === 'connected' || message.type === 'ack') {
            // Connection confirmation, ignore
          }
        } catch (error) {
          console.error('Error parsing Recommendation Feedback WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('Recommendation Feedback WebSocket error:', error)
      }

      this.ws.onclose = () => {
        console.log('Recommendation Feedback WebSocket disconnected')
        this.reconnect()
      }
    } catch (error) {
      console.error('Error connecting Recommendation Feedback WebSocket:', error)
      this.reconnect()
    }
  }

  private reconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Reconnecting Recommendation Feedback WebSocket (attempt ${this.reconnectAttempts})...`)
      setTimeout(() => {
        this.connect()
      }, this.reconnectDelay)
    } else {
      console.error('Max reconnection attempts reached for Recommendation Feedback WebSocket')
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

