'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { io, Socket } from 'socket.io-client'
import { useAuth } from './AuthContext'
import { WebSocketMessage } from '@/types/websocket'

interface WebSocketContextType {
  socket: Socket | null
  isConnected: boolean
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'reconnecting'
  lastMessage: WebSocketMessage | null
  sendMessage: (message: WebSocketMessage) => void
  joinRoom: (room: string) => void
  leaveRoom: (room: string) => void
  subscribeToAgent: (agentType: string) => void
  unsubscribeFromAgent: (agentType: string) => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'reconnecting'>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const { user, isAuthenticated } = useAuth()

  useEffect(() => {
    if (!isAuthenticated || !user) {
      // Disconnect if not authenticated
      if (socket) {
        socket.disconnect()
        setSocket(null)
        setIsConnected(false)
        setConnectionStatus('disconnected')
      }
      return
    }

    // Initialize WebSocket connection
    const initWebSocket = async () => {
      try {
        setConnectionStatus('connecting')
        
        const token = localStorage.getItem('auth_token')
        if (!token) {
          throw new Error('No auth token available')
        }

        // Create socket connection
        const socketInstance = io(process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8001', {
          auth: {
            token,
            userId: user.id,
          },
          transports: ['websocket', 'polling'],
          upgrade: true,
          rememberUpgrade: true,
        })

        // Connection event handlers
        socketInstance.on('connect', () => {
          console.log('WebSocket connected')
          setIsConnected(true)
          setConnectionStatus('connected')
        })

        socketInstance.on('disconnect', (reason) => {
          console.log('WebSocket disconnected:', reason)
          setIsConnected(false)
          setConnectionStatus(reason === 'io client disconnect' ? 'disconnected' : 'reconnecting')
        })

        socketInstance.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error)
          setIsConnected(false)
          setConnectionStatus('disconnected')
        })

        socketInstance.on('reconnect', (attemptNumber) => {
          console.log('WebSocket reconnected after', attemptNumber, 'attempts')
          setIsConnected(true)
          setConnectionStatus('connected')
        })

        socketInstance.on('reconnect_error', (error) => {
          console.error('WebSocket reconnection error:', error)
          setConnectionStatus('reconnecting')
        })

        // Message handlers
        socketInstance.on('message', (data: WebSocketMessage) => {
          console.log('Received WebSocket message:', data)
          setLastMessage(data)
          
          // Handle different message types
          handleMessage(data)
        })

        socketInstance.on('agent_update', (data) => {
          console.log('Agent update received:', data)
          // Handle agent-specific updates
        })

        socketInstance.on('progress_update', (data) => {
          console.log('Progress update received:', data)
          // Handle progress updates
        })

        socketInstance.on('quiz_result', (data) => {
          console.log('Quiz result received:', data)
          // Handle quiz results
        })

        socketInstance.on('code_analysis', (data) => {
          console.log('Code analysis received:', data)
          // Handle code analysis results
        })

        socketInstance.on('quality_assessment', (data) => {
          console.log('Quality assessment received:', data)
          // Handle quality assessment results
        })

        socketInstance.on('recommendation_update', (data) => {
          console.log('Recommendation update received:', data)
          // Handle recommendation updates
        })

        socketInstance.on('analytics_data', (data) => {
          console.log('Analytics data received:', data)
          // Handle analytics data
        })

        // System events
        socketInstance.on('system_notification', (data) => {
          console.log('System notification:', data)
          // Handle system notifications
        })

        setSocket(socketInstance)
      } catch (error) {
        console.error('Failed to initialize WebSocket:', error)
        setConnectionStatus('disconnected')
      }
    }

    initWebSocket()

    // Cleanup on unmount or dependency change
    return () => {
      if (socket) {
        socket.disconnect()
      }
    }
  }, [isAuthenticated, user])

  const handleMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'agent_response':
        // Handle agent responses
        break
      case 'error':
        console.error('WebSocket error message:', message.payload)
        break
      case 'status_update':
        // Handle status updates
        break
      default:
        console.log('Unhandled message type:', message.type)
    }
  }

  const sendMessage = (message: WebSocketMessage) => {
    if (!socket || !isConnected) {
      console.warn('WebSocket not connected, cannot send message')
      return
    }

    socket.emit('message', {
      ...message,
      timestamp: Date.now(),
      userId: user?.id,
    })
  }

  const joinRoom = (room: string) => {
    if (!socket || !isConnected) {
      console.warn('WebSocket not connected, cannot join room')
      return
    }

    socket.emit('join_room', { room, userId: user?.id })
    console.log(`Joined room: ${room}`)
  }

  const leaveRoom = (room: string) => {
    if (!socket || !isConnected) {
      console.warn('WebSocket not connected, cannot leave room')
      return
    }

    socket.emit('leave_room', { room, userId: user?.id })
    console.log(`Left room: ${room}`)
  }

  const subscribeToAgent = (agentType: string) => {
    if (!socket || !isConnected) {
      console.warn('WebSocket not connected, cannot subscribe to agent')
      return
    }

    socket.emit('subscribe_agent', { agentType, userId: user?.id })
    console.log(`Subscribed to agent: ${agentType}`)
  }

  const unsubscribeFromAgent = (agentType: string) => {
    if (!socket || !isConnected) {
      console.warn('WebSocket not connected, cannot unsubscribe from agent')
      return
    }

    socket.emit('unsubscribe_agent', { agentType, userId: user?.id })
    console.log(`Unsubscribed from agent: ${agentType}`)
  }

  const value: WebSocketContextType = {
    socket,
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    joinRoom,
    leaveRoom,
    subscribeToAgent,
    unsubscribeFromAgent,
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocket(): WebSocketContextType {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}