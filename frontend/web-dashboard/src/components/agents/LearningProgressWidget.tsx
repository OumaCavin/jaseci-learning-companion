'use client'

import React, { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  LinearProgress,
  Grid,
  Card,
  CardContent,
  Avatar,
  Chip,
  Skeleton,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  EmojiEvents as EmojiEventsIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material'

interface LearningProgressWidgetProps {
  preview?: boolean
}

interface ProgressData {
  currentLevel: number
  targetLevel: number
  progress: number
  studyStreak: number
  totalStudyTime: number
  skills: {
    name: string
    level: number
    progress: number
  }[]
  milestones: {
    title: string
    description: string
    achievedAt: string
    points: number
  }[]
}

export function LearningProgressWidget({ preview = false }: LearningProgressWidgetProps) {
  const [progressData, setProgressData] = useState<ProgressData | null>(null)
  const [loading, setLoading] = useState(!preview)

  useEffect(() => {
    if (preview) {
      // Mock data for preview
      setProgressData({
        currentLevel: 7,
        targetLevel: 10,
        progress: 70,
        studyStreak: 12,
        totalStudyTime: 2450,
        skills: [
          { name: 'Graph Theory', level: 8, progress: 85 },
          { name: 'Algorithm Design', level: 6, progress: 60 },
          { name: 'Jaseci Syntax', level: 9, progress: 90 },
          { name: 'Data Structures', level: 5, progress: 55 },
        ],
        milestones: [
          {
            title: 'Code Master',
            description: 'Completed 50 coding challenges',
            achievedAt: '2024-11-15T10:30:00Z',
            points: 500,
          },
          {
            title: 'Streak Warrior',
            description: '7-day study streak',
            achievedAt: '2024-11-14T15:45:00Z',
            points: 200,
          },
        ],
      })
      setLoading(false)
    } else {
      // Load real data
      loadProgressData()
    }
  }, [preview])

  const loadProgressData = async () => {
    try {
      const response = await fetch('/api/v1/agents/learning-progress')
      if (response.ok) {
        const data = await response.json()
        setProgressData(data)
      }
    } catch (error) {
      console.error('Failed to load progress data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box>
        <Skeleton variant="text" width="60%" />
        <Skeleton variant="rectangular" height={100} sx={{ mt: 2 }} />
        <Grid container spacing={2} sx={{ mt: 1 }}>
          {[...Array(4)].map((_, i) => (
            <Grid item xs={6} key={i}>
              <Skeleton variant="rectangular" height={60} />
            </Grid>
          ))}
        </Grid>
      </Box>
    )
  }

  if (!progressData) {
    return (
      <Box sx={{ textAlign: 'center', py: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No progress data available
        </Typography>
      </Box>
    )
  }

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
  }

  return (
    <Box>
      {/* Current Level Progress */}
      <Card sx={{ mb: 2, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <CardContent sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <TrendingUpIcon sx={{ mr: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Level {progressData.currentLevel}
            </Typography>
            <Chip
              label={`Target: ${progressData.targetLevel}`}
              size="small"
              sx={{ 
                ml: 'auto', 
                bgcolor: 'rgba(255,255,255,0.2)', 
                color: 'inherit',
                '& .MuiChip-label': { color: 'inherit' }
              }}
            />
          </Box>
          
          <Box sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2">
                Progress to Level {progressData.currentLevel + 1}
              </Typography>
              <Typography variant="body2">
                {progressData.progress}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progressData.progress}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: 'rgba(255,255,255,0.2)',
                '& .MuiLinearProgress-bar': {
                  bgcolor: 'rgba(255,255,255,0.8)',
                },
              }}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={6}>
          <Card sx={{ textAlign: 'center', p: 2 }}>
            <Avatar sx={{ bgcolor: 'success.main', mx: 'auto', mb: 1 }}>
              <ScheduleIcon />
            </Avatar>
            <Typography variant="h6" color="success.main">
              {progressData.studyStreak}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Day Streak
            </Typography>
          </Card>
        </Grid>
        
        <Grid item xs={6}>
          <Card sx={{ textAlign: 'center', p: 2 }}>
            <Avatar sx={{ bgcolor: 'info.main', mx: 'auto', mb: 1 }}>
              <SpeedIcon />
            </Avatar>
            <Typography variant="h6" color="info.main">
              {formatTime(progressData.totalStudyTime)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Total Study Time
            </Typography>
          </Card>
        </Grid>
      </Grid>

      {/* Skills Progress */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
          Skills Progress
        </Typography>
        
        {progressData.skills.map((skill, index) => (
          <Box key={skill.name} sx={{ mb: 1.5 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {skill.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Lvl {skill.level} • {skill.progress}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={skill.progress}
              sx={{
                height: 6,
                borderRadius: 3,
                '& .MuiLinearProgress-bar': {
                  bgcolor: `hsl(${(index * 60) % 360}, 70%, 50%)`,
                },
              }}
            />
          </Box>
        ))}
      </Box>

      {/* Recent Milestones */}
      {progressData.milestones.length > 0 && (
        <Box>
          <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, display: 'flex', alignItems: 'center' }}>
            <EmojiEventsIcon sx={{ mr: 0.5, fontSize: 16 }} />
            Recent Achievements
          </Typography>
          
          {progressData.milestones.slice(0, 2).map((milestone, index) => (
            <Card key={index} sx={{ mb: 1, p: 1.5, bgcolor: 'success.light', color: 'success.contrastText' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {milestone.title}
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.9 }}>
                    {milestone.description}
                  </Typography>
                </Box>
                <Chip
                  label={`+${milestone.points}`}
                  size="small"
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'inherit' }}
                />
              </Box>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  )
}