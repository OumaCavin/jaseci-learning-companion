'use client'

import React, { useEffect, useState } from 'react'
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Alert,
  Skeleton,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Code as CodeIcon,
  Quiz as QuizIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as PsychologyIcon,
  Analytics as AnalyticsIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material'
import { useAuth } from '@/contexts/AuthContext'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { DashboardHeader } from '@/components/dashboard/DashboardHeader'
import { RealTimeStats } from '@/components/dashboard/RealTimeStats'
import { AgentStatus } from '@/components/dashboard/AgentStatus'
import { RecentActivity } from '@/components/dashboard/RecentActivity'
import { LearningProgressWidget } from '@/components/agents/LearningProgressWidget'
import { QuizWidget } from '@/components/agents/QuizWidget'
import { CodeAnalysisWidget } from '@/components/agents/CodeAnalysisWidget'
import { QualityAssessmentWidget } from '@/components/agents/QualityAssessmentWidget'
import { ContentRecommendationWidget } from '@/components/agents/ContentRecommendationWidget'
import { AnalyticsWidget } from '@/components/agents/AnalyticsWidget'
import OSPGraphWidget from '@/components/osp/OSPGraphWidget'
import { Link } from 'next/link'

export default function DashboardPage() {
  const { user, isLoading: authLoading } = useAuth()
  const { isConnected, connectionStatus } = useWebSocket()
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)

  // Mock data - replace with real API calls
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        setDashboardData({
          totalUsers: 1247,
          activeUsers: 89,
          completedQuizzes: 3421,
          codeSubmissions: 1567,
          averageScore: 87.5,
          systemHealth: 'excellent',
        })
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [])

  const agentCards = [
    {
      title: 'Learning Progress',
      description: 'Track your learning journey and achievements',
      icon: TrendingUpIcon,
      color: '#10b981',
      widget: LearningProgressWidget,
      path: '/agents/learning-progress',
    },
    {
      title: 'Quiz Generator',
      description: 'AI-powered adaptive quizzes for knowledge assessment',
      icon: QuizIcon,
      color: '#3b82f6',
      widget: QuizWidget,
      path: '/agents/quiz-generator',
    },
    {
      title: 'Code Analyzer',
      description: 'Deep code analysis with Context Graph technology',
      icon: CodeIcon,
      color: '#8b5cf6',
      widget: CodeAnalysisWidget,
      path: '/agents/code-analyzer',
    },
    {
      title: 'Quality Assessor',
      description: '5-dimensional code quality evaluation',
      icon: AssessmentIcon,
      color: '#f59e0b',
      widget: QualityAssessmentWidget,
      path: '/agents/quality-assessor',
    },
    {
      title: 'Content Recommender',
      description: 'Personalized learning content suggestions',
      icon: PsychologyIcon,
      color: '#06b6d4',
      widget: ContentRecommendationWidget,
      path: '/agents/content-recommender',
    },
    {
      title: 'Analytics',
      description: 'Predictive analytics and system insights',
      icon: AnalyticsIcon,
      color: '#ef4444',
      widget: AnalyticsWidget,
      path: '/agents/analytics',
    },
    {
      title: 'OSP Graph',
      description: 'Interactive code analysis and graph visualization',
      icon: TimelineIcon,
      color: '#8b5cf6',
      widget: OSPGraphWidget,
      path: '/dashboard/osp-graph',
    },
  ]

  if (authLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Skeleton variant="text" height={60} />
        <Grid container spacing={3}>
          {[...Array(6)].map((_, i) => (
            <Grid item xs={12} md={4} key={i}>
              <Skeleton variant="rectangular" height={200} />
            </Grid>
          ))}
        </Grid>
      </Container>
    )
  }

  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: 'background.default' }}>
      <DashboardHeader />
      
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Connection Status Alert */}
        {!isConnected && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            {connectionStatus === 'connecting' && 'Connecting to real-time services...'}
            {connectionStatus === 'disconnected' && 'Real-time updates unavailable. Some features may be limited.'}
            {connectionStatus === 'reconnecting' && 'Reconnecting to real-time services...'}
          </Alert>
        )}

        {/* Real-time Statistics */}
        <RealTimeStats 
          data={dashboardData} 
          loading={loading}
          isConnected={isConnected}
        />

        {/* Agent Status Overview */}
        <AgentStatus agents={agentCards} />

        {/* Main Agent Grid */}
        <Grid container spacing={3} sx={{ mt: 2 }}>
          {agentCards.map((agent, index) => (
            <Grid item xs={12} lg={6} xl={4} key={agent.title}>
              <Card 
                sx={{ 
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: (theme) => theme.shadows[8],
                  },
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: agent.color + '20',
                        color: agent.color,
                        mr: 2,
                      }}
                    >
                      <agent.icon fontSize="large" />
                    </Box>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" component="h2" gutterBottom>
                        {agent.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {agent.description}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Agent Widget Preview */}
                  <Box sx={{ mt: 2 }}>
                    <agent.widget preview />
                  </Box>
                </CardContent>

                <CardActions sx={{ p: 2, pt: 0 }}>
                  <Button
                    component={Link}
                    href={agent.path}
                    variant="contained"
                    size="small"
                    fullWidth
                    sx={{
                      bgcolor: agent.color,
                      '&:hover': {
                        bgcolor: agent.color + 'cc',
                      },
                    }}
                  >
                    Open {agent.title}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Recent Activity */}
        <RecentActivity />

        {/* System Information */}
        <Paper sx={{ p: 3, mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            System Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="primary">
                  {loading ? '---' : dashboardData?.totalUsers || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Users
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="success.main">
                  {loading ? '---' : dashboardData?.activeUsers || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Sessions
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="info.main">
                  {loading ? '---' : dashboardData?.completedQuizzes || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Quizzes Completed
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Chip
                  label={dashboardData?.systemHealth || 'Loading...'}
                  color={
                    dashboardData?.systemHealth === 'excellent' 
                      ? 'success' 
                      : dashboardData?.systemHealth === 'good' 
                        ? 'warning' 
                        : 'error'
                  }
                  size="small"
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  System Health
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </Container>
    </Box>
  )
}