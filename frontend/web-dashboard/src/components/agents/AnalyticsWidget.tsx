'use client'

import React from 'react'
import { Box, Typography, Card, CardContent, Grid, LinearProgress, Chip } from '@mui/material'
import { Analytics as AnalyticsIcon, TrendingUp as TrendingUpIcon, Prediction as PredictionIcon, Assessment as AssessmentIcon } from '@mui/icons-material'

export function AnalyticsWidget({ preview = false }: { preview?: boolean }) {
  const analyticsData = {
    predictions: [
      { type: 'Success Probability', value: 87, confidence: 92, timeframe: 'Next 30 days' },
      { type: 'Difficulty Adjustment', value: 75, confidence: 85, timeframe: 'Optimal setting' },
      { type: 'Completion Rate', value: 94, confidence: 88, timeframe: 'This week' },
    ],
    trends: [
      { metric: 'Learning Velocity', direction: 'up', change: 15, strength: 0.89 },
      { metric: 'Engagement Score', direction: 'up', change: 8, strength: 0.76 },
      { metric: 'Retention Rate', direction: 'stable', change: 0, strength: 0.95 },
    ],
    systemMetrics: {
      uptime: 99.9,
      responseTime: 245,
      errorRate: 0.02,
    },
  }

  return (
    <Box>
      <Card sx={{ mb: 2, bgcolor: 'error.main', color: 'error.contrastText' }}>
        <CardContent sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center' }}>
            <AnalyticsIcon sx={{ mr: 1 }} />
            Predictive Analytics
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9, mt: 1 }}>
            ML-powered insights and forecasts
          </Typography>
        </CardContent>
      </Card>

      {/* Predictions */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, display: 'flex', alignItems: 'center' }}>
          <PredictionIcon sx={{ mr: 0.5, fontSize: 16 }} />
          Predictions & Forecasts
        </Typography>
        
        {analyticsData.predictions.map((prediction, index) => (
          <Box key={index} sx={{ mb: 2, p: 1.5, bgcolor: 'background.default', borderRadius: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {prediction.type}
              </Typography>
              <Chip
                label={`${prediction.value}%`}
                size="small"
                color={prediction.value >= 80 ? 'success' : prediction.value >= 60 ? 'warning' : 'error'}
              />
            </Box>
            
            <Box sx={{ mb: 1 }}>
              <LinearProgress
                variant="determinate"
                value={prediction.value}
                sx={{ height: 6, borderRadius: 3, mb: 0.5 }}
              />
              <Typography variant="caption" color="text.secondary">
                Confidence: {prediction.confidence}% • {prediction.timeframe}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>

      {/* Trends */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, display: 'flex', alignItems: 'center' }}>
          <TrendingUpIcon sx={{ mr: 0.5, fontSize: 16 }} />
          Learning Trends
        </Typography>
        
        {analyticsData.trends.map((trend, index) => (
          <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2">{trend.metric}</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color={trend.direction === 'up' ? 'success.main' : trend.direction === 'down' ? 'error.main' : 'text.secondary'}>
                {trend.change > 0 ? '+' : ''}{trend.change}%
              </Typography>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: trend.direction === 'up' ? 'success.main' : trend.direction === 'down' ? 'error.main' : 'grey.500',
                }}
              />
            </Box>
          </Box>
        ))}
      </Box>

      {/* System Health */}
      <Box>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, display: 'flex', alignItems: 'center' }}>
          <AssessmentIcon sx={{ mr: 0.5, fontSize: 16 }} />
          System Health
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={4}>
            <Card sx={{ textAlign: 'center', p: 1 }}>
              <Typography variant="h6" color="success.main">
                {analyticsData.systemMetrics.uptime}%
              </Typography>
              <Typography variant="caption">Uptime</Typography>
            </Card>
          </Grid>
          <Grid item xs={4}>
            <Card sx={{ textAlign: 'center', p: 1 }}>
              <Typography variant="h6" color="info.main">
                {analyticsData.systemMetrics.responseTime}ms
              </Typography>
              <Typography variant="caption">Response</Typography>
            </Card>
          </Grid>
          <Grid item xs={4}>
            <Card sx={{ textAlign: 'center', p: 1 }}>
              <Typography variant="h6" color="warning.main">
                {analyticsData.systemMetrics.errorRate}%
              </Typography>
              <Typography variant="caption">Error Rate</Typography>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}