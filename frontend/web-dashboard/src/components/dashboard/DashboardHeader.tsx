'use client'

import React from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Avatar,
  Menu,
  MenuItem,
  Box,
  IconButton,
  Badge,
  Tooltip,
  Chip,
} from '@mui/material'
import {
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  AccountCircle as AccountCircleIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Dashboard as DashboardIcon,
} from '@mui/icons-material'
import { useAuth } from '@/contexts/AuthContext'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export function DashboardHeader() {
  const { user, logout } = useAuth()
  const { isConnected, connectionStatus } = useWebSocket()
  const router = useRouter()
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null)
  const [notificationAnchor, setNotificationAnchor] = React.useState<null | HTMLElement>(null)

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleProfileMenuClose = () => {
    setAnchorEl(null)
  }

  const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget)
  }

  const handleNotificationMenuClose = () => {
    setNotificationAnchor(null)
  }

  const handleLogout = () => {
    logout()
    router.push('/auth/login')
  }

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'success'
      case 'connecting':
      case 'reconnecting':
        return 'warning'
      case 'disconnected':
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <AppBar 
      position="sticky" 
      elevation={1}
      sx={{ 
        bgcolor: 'background.paper',
        color: 'text.primary',
        borderBottom: 1,
        borderColor: 'divider',
      }}
    >
      <Toolbar>
        {/* Logo and Title */}
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Box
            sx={{
              p: 1,
              borderRadius: 1,
              bgcolor: 'primary.main',
              color: 'primary.contrastText',
              mr: 2,
            }}
          >
            <DashboardIcon fontSize="medium" />
          </Box>
          <Typography
            variant="h6"
            component="div"
            sx={{ 
              fontWeight: 600,
              background: 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Jaseci Learning Companion
          </Typography>
        </Box>

        {/* Connection Status */}
        <Tooltip title={`WebSocket Status: ${connectionStatus}`}>
          <Chip
            size="small"
            label={connectionStatus}
            color={getConnectionStatusColor() as any}
            icon={<Box sx={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              bgcolor: isConnected ? 'success.main' : 'error.main' 
            }} />}
            sx={{ mr: 2 }}
          />
        </Tooltip>

        {/* Navigation */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mr: 2 }}>
          <Button
            component={Link}
            href="/dashboard"
            startIcon={<DashboardIcon />}
            sx={{ 
              color: 'text.primary',
              '&:hover': { bgcolor: 'action.hover' }
            }}
          >
            Dashboard
          </Button>
          <Button
            component={Link}
            href="/code-editor"
            sx={{ 
              color: 'text.primary',
              '&:hover': { bgcolor: 'action.hover' }
            }}
          >
            Code Editor
          </Button>
          <Button
            component={Link}
            href="/quiz"
            sx={{ 
              color: 'text.primary',
              '&:hover': { bgcolor: 'action.hover' }
            }}
          >
            Quiz Generator
          </Button>
        </Box>

        {/* Notifications */}
        <Tooltip title="Notifications">
          <IconButton
            size="large"
            color="inherit"
            onClick={handleNotificationMenuOpen}
            sx={{ mr: 1 }}
          >
            <Badge badgeContent={0} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
        </Tooltip>

        {/* Settings */}
        <Tooltip title="Settings">
          <IconButton
            size="large"
            color="inherit"
            component={Link}
            href="/settings"
            sx={{ mr: 1 }}
          >
            <SettingsIcon />
          </IconButton>
        </Tooltip>

        {/* Profile */}
        <Tooltip title="Profile">
          <IconButton
            size="large"
            onClick={handleProfileMenuOpen}
            color="inherit"
          >
            {user?.avatar ? (
              <Avatar
                src={user.avatar}
                alt={user.username}
                sx={{ width: 32, height: 32 }}
              />
            ) : (
              <AccountCircleIcon />
            )}
          </IconButton>
        </Tooltip>

        {/* Profile Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleProfileMenuClose}
          onClick={handleProfileMenuClose}
          PaperProps={{
            elevation: 3,
            sx: {
              overflow: 'visible',
              filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
              mt: 1.5,
              minWidth: 200,
            },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItem component={Link} href="/profile">
            <AccountCircleIcon sx={{ mr: 2 }} />
            Profile
          </MenuItem>
          <MenuItem component={Link} href="/settings">
            <SettingsIcon sx={{ mr: 2 }} />
            Settings
          </MenuItem>
          <MenuItem onClick={handleLogout}>
            <Box sx={{ mr: 2, color: 'error.main' }}>↩</Box>
            Logout
          </MenuItem>
        </Menu>

        {/* Notification Menu */}
        <Menu
          anchorEl={notificationAnchor}
          open={Boolean(notificationAnchor)}
          onClose={handleNotificationMenuClose}
          PaperProps={{
            elevation: 3,
            sx: {
              overflow: 'visible',
              filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
              mt: 1.5,
              minWidth: 250,
            },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItem>
            <Typography variant="body2" color="text.secondary">
              No new notifications
            </Typography>
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  )
}