'use client'

import React from 'react'
import { Box, Typography, Card, CardContent, Grid, LinearProgress, Chip } from '@mui/material'
import { Assessment as AssessmentIcon, Shield as ShieldIcon, Speed as SpeedIcon, Code as CodeIcon } from '@mui/icons-material'

export function QualityAssessmentWidget({ preview = false }: { preview?: boolean }) {
  const assessmentData = {
    dimensions: [
      { name: 'Correctness', score: 95, color: 'success.main' },
      { name: 'Performance', score: 87, color: 'warning.main' },
      { name: 'Security', score: 92, color: 'info.main' },
      { name: 'Code Quality', score: 89, color: 'secondary.main' },
      { name: 'Documentation', score: 78, color: 'error.main' },
    ],
    overallScore: 88.2,
    lastAssessment: '5 minutes ago',
  }

  return (
    <Box>
      <Card sx={{ mb: 2, bgcolor: 'warning.main', color: 'warning.contrastText' }}>
        <CardContent sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center' }}>
            <AssessmentIcon sx={{ mr: 1 }} />
            5-Dimensional Assessment
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9, mt: 1 }}>
            Comprehensive code quality evaluation
          </Typography>
        </CardContent>
      </Card>

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
          Overall Score: {assessmentData.overallScore}%
        </Typography>
        <LinearProgress
          variant="determinate"
          value={assessmentData.overallScore}
          sx={{
            height: 8,
            borderRadius: 4,
            '& .MuiLinearProgress-bar': {
              bgcolor: 'success.main',
            },
          }}
        />
      </Box>

      {assessmentData.dimensions.map((dimension) => (
        <Box key={dimension.name} sx={{ mb: 1.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {dimension.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {dimension.score}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={dimension.score}
            sx={{
              height: 6,
              borderRadius: 3,
              '& .MuiLinearProgress-bar': {
                bgcolor: dimension.color,
              },
            }}
          />
        </Box>
      ))}
    </Box>
  )
}