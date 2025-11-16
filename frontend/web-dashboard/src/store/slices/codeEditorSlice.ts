import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { CodeEditorState } from '@/types/codeEditor'

const initialState: CodeEditorState = {
  code: '',
  language: 'jac',
  theme: 'vs-dark',
  fontSize: 14,
  isReadOnly: false,
  showMinimap: true,
  showLineNumbers: true,
  autoComplete: true,
  syntaxValidation: true,
  executionResults: null,
  isExecuting: false,
  errors: [],
  warnings: [],
  suggestions: [],
  codeMetrics: null,
  history: [],
  currentHistoryIndex: -1,
  savedAt: null,
}

const codeEditorSlice = createSlice({
  name: 'codeEditor',
  initialState,
  reducers: {
    setCode: (state, action: PayloadAction<string>) => {
      state.code = action.payload
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      state.language = action.payload
    },
    setTheme: (state, action: PayloadAction<string>) => {
      state.theme = action.payload
    },
    setFontSize: (state, action: PayloadAction<number>) => {
      state.fontSize = action.payload
    },
    setReadOnly: (state, action: PayloadAction<boolean>) => {
      state.isReadOnly = action.payload
    },
    setShowMinimap: (state, action: PayloadAction<boolean>) => {
      state.showMinimap = action.payload
    },
    setShowLineNumbers: (state, action: PayloadAction<boolean>) => {
      state.showLineNumbers = action.payload
    },
    setAutoComplete: (state, action: PayloadAction<boolean>) => {
      state.autoComplete = action.payload
    },
    setSyntaxValidation: (state, action: PayloadAction<boolean>) => {
      state.syntaxValidation = action.payload
    },
    setExecutionResults: (state, action: PayloadAction<any>) => {
      state.executionResults = action.payload
    },
    setIsExecuting: (state, action: PayloadAction<boolean>) => {
      state.isExecuting = action.payload
    },
    setErrors: (state, action: PayloadAction<any[]>) => {
      state.errors = action.payload
    },
    setWarnings: (state, action: PayloadAction<any[]>) => {
      state.warnings = action.payload
    },
    setSuggestions: (state, action: PayloadAction<any[]>) => {
      state.suggestions = action.payload
    },
    setCodeMetrics: (state, action: PayloadAction<any>) => {
      state.codeMetrics = action.payload
    },
    addToHistory: (state, action: PayloadAction<string>) => {
      state.history = [...state.history.slice(state.currentHistoryIndex + 1), action.payload]
      state.currentHistoryIndex = state.history.length - 1
    },
    undo: (state) => {
      if (state.currentHistoryIndex > 0) {
        state.currentHistoryIndex--
        state.code = state.history[state.currentHistoryIndex]
      }
    },
    redo: (state) => {
      if (state.currentHistoryIndex < state.history.length - 1) {
        state.currentHistoryIndex++
        state.code = state.history[state.currentHistoryIndex]
      }
    },
    saveCode: (state) => {
      state.savedAt = new Date().toISOString()
    },
    resetEditor: (state) => {
      state.code = ''
      state.errors = []
      state.warnings = []
      state.suggestions = []
      state.executionResults = null
      state.isExecuting = false
    },
  },
})

export const {
  setCode,
  setLanguage,
  setTheme,
  setFontSize,
  setReadOnly,
  setShowMinimap,
  setShowLineNumbers,
  setAutoComplete,
  setSyntaxValidation,
  setExecutionResults,
  setIsExecuting,
  setErrors,
  setWarnings,
  setSuggestions,
  setCodeMetrics,
  addToHistory,
  undo,
  redo,
  saveCode,
  resetEditor,
} = codeEditorSlice.actions

export default codeEditorSlice.reducer