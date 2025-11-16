import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { Quiz, QuizState } from '@/types/quiz'

const initialState: QuizState = {
  currentQuiz: null,
  quizzes: [],
  isLoading: false,
  isGenerating: false,
  error: null,
  currentQuestionIndex: 0,
  answers: {},
  timeRemaining: null,
  startTime: null,
  endTime: null,
  results: null,
  showResults: false,
  selectedDifficulty: 'medium',
  selectedTopic: null,
  questionCount: 10,
  adaptiveMode: true,
  attempts: [],
}

const quizSlice = createSlice({
  name: 'quiz',
  initialState,
  reducers: {
    setCurrentQuiz: (state, action: PayloadAction<Quiz | null>) => {
      state.currentQuiz = action.payload
      state.currentQuestionIndex = 0
      state.answers = {}
      state.results = null
      state.showResults = false
      state.timeRemaining = action.payload?.timeLimit || null
    },
    setQuizzes: (state, action: PayloadAction<Quiz[]>) => {
      state.quizzes = action.payload
    },
    addQuiz: (state, action: PayloadAction<Quiz>) => {
      state.quizzes = [action.payload, ...state.quizzes]
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setGenerating: (state, action: PayloadAction<boolean>) => {
      state.isGenerating = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setCurrentQuestionIndex: (state, action: PayloadAction<number>) => {
      state.currentQuestionIndex = action.payload
    },
    setAnswer: (state, action: PayloadAction<{ questionIndex: number; answer: string }>) => {
      state.answers[action.payload.questionIndex] = action.payload.answer
    },
    setTimeRemaining: (state, action: PayloadAction<number | null>) => {
      state.timeRemaining = action.payload
    },
    setStartTime: (state, action: PayloadAction<string>) => {
      state.startTime = action.payload
    },
    setEndTime: (state, action: PayloadAction<string>) => {
      state.endTime = action.payload
    },
    setResults: (state, action: PayloadAction<any>) => {
      state.results = action.payload
      state.showResults = true
      state.endTime = new Date().toISOString()
    },
    setShowResults: (state, action: PayloadAction<boolean>) => {
      state.showResults = action.payload
    },
    setSelectedDifficulty: (state, action: PayloadAction<'easy' | 'medium' | 'hard' | 'expert'>) => {
      state.selectedDifficulty = action.payload
    },
    setSelectedTopic: (state, action: PayloadAction<string | null>) => {
      state.selectedTopic = action.payload
    },
    setQuestionCount: (state, action: PayloadAction<number>) => {
      state.questionCount = action.payload
    },
    setAdaptiveMode: (state, action: PayloadAction<boolean>) => {
      state.adaptiveMode = action.payload
    },
    addAttempt: (state, action: PayloadAction<any>) => {
      state.attempts = [action.payload, ...state.attempts]
      // Keep only last 10 attempts
      if (state.attempts.length > 10) {
        state.attempts = state.attempts.slice(0, 10)
      }
    },
    nextQuestion: (state) => {
      if (state.currentQuiz && state.currentQuestionIndex < state.currentQuiz.questions.length - 1) {
        state.currentQuestionIndex++
      }
    },
    previousQuestion: (state) => {
      if (state.currentQuestionIndex > 0) {
        state.currentQuestionIndex--
      }
    },
    resetQuiz: (state) => {
      state.currentQuiz = null
      state.currentQuestionIndex = 0
      state.answers = {}
      state.timeRemaining = null
      state.startTime = null
      state.endTime = null
      state.results = null
      state.showResults = false
      state.error = null
    },
  },
})

export const {
  setCurrentQuiz,
  setQuizzes,
  addQuiz,
  setLoading,
  setGenerating,
  setError,
  setCurrentQuestionIndex,
  setAnswer,
  setTimeRemaining,
  setStartTime,
  setEndTime,
  setResults,
  setShowResults,
  setSelectedDifficulty,
  setSelectedTopic,
  setQuestionCount,
  setAdaptiveMode,
  addAttempt,
  nextQuestion,
  previousQuestion,
  resetQuiz,
} = quizSlice.actions

export default quizSlice.reducer