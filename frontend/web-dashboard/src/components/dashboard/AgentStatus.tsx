'use client'

import React from 'react'
import {
  Grid,
  Paper,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Tooltip,
  Card,
  CardContent,
  Avatar,
} from '@mui/material'
import {
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  Quiz as QuizIcon,
  Code as CodeIcon,
  Assessment as AssessmentIcon,
  Insights as InsightsIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { AgentType } from '@/types/agent'

interface AgentStatusProps {
  agents: Array<{
    title: string
    description: string
    icon: React.ReactNode
    color: string
    path: string
  }>
}

interface AgentStatusData {
  status: 'inactive' | 'active' | 'processing' | 'error' | 'maintenance'
  lastActivity: string | null
  processing: boolean
  metrics: {
    totalRequests?: number
    successRate?: number
    averageResponseTime?: number
  }
  capabilities: string[]
}

export function AgentStatus({ agents }: AgentStatusProps) {
  // Mock agent status data - in real app this would come from context/API
  const agentStatuses: Record<string, AgentStatusData> = {
    'Learning Progress': {
      status: 'active',
      lastActivity: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
      processing: false,
      metrics: {
        totalRequests: 156,
        successRate: 98.5,
        averageResponseTime: 245,
      },
      capabilities: ['progress_tracking', 'streak_monitoring'],
    },
    'Quiz Generator': {
      status: 'processing',
      lastActivity: new Date(Date.now() - 30 * 1000).toISOString(),
      processing: true,
      metrics: {
        totalRequests: 89,
        successRate: 96.2,
        averageResponseTime: 1200,
      },
      capabilities: ['adaptive_quiz_generation', 'byllm_integration'],
    },
    'Code Analyzer': {
      status: 'active',
      lastActivity: new Date(Date.now() - 45 * 1000).toISOString(),
      processing: false,
      metrics: {
        totalRequests: 234,
        successRate: 94.8,
        averageResponseTime: 890,
      },
      capabilities: ['ast_parsing', 'code_context_graph'],
    },
    'Quality Assessor': {
      status: 'active',
      lastActivity: new Date(Date.now() - 1 * 60 * 1000).toISOString(),
      processing: false,
      metrics: {
        totalRequests: 178,
        successRate: 97.1,
        averageResponseTime: 1560,
      },
      capabilities: ['correctness_assessment', 'security_analysis'],
    },
    'Content Recommender': {
      status: 'active',
      lastActivity: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
      processing: false,
      metrics: {
        totalRequests: 267,
        successRate: 95.7,
        averageResponseTime: 780,
      },
      capabilities: ['collaborative_filtering', 'learning_path_generation'],
    },
    'Analytics': {
      status: 'maintenance',
      lastActivity: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      processing: false,
      metrics: {
        totalRequests: 45,
        successRate: 88.9,
        averageResponseTime: 2100,
      },
      capabilities: ['predictive_analytics', 'trend_analysis'],
    },
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon sx={{ color: 'success.main' }} />
      case 'processing':
        return <SpeedIcon sx={{ color: 'warning.main', animation: 'spin 2s linear infinite' }} />
      case 'error':
        return <ErrorIcon sx={{ color: 'error.main' }} />
      case 'maintenance':
        return <WarningIcon sx={{ color: 'warning.main' }} />
      default:
        return <ErrorIcon sx={{ color: 'grey.500' }} />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success'
      case 'processing':
        return 'warning'
      case 'error':
        return 'error'
      case 'maintenance':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getStatusText = (status: string) => {
    return status.charAt(0).toUpperCase() + status.slice(1)
  }

  const formatLastActivity = (lastActivity: string | null) => {
    if (!lastActivity) return 'Never'
    
    const now = new Date()
    const activity = new Date(lastActivity)
    const diffMs = now.getTime() - activity.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
    return `${Math.floor(diffMins / 1440)}d ago`
  }

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
        Agent System Status
      </Typography>
      
      <Grid container spacing={3}>
        {agents.map((agent) => {
          const status = agentStatuses[agent.title]
          if (!status) return null

          return (
            <Grid item xs={12} sm={6} lg={4} key={agent.title}>
              <Card 
                sx={{ 
                  height: '100%',
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: (theme) => theme.shadows[6],
                  },
                  border: status.status === 'processing' ? '2px solid' : '1px solid',
                  borderColor: status.status === 'processing' ? 'warning.main' : 'divider',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  {/* Agent Header */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar
                      sx={{
                        bgcolor: agent.color + '20',
                        color: agent.color,
                        mr: 2,
                        width: 48,
                        height: 48,
                      }}
                    >
                      {agent.icon}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {agent.title}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        {getStatusIcon(status.status)}
                        <Chip
                          label={getStatusText(status.status)}
                          color={getStatusColor(status.status) as any}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    </Box>
                  </Box>

                  {/* Capabilities */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Capabilities
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {status.capabilities.slice(0, 2).map((capability) => (
                        <Chip
                          key={capability}
                          label={capability.replace(/_/g, ' ')}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                      ))}
                      {status.capabilities.length > 2 && (
                        <Chip
                          label={`+${status.capabilities.length - 2}`}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                      )}
                    </Box>
                  </Box>

                  {/* Metrics */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Performance Metrics
                    </Typography>
                    
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mt: 1 }}>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {status.metrics.totalRequests || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Requests
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {status.metrics.successRate?.toFixed(1) || 0}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Success Rate
                        </Typography>
                      </Box>
                    </Box>

                    <Box sx={{ mt: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          Success Rate
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {status.metrics.successRate?.toFixed(1) || 0}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={status.metrics.successRate || 0}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: (status.metrics.successRate || 0) >= 95 ? 'success.main' : 
                                           (status.metrics.successRate || 0) >= 90 ? 'warning.main' : 'error.main',
                          },
                        }}
                      />
                    </Box>
                  </Box>

                  {/* Last Activity */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      Last Active: {formatLastActivity(status.lastActivity)}
                    </Typography>
                    
                    {status.processing && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                          sx={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            bgcolor: 'warning.main',
                            animation: 'pulse 1s infinite',
                          }}
                        />
                        <Typography variant="caption" color="warning.main" sx={{ fontWeight: 500 }}>
                          Processing
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )
        })}
      </Grid>
    </Box>
  )
}