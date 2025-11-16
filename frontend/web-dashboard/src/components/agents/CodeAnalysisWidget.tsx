'use client'

import React, { useEffect, useState } from 'react'
import { Box, Typography, Card, CardContent, Chip, Grid, Button, Skeleton, Alert } from '@mui/material'
import { Code as CodeIcon, Psychology as PsychologyIcon, Timeline as TimelineIcon, BugReport as BugIcon } from '@mui/icons-material'
import { useAgent } from '@/contexts/AgentContext'

interface CodeAnalysisWidgetProps {
  preview?: boolean
}

export function CodeAnalysisWidget({ preview = false }: CodeAnalysisWidgetProps) {
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [loading, setLoading] = useState(!preview)
  const [error, setError] = useState<string | null>(null)
  const { sendAgentMessage } = useAgent()

  useEffect(() => {
    if (preview) {
      setAnalysisData({
        recentSubmissions: 3,
        averageComplexity: 'Medium',
        securityScore: 95,
        performanceScore: 87,
        maintainabilityScore: 92,
        lastAnalysis: '2 minutes ago',
        issuesFound: {
          critical: 0,
          warnings: 2,
          info: 5,
        },
      })
      setLoading(false)
    }
  }, [preview])

  const analyzeCode = async () => {
    try {
      setError(null)
      const result = await sendAgentMessage('code_analyzer', {
        action: 'analyze_code',
        code: 'sample_code',
        language: 'jac',
      })
      setAnalysisData(result)
    } catch (error) {
      setError('Failed to analyze code')
    }
  }

  if (loading) return <Skeleton variant="rectangular" height={200} />

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <Card sx={{ mb: 2, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <CardContent sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center' }}>
            <CodeIcon sx={{ mr: 1 }} />
            Code Context Graph Analysis
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9, mt: 1 }}>
            Advanced AST parsing and code relationship mapping
          </Typography>
        </CardContent>
      </Card>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={6}>
          <Card sx={{ textAlign: 'center', p: 1 }}>
            <Typography variant="h6" color="success.main">
              {analysisData?.securityScore}%
            </Typography>
            <Typography variant="caption">Security Score</Typography>
          </Card>
        </Grid>
        <Grid item xs={6}>
          <Card sx={{ textAlign: 'center', p: 1 }}>
            <Typography variant="h6" color="warning.main">
              {analysisData?.performanceScore}%
            </Typography>
            <Typography variant="caption">Performance</Typography>
          </Card>
        </Grid>
      </Grid>

      <Button
        variant="contained"
        fullWidth
        startIcon={<PsychologyIcon />}
        onClick={analyzeCode}
      >
        Analyze Code Submission
      </Button>
    </Box>
  )
}