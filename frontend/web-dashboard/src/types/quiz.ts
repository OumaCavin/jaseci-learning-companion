// Quiz Types
export interface Quiz {
  id: string
  title: string
  description: string
  difficulty: 'easy' | 'medium' | 'hard' | 'expert'
  topic: string
  language: 'jac' | 'python' | 'javascript' | 'general'
  timeLimit: number // in seconds
  questionCount: number
  questions: QuizQuestion[]
  tags: string[]
  createdAt: string
  updatedAt: string
  isAdaptive: boolean
  metadata?: {
    estimatedDifficulty: number
    successRate: number
    averageTime: number
  }
}

export interface QuizQuestion {
  id: string
  type: 'multiple_choice' | 'true_false' | 'fill_blank' | 'code_completion' | 'code_analysis'
  question: string
  options?: string[]
  correctAnswer: string | string[]
  explanation: string
  points: number
  timeLimit?: number
  code?: {
    language: string
    content: string
    language: 'jac' | 'python' | 'javascript'
  }
  hints?: string[]
  difficulty: number
  tags: string[]
}

export interface QuizState {
  currentQuiz: Quiz | null
  quizzes: Quiz[]
  isLoading: boolean
  isGenerating: boolean
  error: string | null
  currentQuestionIndex: number
  answers: Record<number, string>
  timeRemaining: number | null
  startTime: string | null
  endTime: string | null
  results: QuizResult | null
  showResults: boolean
  selectedDifficulty: 'easy' | 'medium' | 'hard' | 'expert'
  selectedTopic: string | null
  questionCount: number
  adaptiveMode: boolean
  attempts: QuizAttempt[]
}

export interface QuizAttempt {
  id: string
  quizId: string
  userId: string
  startTime: string
  endTime?: string
  answers: Record<number, string>
  score?: number
  maxScore: number
  timeTaken: number
  isCompleted: boolean
  difficulty: 'easy' | 'medium' | 'hard' | 'expert'
  performance: {
    accuracy: number
    speed: number
    consistency: number
  }
}

export interface QuizResult {
  attempt: QuizAttempt
  score: number
  maxScore: number
  percentage: number
  grade: 'A' | 'B' | 'C' | 'D' | 'F'
  timeSpent: number
  questions: {
    id: string
    userAnswer: string
    correctAnswer: string
    isCorrect: boolean
    points: number
    explanation?: string
  }[]
  insights: {
    strongAreas: string[]
    weakAreas: string[]
    recommendations: string[]
    nextSteps: string[]
  }
  skillAssessment: {
    currentLevel: number
    projectedLevel: number
    confidence: number
  }
}

export interface QuizGenerationRequest {
  topic: string
  difficulty: 'easy' | 'medium' | 'hard' | 'expert'
  questionCount: number
  timeLimit?: number
  includeCodeQuestions: boolean
  languages: string[]
  customRequirements?: string
  userLevel: number
  adaptiveMode: boolean
}