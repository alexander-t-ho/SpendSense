/**
 * WebSocket service for real-time subscription cancellation updates
 */

export interface SubscriptionCancellationUpdate {
  type: 'subscription_cancellation'
  user_id: string
  merchant_name: string
  cancelled: boolean
  timestamp: string
}

export class SubscriptionWebSocket {
  private ws: WebSocket | null = null
  private userId: string
  private onCancellationUpdate: (update: SubscriptionCancellationUpdate) => void
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(userId: string, onCancellationUpdate: (update: SubscriptionCancellationUpdate) => void) {
    this.userId = userId
    this.onCancellationUpdate = onCancellationUpdate
  }

  connect(): void {
    try {
      // Use WebSocket URL that works with Vite proxy
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${wsProtocol}//${window.location.host}/ws/subscriptions/${this.userId}`
      console.log('Connecting to Subscription WebSocket:', wsUrl)
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('Subscription WebSocket connected for user:', this.userId)
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const message: SubscriptionCancellationUpdate = JSON.parse(event.data)
          console.log('Subscription WebSocket message received:', message)

          if (message.type === 'subscription_cancellation') {
            this.onCancellationUpdate(message)
          }
        } catch (error) {
          console.error('Error parsing Subscription WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('Subscription WebSocket error:', error)
      }

      this.ws.onclose = () => {
        console.log('Subscription WebSocket disconnected')
        this.reconnect()
      }
    } catch (error) {
      console.error('Error connecting Subscription WebSocket:', error)
      this.reconnect()
    }
  }

  private reconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      console.log(`Reconnecting Subscription WebSocket in ${delay}ms (attempt ${this.reconnectAttempts})`)
      setTimeout(() => {
        this.connect()
      }, delay)
    } else {
      console.error('Max reconnection attempts for Subscription WebSocket reached')
    }
  }

  disconnect(): void {
    if (this.ws) {
      console.log('Disconnecting Subscription WebSocket')
      this.ws.close()
      this.ws = null
    }
  }
}

