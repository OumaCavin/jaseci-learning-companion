import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { User, AuthState } from '@/types/auth'

const initialState: AuthState = {
  user: null,
  isLoading: false,
  isAuthenticated: false,
  error: null,
  token: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setUser: (state, action: PayloadAction<User | null>) => {
      state.user = action.payload
      state.isAuthenticated = !!action.payload
      state.error = null
    },
    setToken: (state, action: PayloadAction<string | null>) => {
      state.token = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
      state.isLoading = false
    },
    clearAuth: (state) => {
      state.user = null
      state.isAuthenticated = false
      state.token = null
      state.error = null
      state.isLoading = false
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload }
      }
    },
  },
})

export const {
  setLoading,
  setUser,
  setToken,
  setError,
  clearAuth,
  updateUser,
} = authSlice.actions

export default authSlice.reducer