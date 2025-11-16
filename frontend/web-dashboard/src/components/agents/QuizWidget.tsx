'use client'

import React, { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Skeleton,
  Alert,
} from '@mui/material'
import {
  Quiz as QuizIcon,
  AutoAwesome as AutoAwesomeIcon,
  Timer as TimerIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material'
import { useAgent } from '@/contexts/AgentContext'

interface QuizWidgetProps {
  preview?: boolean
}

interface QuizPreview {
  title: string
  difficulty: 'easy' | 'medium' | 'hard' | 'expert'
  questions: number
  estimatedTime: number
  topic: string
  adaptive: boolean
  recentPerformance?: {
    averageScore: number
    totalQuizzes: number
    improvement: number
  }
}

export function QuizWidget({ preview = false }: QuizWidgetProps) {
  const [quizPreview, setQuizPreview] = useState<QuizPreview | null>(null)
  const [loading, setLoading] = useState(!preview)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { sendAgentMessage } = useAgent()

  useEffect(() => {
    if (preview) {
      // Mock data for preview
      setQuizPreview({
        title: 'Jaseci Graph Algorithms',
        difficulty: 'medium',
        questions: 15,
        estimatedTime: 20,
        topic: 'graph_algorithms',
        adaptive: true,
        recentPerformance: {
          averageScore: 87,
          totalQuizzes: 12,
          improvement: 15,
        },
      })
      setLoading(false)
    } else {
      loadQuizPreview()
    }
  }, [preview])

  const loadQuizPreview = async () => {
    try {
      const result = await sendAgentMessage('quiz_generator', {
        action: 'get_preview',
        userId: 'current_user',
      })
      setQuizPreview(result)
    } catch (error) {
      console.error('Failed to load quiz preview:', error)
      setError('Failed to load quiz data')
    } finally {
      setLoading(false)
    }
  }

  const generateQuiz = async () => {
    try {
      setGenerating(true)
      setError(null)
      
      const result = await sendAgentMessage('quiz_generator', {
        action: 'generate_quiz',
        userId: 'current_user',
        preferences: {
          difficulty: quizPreview?.difficulty || 'medium',
          topic: quizPreview?.topic || 'general',
          questionCount: 10,
          adaptiveMode: true,
        },
      })
      
      // Navigate to quiz or show results
      console.log('Quiz generated:', result)
    } catch (error) {
      console.error('Failed to generate quiz:', error)
      setError('Failed to generate quiz. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'success'
      case 'medium':
        return 'warning'
      case 'hard':
        return 'error'
      case 'expert':
        return 'error'
      default:
        return 'default'
    }
  }

  if (loading) {
    return (
      <Box>
        <Skeleton variant="text" width="70%" />
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={8}>
            <Skeleton variant="rectangular" height={80} />
          </Grid>
          <Grid item xs={4}>
            <Skeleton variant="rectangular" height={80} />
          </Grid>
        </Grid>
        <Skeleton variant="rectangular" height={40} sx={{ mt: 2 }} />
      </Box>
    )
  }

  if (!quizPreview) {
    return (
      <Box sx={{ textAlign: 'center', py: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No quiz data available
        </Typography>
      </Box>
    )
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Quiz Header */}
      <Card sx={{ mb: 2, bgcolor: 'secondary.main', color: 'secondary.contrastText' }}>
        <CardContent sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center' }}>
              <QuizIcon sx={{ mr: 1 }} />
              {quizPreview.title}
            </Typography>
            {quizPreview.adaptive && (
              <Chip
                label="Adaptive"
                size="small"
                icon={<AutoAwesomeIcon />}
                sx={{ 
                  bgcolor: 'rgba(255,255,255,0.2)', 
                  color: 'inherit',
                  '& .MuiChip-icon': { color: 'inherit' }
                }}
              />
            )}
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 1 }}>
            <Chip
              label={quizPreview.difficulty.toUpperCase()}
              size="small"
              color={getDifficultyColor(quizPreview.difficulty) as any}
            />
            <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
              <TimerIcon sx={{ mr: 0.5, fontSize: 16 }} />
              {quizPreview.estimatedTime} min
            </Typography>
            <Typography variant="body2">
              {quizPreview.questions} questions
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Performance Stats */}
      {quizPreview.recentPerformance && (
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={4}>
            <Card sx={{ textAlign: 'center', p: 1.5 }}>
              <Typography variant="h6" color="success.main">
                {quizPreview.recentPerformance.averageScore}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg Score
              </Typography>
            </Card>
          </Grid>
          
          <Grid item xs={4}>
            <Card sx={{ textAlign: 'center', p: 1.5 }}>
              <Typography variant="h6" color="primary.main">
                {quizPreview.recentPerformance.totalQuizzes}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Quizzes
              </Typography>
            </Card>
          </Grid>
          
          <Grid item xs={4}>
            <Card sx={{ textAlign: 'center', p: 1.5 }}>
              <Typography variant="h6" color="info.main">
                +{quizPreview.recentPerformance.improvement}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Improvement
              </Typography>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Quiz Generation Section */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
          Generate New Quiz
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <LinearProgress
            variant="determinate"
            value={quizPreview.recentPerformance?.averageScore || 75}
            sx={{
              height: 8,
              borderRadius: 4,
              mb: 1,
              '& .MuiLinearProgress-bar': {
                bgcolor: (quizPreview.recentPerformance?.averageScore || 75) >= 80 ? 'success.main' : 'warning.main',
              },
            }}
          />
          <Typography variant="caption" color="text.secondary">
            Performance Level: {quizPreview.recentPerformance?.averageScore || 75 >= 80 ? 'Excellent' : 'Good'}
          </Typography>
        </Box>

        <Button
          variant="contained"
          fullWidth
          onClick={generateQuiz}
          disabled={generating}
          startIcon={generating ? undefined : <PsychologyIcon />}
          sx={{ 
            mb: 1,
            background: 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
            '&:hover': {
              background: 'linear-gradient(45deg, #1d4ed8, #6d28d9)',
            },
          }}
        >
          {generating ? 'Generating Quiz...' : 'Generate Adaptive Quiz'}
        </Button>
      </Box>

      {/* Recent Quizzes */}
      <Box>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
          Recent Performance
        </Typography>
        
        {[...Array(3)].map((_, index) => (
          <Box 
            key={index} 
            sx={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              mb: 1,
              p: 1,
              bgcolor: 'background.default',
              borderRadius: 1,
            }}
          >
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                Quiz #{12 - index}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {new Date(Date.now() - index * 24 * 60 * 60 * 1000).toLocaleDateString()}
              </Typography>
            </Box>
            <Chip
              label={`${80 + index * 5}%`}
              size="small"
              color={index === 0 ? 'success' : 'default'}
              variant={index === 0 ? 'filled' : 'outlined'}
            />
          </Box>
        ))}
      </Box>
    </Box>
  )
}