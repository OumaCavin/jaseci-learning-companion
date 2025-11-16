import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { DashboardState } from '@/types/dashboard'

const initialState: DashboardState = {
  stats: null,
  loading: true,
  error: null,
  lastUpdated: null,
  selectedTimeRange: '7d',
  refreshInterval: 30000, // 30 seconds
}

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    setStats: (state, action: PayloadAction<any>) => {
      state.stats = action.payload
      state.lastUpdated = new Date().toISOString()
      state.error = null
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload
      state.loading = false
    },
    setTimeRange: (state, action: PayloadAction<'1h' | '24h' | '7d' | '30d'>) => {
      state.selectedTimeRange = action.payload
    },
    setRefreshInterval: (state, action: PayloadAction<number>) => {
      state.refreshInterval = action.payload
    },
    clearDashboard: (state) => {
      state.stats = null
      state.error = null
      state.loading = true
      state.lastUpdated = null
    },
  },
})

export const {
  setStats,
  setLoading,
  setError,
  setTimeRange,
  setRefreshInterval,
  clearDashboard,
} = dashboardSlice.actions

export default dashboardSlice.reducer