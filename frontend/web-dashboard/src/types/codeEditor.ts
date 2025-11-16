// Code Editor Types
export interface CodeEditorState {
  code: string
  language: string
  theme: string
  fontSize: number
  isReadOnly: boolean
  showMinimap: boolean
  showLineNumbers: boolean
  autoComplete: boolean
  syntaxValidation: boolean
  executionResults: ExecutionResult | null
  isExecuting: boolean
  errors: EditorError[]
  warnings: EditorWarning[]
  suggestions: CodeSuggestion[]
  codeMetrics: CodeMetrics | null
  history: string[]
  currentHistoryIndex: number
  savedAt: string | null
}

export interface ExecutionResult {
  success: boolean
  output?: string
  error?: string
  executionTime: number
  memoryUsage?: number
  timestamp: string
}

export interface EditorError {
  line: number
  column: number
  message: string
  severity: 'error' | 'warning' | 'info'
  source: string
}

export interface EditorWarning extends EditorError {
  // Inherits all properties from EditorError
}

export interface CodeSuggestion {
  startLine: number
  endLine: number
  text: string
  type: 'completion' | 'snippet' | 'refactoring'
  confidence: number
  description?: string
}

export interface CodeMetrics {
  linesOfCode: number
  cyclomaticComplexity: number
  cognitiveComplexity: number
  maintainabilityIndex: number
  testCoverage?: number
  documentationCoverage: number
  technicalDebtRatio: number
  duplicatedLines: number
}

export interface CodeAnalysisResult {
  syntaxValid: boolean
  errors: EditorError[]
  warnings: EditorWarning[]
  metrics: CodeMetrics
  suggestions: CodeSuggestion[]
  securityIssues?: SecurityIssue[]
  performanceIssues?: PerformanceIssue[]
}

export interface SecurityIssue {
  severity: 'low' | 'medium' | 'high' | 'critical'
  type: string
  description: string
  line: number
  column: number
  cweId?: string
  recommendation: string
}

export interface PerformanceIssue {
  severity: 'low' | 'medium' | 'high'
  type: string
  description: string
  line: number
  column: number
  impact: string
  recommendation: string
}