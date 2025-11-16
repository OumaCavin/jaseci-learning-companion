// Dashboard Types
export interface DashboardStats {
  totalUsers: number
  activeUsers: number
  completedQuizzes: number
  codeSubmissions: number
  averageScore: number
  systemHealth: 'excellent' | 'good' | 'fair' | 'poor'
  uptime: number
  responseTime: number
  errorRate: number
  lastUpdated: string
}

export interface DashboardState {
  stats: DashboardStats | null
  loading: boolean
  error: string | null
  lastUpdated: string | null
  selectedTimeRange: '1h' | '24h' | '7d' | '30d'
  refreshInterval: number
}

export interface ActivityItem {
  id: string
  type: 'quiz_completed' | 'code_submitted' | 'progress_updated' | 'achievement_unlocked' | 'agent_interaction'
  user: {
    id: string
    username: string
    avatar?: string
  }
  title: string
  description: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface SystemMetric {
  name: string
  value: number | string
  unit?: string
  trend: 'up' | 'down' | 'stable'
  change?: number
  threshold?: {
    warning: number
    critical: number
  }
}