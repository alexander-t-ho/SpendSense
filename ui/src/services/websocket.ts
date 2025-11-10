/**
 * WebSocket service for real-time consent updates
 */

// Use Vite proxy for local dev (relative path), or explicit URL for production
const WS_BASE_URL = (import.meta as any).env?.VITE_WS_BASE_URL || ''

export class ConsentWebSocket {
  private ws: WebSocket | null = null
  private userId: string
  private onConsentUpdate: (consented: boolean, data: any) => void
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(userId: string, onConsentUpdate: (consented: boolean, data: any) => void) {
    this.userId = userId
    this.onConsentUpdate = onConsentUpdate
  }

  connect(): void {
    try {
      // Use relative path for Vite proxy, or full URL if VITE_WS_BASE_URL is set
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsHost = WS_BASE_URL || `${wsProtocol}//${window.location.host}`
      const wsUrl = `${wsHost}/ws/consent/${this.userId}`
      console.log('Connecting to WebSocket:', wsUrl)
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected for user:', this.userId)
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('WebSocket message received:', message)

          if (message.type === 'consent_update') {
            this.onConsentUpdate(message.consented, message.data)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.reconnect()
      }
    } catch (error) {
      console.error('Error connecting WebSocket:', error)
      this.reconnect()
    }
  }

  private reconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      console.log(`Reconnecting WebSocket in ${delay}ms (attempt ${this.reconnectAttempts})`)
      setTimeout(() => {
        this.connect()
      }, delay)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

