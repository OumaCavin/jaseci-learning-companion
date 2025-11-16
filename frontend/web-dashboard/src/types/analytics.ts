// Analytics Types
export interface AnalyticsState {
  userAnalytics: UserAnalytics | null
  learningProgress: LearningProgress[]
  skillLevels: Record<string, number>
  predictions: PredictionResult | null
  trends: TrendAnalysis | null
  systemMetrics: SystemMetrics | null
  isLoading: boolean
  isGeneratingReport: boolean
  error: string | null
  selectedTimeRange: '1h' | '24h' | '7d' | '30d' | '90d'
  selectedMetrics: string[]
  lastUpdated: string | null
  alerts: Alert[]
  recommendations: Recommendation[]
}

export interface UserAnalytics {
  userId: string
  totalStudyTime: number // in minutes
  sessionsCompleted: number
  quizzesCompleted: number
  averageScore: number
  streakCount: number
  longestStreak: number
  currentStreak: number
  skillProgress: SkillProgress[]
  learningVelocity: number
  engagementScore: number
  consistencyScore: number
  achievementCount: number
  lastActive: string
  period: {
    start: string
    end: string
  }
}

export interface LearningProgress {
  date: string
  studyTime: number
  activitiesCompleted: number
  score: number
  skillLevel: number
  engagement: number
  milestones: Milestone[]
}

export interface SkillProgress {
  skill: string
  currentLevel: number
  targetLevel: number
  progress: number // 0-100
  lastUpdated: string
  masteryPoints: number
  nextMilestone: {
    level: number
    points: number
    description: string
  }
}

export interface Milestone {
  id: string
  type: 'streak' | 'score' | 'completion' | 'skill' | 'time'
  title: string
  description: string
  achievedAt: string
  points: number
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
}

export interface PredictionResult {
  userId: string
  predictionType: 'success_probability' | 'difficulty_need' | 'completion_time' | 'skill_development'
  results: {
    prediction: number
    confidence: number
    factors: {
      name: string
      impact: number // -1 to 1
      importance: number // 0 to 1
    }[]
    timeframe: string
  }
  recommendations: string[]
  generatedAt: string
}

export interface TrendAnalysis {
  period: {
    start: string
    end: string
  }
  trends: {
    metric: string
    direction: 'increasing' | 'decreasing' | 'stable'
    strength: number // 0 to 1
    change: number
    confidence: number
  }[]
  insights: string[]
  forecasts: {
    metric: string
    predicted: number
    confidence: number
    timeframe: string
  }[]
}

export interface SystemMetrics {
  timestamp: string
  activeUsers: number
  totalUsers: number
  systemLoad: number
  responseTime: number
  errorRate: number
  uptime: number
  resourceUsage: {
    cpu: number
    memory: number
    disk: number
    network: number
  }
  agentMetrics: Record<string, {
    requests: number
    successRate: number
    avgResponseTime: number
    active: boolean
  }>
}

export interface Alert {
  id: string
  type: 'warning' | 'error' | 'info' | 'success'
  category: 'system' | 'user' | 'agent' | 'security'
  title: string
  message: string
  timestamp: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  acknowledged: boolean
  metadata?: Record<string, any>
}

export interface Recommendation {
  id: string
  type: 'study_plan' | 'skill_development' | 'content_suggestion' | 'practice_area'
  title: string
  description: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  category: string
  actions: {
    label: string
    action: string
    parameters?: Record<string, any>
  }[]
  estimatedTime: number // in minutes
  successRate?: number
  createdAt: string
  expiresAt?: string
}