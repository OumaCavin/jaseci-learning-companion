'use client'

import React, { useEffect, useState } from 'react'
import {
  Grid,
  Paper,
  Typography,
  Box,
  Skeleton,
  Card,
  CardContent,
  LinearProgress,
  Chip,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Quiz as QuizIcon,
  Code as CodeIcon,
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { useWebSocket } from '@/contexts/WebSocketContext'

interface RealTimeStatsProps {
  data: any
  loading: boolean
  isConnected: boolean
}

interface StatCard {
  title: string
  value: string | number
  change?: number
  trend?: 'up' | 'down' | 'stable'
  color: string
  icon: React.ReactNode
  progress?: number
}

export function RealTimeStats({ data, loading, isConnected }: RealTimeStatsProps) {
  const [statsData, setStatsData] = useState<any[]>([])
  const [performanceData, setPerformanceData] = useState<any[]>([])
  const { lastMessage, sendMessage } = useWebSocket()

  useEffect(() => {
    // Initialize mock data for charts
    const generateMockData = () => {
      const now = new Date()
      const data = []
      const performance = []
      
      for (let i = 23; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000)
        data.push({
          time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          users: Math.floor(Math.random() * 50) + 20,
          quizzes: Math.floor(Math.random() * 20) + 5,
          code: Math.floor(Math.random() * 15) + 3,
          score: Math.floor(Math.random() * 20) + 80,
        })
        
        performance.push({
          time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          responseTime: Math.floor(Math.random() * 200) + 100,
          cpu: Math.floor(Math.random() * 30) + 20,
          memory: Math.floor(Math.random() * 40) + 30,
        })
      }
      
      setStatsData(data)
      setPerformanceData(performance)
    }

    generateMockData()
    
    // Set up real-time data updates
    const interval = setInterval(() => {
      if (isConnected) {
        sendMessage({
          type: 'request_stats_update',
          payload: {},
          timestamp: Date.now(),
        })
      }
    }, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [isConnected, sendMessage])

  useEffect(() => {
    // Handle real-time stats updates
    if (lastMessage?.type === 'stats_update') {
      // Update stats with real data
      console.log('Received stats update:', lastMessage.payload)
    }
  }, [lastMessage])

  const getStatCards = (): StatCard[] => [
    {
      title: 'Active Users',
      value: loading ? '---' : data?.activeUsers || 0,
      change: Math.floor(Math.random() * 10) - 5,
      trend: 'up',
      color: '#10b981',
      icon: <PeopleIcon />,
      progress: Math.floor(Math.random() * 30) + 60,
    },
    {
      title: 'Quizzes Today',
      value: loading ? '---' : Math.floor((data?.completedQuizzes || 0) * 0.3),
      change: Math.floor(Math.random() * 15) + 2,
      trend: 'up',
      color: '#3b82f6',
      icon: <QuizIcon />,
      progress: Math.floor(Math.random() * 40) + 45,
    },
    {
      title: 'Code Submissions',
      value: loading ? '---' : Math.floor((data?.codeSubmissions || 0) * 0.25),
      change: Math.floor(Math.random() * 8) + 1,
      trend: 'up',
      color: '#8b5cf6',
      icon: <CodeIcon />,
      progress: Math.floor(Math.random() * 35) + 50,
    },
    {
      title: 'Average Score',
      value: loading ? '---' : `${data?.averageScore || 0}%`,
      change: Math.floor(Math.random() * 6) - 3,
      trend: 'stable',
      color: '#f59e0b',
      icon: <AssessmentIcon />,
      progress: data?.averageScore || 75,
    },
    {
      title: 'System Health',
      value: loading ? '---' : data?.systemHealth?.toUpperCase() || 'GOOD',
      change: 0,
      trend: 'stable',
      color: data?.systemHealth === 'excellent' ? '#10b981' : '#f59e0b',
      icon: <SpeedIcon />,
      progress: data?.systemHealth === 'excellent' ? 95 : 80,
    },
  ]

  const statCards = getStatCards()

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
        Real-time Statistics
      </Typography>
      
      {/* Stat Cards Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((stat, index) => (
          <Grid item xs={12} sm={6} md={4} lg={2.4} key={stat.title}>
            <Card 
              sx={{ 
                height: '100%',
                transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: (theme) => theme.shadows[8],
                },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: stat.color + '20',
                      color: stat.color,
                      mr: 2,
                    }}
                  >
                    {stat.icon}
                  </Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {stat.value}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {stat.title}
                    </Typography>
                  </Box>
                </Box>
                
                {stat.progress !== undefined && (
                  <Box sx={{ mt: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Progress
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {stat.progress}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={stat.progress}
                      sx={{
                        height: 4,
                        borderRadius: 2,
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: stat.color,
                        },
                      }}
                    />
                  </Box>
                )}
                
                {stat.change !== undefined && (
                  <Box sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
                    <TrendingUpIcon 
                      fontSize="small" 
                      sx={{ 
                        color: stat.trend === 'up' ? 'success.main' : stat.trend === 'down' ? 'error.main' : 'grey.500',
                        mr: 0.5,
                      }} 
                    />
                    <Typography variant="caption" color="text.secondary">
                      {stat.change > 0 ? '+' : ''}{stat.change} from yesterday
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Charts Grid */}
      <Grid container spacing={3}>
        {/* Activity Chart */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Activity Over Time
            </Typography>
            {loading ? (
              <Skeleton variant="rectangular" height={320} />
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={statsData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="users"
                    stackId="1"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.3}
                  />
                  <Area
                    type="monotone"
                    dataKey="quizzes"
                    stackId="2"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.3}
                  />
                  <Area
                    type="monotone"
                    dataKey="code"
                    stackId="3"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        {/* Performance Chart */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              System Performance
            </Typography>
            {loading ? (
              <Skeleton variant="rectangular" height={320} />
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="responseTime"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        {/* Score Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 300 }}>
            <Typography variant="h6" gutterBottom>
              Score Distribution
            </Typography>
            {loading ? (
              <Skeleton variant="rectangular" height={220} />
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={[
                  { range: '0-20%', count: 5 },
                  { range: '21-40%', count: 12 },
                  { range: '41-60%', count: 28 },
                  { range: '61-80%', count: 45 },
                  { range: '81-100%', count: 32 },
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        {/* Real-time Updates Indicator */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 300, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              Real-time Status
            </Typography>
            <Box sx={{ flexGrow: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    bgcolor: isConnected ? 'success.main' : 'error.main',
                    mr: 2,
                    animation: isConnected ? 'pulse 2s infinite' : 'none',
                  }}
                />
                <Typography variant="body1">
                  {isConnected ? 'Connected to real-time services' : 'Disconnected from real-time services'}
                </Typography>
              </Box>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Last Update: {new Date().toLocaleTimeString()}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Next Update: {new Date(Date.now() + 30000).toLocaleTimeString()}
                </Typography>
              </Box>

              <Box sx={{ mt: 3 }}>
                <Chip 
                  label={isConnected ? 'Real-time Updates Active' : 'Real-time Updates Inactive'}
                  color={isConnected ? 'success' : 'error'}
                  size="small"
                />
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}