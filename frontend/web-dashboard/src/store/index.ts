import { configureStore } from '@reduxjs/toolkit'
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux'
import authSlice from './slices/authSlice'
import agentsSlice from './slices/agentsSlice'
import dashboardSlice from './slices/dashboardSlice'
import codeEditorSlice from './slices/codeEditorSlice'
import quizSlice from './slices/quizSlice'
import analyticsSlice from './slices/analyticsSlice'

export const store = configureStore({
  reducer: {
    auth: authSlice,
    agents: agentsSlice,
    dashboard: dashboardSlice,
    codeEditor: codeEditorSlice,
    quiz: quizSlice,
    analytics: analyticsSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [
          'persist/PERSIST',
          'persist/REHYDRATE',
          'agents/updateAgentStatus',
        ],
        ignoredPaths: ['register', 'rehydrate'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = () => useDispatch<AppDispatch>()
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector