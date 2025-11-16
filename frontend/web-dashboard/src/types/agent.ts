// Agent Types
export enum AgentType {
  LEARNING_PROGRESS = 'learning_progress',
  QUIZ_GENERATOR = 'quiz_generator',
  CODE_ANALYZER = 'code_analyzer',
  QUALITY_ASSESSOR = 'quality_assessor',
  CONTENT_RECOMMENDER = 'content_recommender',
  ANALYTICS = 'analytics',
}

export interface AgentStatus {
  status: 'inactive' | 'active' | 'processing' | 'error' | 'maintenance'
  lastActivity: string | null
  processing: boolean
  metrics: {
    totalRequests?: number
    successRate?: number
    averageResponseTime?: number
    activeUsers?: number
    quizzesGenerated?: number
    codeSubmissions?: number
    assessmentsCompleted?: number
    recommendationsGenerated?: number
    predictionsGenerated?: number
  }
  capabilities: string[]
  configuration: Record<string, any>
}

export interface AgentMessage {
  type: string
  payload: any
  timestamp: number
  userId?: string
  agentType?: AgentType
  requestId?: string
  callback?: string
}

export interface AgentsState {
  agents: Record<AgentType, AgentStatus>
  activeAgent: AgentType | null
  isAnyAgentProcessing: boolean
  agentMessages: Record<AgentType, any[]>
  lastActivity: string | null
}