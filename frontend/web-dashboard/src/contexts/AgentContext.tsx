'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useWebSocket } from './WebSocketContext'
import { AgentType, AgentStatus as AgentStatusType, AgentMessage } from '@/types/agent'

interface AgentContextType {
  agents: Map<AgentType, AgentStatusType>
  learningProgressAgent: any
  quizGeneratorAgent: any
  codeAnalyzerAgent: any
  qualityAssessorAgent: any
  contentRecommenderAgent: any
  analyticsAgent: any
  isAnyAgentProcessing: boolean
  getAgentStatus: (agentType: AgentType) => AgentStatusType
  updateAgentStatus: (agentType: AgentType, status: Partial<AgentStatusType>) => void
  sendAgentMessage: (agentType: AgentType, message: any) => Promise<any>
  getAgentMetrics: (agentType: AgentType) => any
  resetAllAgents: () => void
}

const AgentContext = createContext<AgentContextType | undefined>(undefined)

export function AgentProvider({ children }: { children: ReactNode }) {
  const [agents, setAgents] = useState<Map<AgentType, AgentStatusType>>(new Map())
  const [isAnyAgentProcessing, setIsAnyAgentProcessing] = useState(false)
  const { isConnected, subscribeToAgent, unsubscribeFromAgent } = useWebSocket()

  // Initialize agents
  useEffect(() => {
    const initialAgents: Record<AgentType, AgentStatusType> = {
      learning_progress: {
        status: 'inactive',
        lastActivity: null,
        processing: false,
        metrics: {
          totalRequests: 0,
          successRate: 0,
          averageResponseTime: 0,
          activeUsers: 0,
        },
        capabilities: [
          'progress_tracking',
          'streak_monitoring',
          'engagement_analysis',
          'milestone_detection',
        ],
        configuration: {
          updateInterval: 5000,
          enableNotifications: true,
          trackDetailedMetrics: true,
        },
      },
      quiz_generator: {
        status: 'inactive',
        lastActivity: null,
        processing: false,
        metrics: {
          totalRequests: 0,
          successRate: 0,
          averageResponseTime: 0,
          quizzesGenerated: 0,
        },
        capabilities: [
          'adaptive_quiz_generation',
          'difficulty_adjustment',
          'byllm_integration',
          'jaseci_specific_questions',
        ],
        configuration: {
          maxQuestions: 20,
          enableRealTimeGeneration: true,
          difficultyRange: [1, 10],
        },
      },
      code_analyzer: {
        status: 'inactive',
        lastActivity: null,
        processing: false,
        metrics: {
          totalRequests: 0,
          successRate: 0,
          averageResponseTime: 0,
          codeSubmissions: 0,
        },
        capabilities: [
          'ast_parsing',
          'code_context_graph',
          'complexity_analysis',
          'multi_language_support',
        ],
        configuration: {
          supportedLanguages: ['python', 'javascript', 'jac'],
          enableCCGeneration: true,
          maxCodeSize: 100000,
        },
      },
      quality_assessor: {
        status: 'inactive',
        lastActivity: null,
        processing: false,
        metrics: {
          totalRequests: 0,
          successRate: 0,
          averageResponseTime: 0,
          assessmentsCompleted: 0,
        },
        capabilities: [
          'correctness_assessment',
          'performance_evaluation',
          'security_analysis',
          'code_quality_review',
          'documentation_check',
        ],
        configuration: {
          assessmentDimensions: 5,
          enableDetailedReports: true,
          autoRemediation: false,
        },
      },
      content_recommender: {
        status: 'inactive',
        lastActivity: null,
        processing: false,
        metrics: {
          totalRequests: 0,
          successRate: 0,
          averageResponseTime: 0,
          recommendationsGenerated: 0,
        },
        capabilities: [
          'collaborative_filtering',
          'content_based_recommendations',
          'learning_path_generation',
          'personalization',
        ],
        configuration: {
          recommendationCount: 5,
          enablePathGeneration: true,
          learningStyleAdaptation: true,
        },
      },
      analytics: {
        status: 'inactive',
        lastActivity: null,
        processing: false,
        metrics: {
          totalRequests: 0,
          successRate: 0,
          averageResponseTime: 0,
          predictionsGenerated: 0,
        },
        capabilities: [
          'predictive_analytics',
          'trend_analysis',
          'system_monitoring',
          'performance_insights',
        ],
        configuration: {
          predictionModels: ['success_prediction', 'difficulty_prediction'],
          realTimeAnalytics: true,
          reportingInterval: 3600,
        },
      },
    }

    setAgents(new Map(Object.entries(initialAgents)))
  }, [])

  // Subscribe to agent updates when connected
  useEffect(() => {
    if (isConnected) {
      // Subscribe to all agents for real-time updates
      Object.keys(AgentType).forEach(agentType => {
        subscribeToAgent(agentType)
      })
    }

    return () => {
      if (isConnected) {
        Object.keys(AgentType).forEach(agentType => {
          unsubscribeFromAgent(agentType)
        })
      }
    }
  }, [isConnected, subscribeToAgent, unsubscribeFromAgent])

  // Check if any agent is processing
  useEffect(() => {
    const processing = Array.from(agents.values()).some(agent => agent.processing)
    setIsAnyAgentProcessing(processing)
  }, [agents])

  const getAgentStatus = (agentType: AgentType): AgentStatusType => {
    return agents.get(agentType) || {
      status: 'inactive',
      lastActivity: null,
      processing: false,
      metrics: {},
      capabilities: [],
      configuration: {},
    }
  }

  const updateAgentStatus = (agentType: AgentType, statusUpdate: Partial<AgentStatusType>) => {
    setAgents(prev => {
      const newAgents = new Map(prev)
      const currentStatus = newAgents.get(agentType) || {
        status: 'inactive' as any,
        lastActivity: null,
        processing: false,
        metrics: {},
        capabilities: [],
        configuration: {},
      }
      
      newAgents.set(agentType, {
        ...currentStatus,
        ...statusUpdate,
        lastActivity: new Date().toISOString(),
      })
      
      return newAgents
    })
  }

  const sendAgentMessage = async (agentType: AgentType, message: any): Promise<any> => {
    try {
      // Update agent status to processing
      updateAgentStatus(agentType, { processing: true })

      // Send message via WebSocket or API
      const response = await fetch(`/api/v1/agents/${agentType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'agent_request',
          agentType,
          payload: message,
          timestamp: Date.now(),
        }),
      })

      if (!response.ok) {
        throw new Error(`Agent ${agentType} request failed`)
      }

      const result = await response.json()
      
      // Update metrics
      const currentAgent = getAgentStatus(agentType)
      updateAgentStatus(agentType, {
        processing: false,
        metrics: {
          ...currentAgent.metrics,
          totalRequests: (currentAgent.metrics.totalRequests || 0) + 1,
          successRate: ((currentAgent.metrics.successRate || 0) + 1) / 2,
          averageResponseTime: ((currentAgent.metrics.averageResponseTime || 0) + 200) / 2,
        },
      })

      return result
    } catch (error) {
      console.error(`Error sending message to agent ${agentType}:`, error)
      
      // Update agent status to error
      updateAgentStatus(agentType, { processing: false })
      
      throw error
    }
  }

  const getAgentMetrics = (agentType: AgentType) => {
    const agent = getAgentStatus(agentType)
    return agent.metrics || {}
  }

  const resetAllAgents = () => {
    setAgents(prev => {
      const newAgents = new Map()
      prev.forEach((agent, agentType) => {
        newAgents.set(agentType, {
          ...agent,
          processing: false,
          lastActivity: null,
        })
      })
      return newAgents
    })
  }

  const value: AgentContextType = {
    agents,
    learningProgressAgent: agents.get(AgentType.LEARNING_PROGRESS),
    quizGeneratorAgent: agents.get(AgentType.QUIZ_GENERATOR),
    codeAnalyzerAgent: agents.get(AgentType.CODE_ANALYZER),
    qualityAssessorAgent: agents.get(AgentType.QUALITY_ASSESSOR),
    contentRecommenderAgent: agents.get(AgentType.CONTENT_RECOMMENDER),
    analyticsAgent: agents.get(AgentType.ANALYTICS),
    isAnyAgentProcessing,
    getAgentStatus,
    updateAgentStatus,
    sendAgentMessage,
    getAgentMetrics,
    resetAllAgents,
  }

  return (
    <AgentContext.Provider value={value}>
      {children}
    </AgentContext.Provider>
  )
}

export function useAgent(): AgentContextType {
  const context = useContext(AgentContext)
  if (context === undefined) {
    throw new Error('useAgent must be used within an AgentProvider')
  }
  return context
}