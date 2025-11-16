// WebSocket Types
export interface WebSocketMessage {
  type: 'message' | 'agent_response' | 'error' | 'status_update' | 'progress_update' | 'quiz_result' | 'code_analysis' | 'quality_assessment' | 'recommendation_update' | 'analytics_data' | 'system_notification'
  payload: any
  timestamp: number
  userId?: string
  room?: string
  agentType?: string
  requestId?: string
}

export interface WebSocketConnectionState {
  connected: boolean
  authenticated: boolean
  roomJoined?: string
  reconnectAttempts: number
  lastPing: number | null
  latency: number | null
}

export interface RealtimeEvent {
  type: string
  data: any
  timestamp: string
  userId?: string
  room?: string
}