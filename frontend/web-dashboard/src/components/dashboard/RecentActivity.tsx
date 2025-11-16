'use client'

import React, { useEffect, useState } from 'react'
import {
  Paper,
  Typography,
  Box,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
  Skeleton,
  Button,
} from '@mui/material'
import {
  Quiz as QuizIcon,
  Code as CodeIcon,
  TrendingUp as TrendingUpIcon,
  EmojiEvents as EmojiEventsIcon,
  Psychology as PsychologyIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material'
import { formatDistanceToNow } from 'date-fns'
import { ActivityItem } from '@/types/dashboard'

export function RecentActivity() {
  const [activities, setActivities] = useState<ActivityItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Mock activities data
    const mockActivities: ActivityItem[] = [
      {
        id: '1',
        type: 'quiz_completed',
        user: {
          id: 'user1',
          username: 'Alice Smith',
          avatar: 'https://ui-avatars.com/api/?name=Alice+Smith&background=3b82f6&color=fff',
        },
        title: 'Completed Jaseci Basics Quiz',
        description: 'Scored 95% in 12 minutes',
        timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
        metadata: { score: 95, timeSpent: 720 },
      },
      {
        id: '2',
        type: 'code_submitted',
        user: {
          id: 'user2',
          username: 'Bob Johnson',
          avatar: 'https://ui-avatars.com/api/?name=Bob+Johnson&background=10b981&color=fff',
        },
        title: 'Submitted Graph Traversal Code',
        description: 'Implemented BFS algorithm in Jaseci',
        timestamp: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
        metadata: { language: 'jac', complexity: 'medium' },
      },
      {
        id: '3',
        type: 'achievement_unlocked',
        user: {
          id: 'user3',
          username: 'Carol Davis',
          avatar: 'https://ui-avatars.com/api/?name=Carol+Davis&background=f59e0b&color=fff',
        },
        title: 'Unlocked "Code Master" Achievement',
        description: 'Completed 50 coding challenges',
        timestamp: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
        metadata: { achievement: 'code_master', points: 500 },
      },
      {
        id: '4',
        type: 'progress_updated',
        user: {
          id: 'user4',
          username: 'David Wilson',
          avatar: 'https://ui-avatars.com/api/?name=David+Wilson&background=8b5cf6&color=fff',
        },
        title: 'Reached Intermediate Level',
        description: 'Advanced 20% in Jaseci mastery',
        timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
        metadata: { newLevel: 'intermediate', progress: 20 },
      },
      {
        id: '5',
        type: 'agent_interaction',
        user: {
          id: 'user5',
          username: 'Emma Brown',
          avatar: 'https://ui-avatars.com/api/?name=Emma+Brown&background=ef4444&color=fff',
        },
        title: 'Used Quiz Generator Agent',
        description: 'Generated custom quiz on graph algorithms',
        timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
        metadata: { agent: 'quiz_generator', questions: 15 },
      },
      {
        id: '6',
        type: 'quiz_completed',
        user: {
          id: 'user6',
          username: 'Frank Miller',
          avatar: 'https://ui-avatars.com/api/?name=Frank+Miller&background=06b6d4&color=fff',
        },
        title: 'Completed Advanced Jaseci Quiz',
        description: 'Scored 88% in 18 minutes',
        timestamp: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
        metadata: { score: 88, timeSpent: 1080 },
      },
    ]

    setTimeout(() => {
      setActivities(mockActivities)
      setLoading(false)
    }, 1000)
  }, [])

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'quiz_completed':
        return <QuizIcon />
      case 'code_submitted':
        return <CodeIcon />
      case 'achievement_unlocked':
        return <EmojiEventsIcon />
      case 'progress_updated':
        return <TrendingUpIcon />
      case 'agent_interaction':
        return <PsychologyIcon />
      default:
        return <TimelineIcon />
    }
  }

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'quiz_completed':
        return '#3b82f6'
      case 'code_submitted':
        return '#10b981'
      case 'achievement_unlocked':
        return '#f59e0b'
      case 'progress_updated':
        return '#8b5cf6'
      case 'agent_interaction':
        return '#06b6d4'
      default:
        return '#6b7280'
    }
  }

  const getMetadataChip = (activity: ActivityItem) => {
    const metadata = activity.metadata
    if (!metadata) return null

    if (activity.type === 'quiz_completed' && metadata.score) {
      return (
        <Chip
          label={`${metadata.score}%`}
          size="small"
          color={metadata.score >= 90 ? 'success' : metadata.score >= 70 ? 'warning' : 'error'}
          sx={{ ml: 1 }}
        />
      )
    }

    if (activity.type === 'code_submitted' && metadata.language) {
      return (
        <Chip
          label={metadata.language.toUpperCase()}
          size="small"
          variant="outlined"
          sx={{ ml: 1 }}
        />
      )
    }

    if (activity.type === 'achievement_unlocked' && metadata.points) {
      return (
        <Chip
          label={`+${metadata.points} pts`}
          size="small"
          color="success"
          sx={{ ml: 1 }}
        />
      )
    }

    if (activity.type === 'agent_interaction' && metadata.agent) {
      return (
        <Chip
          label={metadata.agent.replace('_', ' ')}
          size="small"
          variant="outlined"
          color="primary"
          sx={{ ml: 1 }}
        />
      )
    }

    return null
  }

  return (
    <Paper sx={{ p: 3, mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Recent Activity
        </Typography>
        <Button size="small" color="primary">
          View All
        </Button>
      </Box>

      {loading ? (
        <List sx={{ p: 0 }}>
          {[...Array(6)].map((_, index) => (
            <ListItem key={index} sx={{ px: 0, py: 1 }}>
              <ListItemAvatar>
                <Skeleton variant="circular" width={40} height={40} />
              </ListItemAvatar>
              <ListItemText
                primary={<Skeleton variant="text" width="60%" />}
                secondary={<Skeleton variant="text" width="40%" />}
              />
            </ListItem>
          ))}
        </List>
      ) : (
        <List sx={{ p: 0 }}>
          {activities.map((activity) => (
            <ListItem 
              key={activity.id}
              sx={{ 
                px: 0, 
                py: 1.5,
                borderBottom: 1,
                borderColor: 'divider',
                '&:last-child': {
                  borderBottom: 'none',
                },
              }}
            >
              <ListItemAvatar>
                <Avatar
                  src={activity.user.avatar}
                  sx={{
                    bgcolor: getActivityColor(activity.type) + '20',
                    color: getActivityColor(activity.type),
                  }}
                >
                  {getActivityIcon(activity.type)}
                </Avatar>
              </ListItemAvatar>
              
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {activity.title}
                    </Typography>
                    {getMetadataChip(activity)}
                  </Box>
                }
                secondary={
                  <Box sx={{ mt: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">
                      {activity.description}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      by {activity.user.username} • {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                    </Typography>
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      )}

      {!loading && activities.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <TimelineIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="body1" color="text.secondary">
            No recent activity
          </Typography>
        </Box>
      )}
    </Paper>
  )
}