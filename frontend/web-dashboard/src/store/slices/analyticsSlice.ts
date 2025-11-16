import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AnalyticsState } from '@/types/analytics'

const initialState: AnalyticsState = {
  userAnalytics: null,
  learningProgress: [],
  skillLevels: {},
  predictions: null,
  trends: null,
  systemMetrics: null,
  isLoading: false,
  isGeneratingReport: false,
  error: null,
  selectedTimeRange: '7d',
  selectedMetrics: ['completion_rate', 'accuracy', 'engagement'],
  lastUpdated: null,
  alerts: [],
  recommendations: [],
}

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    setUserAnalytics: (state, action: PayloadAction<any>) => {
      state.userAnalytics = action.payload
      state.lastUpdated = new Date().toISOString()
    },
    setLearningProgress: (state, action: PayloadAction<any[]>) => {
      state.learningProgress = action.payload
    },
    setSkillLevels: (state, action: PayloadAction<Record<string, number>>) => {
      state.skillLevels = action.payload
    },
    setPredictions: (state, action: PayloadAction<any>) => {
      state.predictions = action.payload
    },
    setTrends: (state, action: PayloadAction<any>) => {
      state.trends = action.payload
    },
    setSystemMetrics: (state, action: PayloadAction<any>) => {
      state.systemMetrics = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setGeneratingReport: (state, action: PayloadAction<boolean>) => {
      state.isGeneratingReport = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setTimeRange: (state, action: PayloadAction<'1h' | '24h' | '7d' | '30d' | '90d'>) => {
      state.selectedTimeRange = action.payload
    },
    setSelectedMetrics: (state, action: PayloadAction<string[]>) => {
      state.selectedMetrics = action.payload
    },
    addAlert: (state, action: PayloadAction<any>) => {
      state.alerts = [action.payload, ...state.alerts]
      // Keep only last 50 alerts
      if (state.alerts.length > 50) {
        state.alerts = state.alerts.slice(0, 50)
      }
    },
    removeAlert: (state, action: PayloadAction<string>) => {
      state.alerts = state.alerts.filter(alert => alert.id !== action.payload)
    },
    setRecommendations: (state, action: PayloadAction<any[]>) => {
      state.recommendations = action.payload
    },
    addRecommendation: (state, action: PayloadAction<any>) => {
      state.recommendations = [action.payload, ...state.recommendations]
    },
    clearAnalytics: (state) => {
      state.userAnalytics = null
      state.learningProgress = []
      state.skillLevels = {}
      state.predictions = null
      state.trends = null
      state.systemMetrics = null
      state.error = null
      state.alerts = []
      state.recommendations = []
    },
  },
})

export const {
  setUserAnalytics,
  setLearningProgress,
  setSkillLevels,
  setPredictions,
  setTrends,
  setSystemMetrics,
  setLoading,
  setGeneratingReport,
  setError,
  setTimeRange,
  setSelectedMetrics,
  addAlert,
  removeAlert,
  setRecommendations,
  addRecommendation,
  clearAnalytics,
} = analyticsSlice.actions

export default analyticsSlice.reducer