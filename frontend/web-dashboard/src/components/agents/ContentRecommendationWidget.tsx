'use client'

import React from 'react'
import { Box, Typography, Card, CardContent, Button, Chip, Grid, LinearProgress } from '@mui/material'
import { Psychology as PsychologyIcon, School as SchoolIcon, Route as RouteIcon, Star as StarIcon } from '@mui/icons-material'

export function ContentRecommendationWidget({ preview = false }: { preview?: boolean }) {
  const recommendations = [
    {
      title: 'Advanced Graph Algorithms',
      type: 'course',
      difficulty: 'Medium',
      estimatedTime: '45 min',
      rating: 4.8,
      tags: ['Algorithms', 'Graph Theory'],
    },
    {
      title: 'Jaseci byLLM Integration',
      type: 'tutorial',
      difficulty: 'Hard',
      estimatedTime: '30 min',
      rating: 4.9,
      tags: ['AI', 'byLLM'],
    },
    {
      title: 'OSP Best Practices',
      type: 'article',
      difficulty: 'Easy',
      estimatedTime: '15 min',
      rating: 4.7,
      tags: ['OSP', 'Best Practices'],
    },
  ]

  const learningPath = {
    name: 'Jaseci Mastery Path',
    progress: 65,
    nextMilestone: 'Graph Traversals',
    estimatedCompletion: '2 weeks',
  }

  return (
    <Box>
      <Card sx={{ mb: 2, bgcolor: 'info.main', color: 'info.contrastText' }}>
        <CardContent sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center' }}>
            <PsychologyIcon sx={{ mr: 1 }} />
            Personalized Recommendations
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9, mt: 1 }}>
            AI-powered content suggestions
          </Typography>
        </CardContent>
      </Card>

      {/* Learning Path */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, display: 'flex', alignItems: 'center' }}>
          <RouteIcon sx={{ mr: 0.5, fontSize: 16 }} />
          {learningPath.name}
        </Typography>
        <Box sx={{ mb: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2">Progress to next milestone</Typography>
            <Typography variant="body2">{learningPath.progress}%</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={learningPath.progress}
            sx={{ height: 6, borderRadius: 3 }}
          />
        </Box>
        <Typography variant="caption" color="text.secondary">
          Next: {learningPath.nextMilestone} • ETA: {learningPath.estimatedCompletion}
        </Typography>
      </Box>

      {/* Recommendations */}
      {recommendations.map((rec, index) => (
        <Card key={index} sx={{ mb: 1, p: 1.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
                {rec.title}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                <Chip label={rec.type} size="small" variant="outlined" />
                <Chip label={rec.difficulty} size="small" color="warning" />
              </Box>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="caption" color="text.secondary">
                {rec.estimatedTime}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', mt: 0.5 }}>
                <StarIcon sx={{ fontSize: 12, color: 'warning.main', mr: 0.5 }} />
                <Typography variant="caption">{rec.rating}</Typography>
              </Box>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 0.5, mb: 1 }}>
            {rec.tags.map((tag) => (
              <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
            ))}
          </Box>
          <Button size="small" variant="contained" fullWidth>
            Start Learning
          </Button>
        </Card>
      ))}
    </Box>
  )
}