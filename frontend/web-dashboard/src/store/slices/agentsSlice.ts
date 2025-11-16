import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AgentType, AgentStatus as AgentStatusType, AgentsState } from '@/types/agent'

const initialState: AgentsState = {
  agents: {},
  activeAgent: null,
  isAnyAgentProcessing: false,
  agentMessages: {},
  lastActivity: null,
}

const agentsSlice = createSlice({
  name: 'agents',
  initialState,
  reducers: {
    setAgentStatus: (state, action: PayloadAction<{ agentType: AgentType; status: Partial<AgentStatusType> }>) => {
      const { agentType, status } = action.payload
      state.agents[agentType] = {
        ...state.agents[agentType],
        ...status,
        lastActivity: new Date().toISOString(),
      }
    },
    setActiveAgent: (state, action: PayloadAction<AgentType | null>) => {
      state.activeAgent = action.payload
    },
    setAnyAgentProcessing: (state, action: PayloadAction<boolean>) => {
      state.isAnyAgentProcessing = action.payload
    },
    addAgentMessage: (state, action: PayloadAction<{ agentType: AgentType; message: any }>) => {
      const { agentType, message } = action.payload
      if (!state.agentMessages[agentType]) {
        state.agentMessages[agentType] = []
      }
      state.agentMessages[agentType].push({
        ...message,
        timestamp: new Date().toISOString(),
        id: Date.now(),
      })
      
      // Keep only last 100 messages per agent
      if (state.agentMessages[agentType].length > 100) {
        state.agentMessages[agentType] = state.agentMessages[agentType].slice(-100)
      }
    },
    clearAgentMessages: (state, action: PayloadAction<AgentType>) => {
      const agentType = action.payload
      state.agentMessages[agentType] = []
    },
    setLastActivity: (state, action: PayloadAction<string | null>) => {
      state.lastActivity = action.payload
    },
    resetAllAgents: (state) => {
      Object.keys(state.agents).forEach(agentType => {
        if (state.agents[agentType as AgentType]) {
          state.agents[agentType as AgentType] = {
            ...state.agents[agentType as AgentType],
            processing: false,
            lastActivity: null,
          }
        }
      })
    },
  },
})

export const {
  setAgentStatus,
  setActiveAgent,
  setAnyAgentProcessing,
  addAgentMessage,
  clearAgentMessages,
  setLastActivity,
  resetAllAgents,
} = agentsSlice.actions

export default agentsSlice.reducer