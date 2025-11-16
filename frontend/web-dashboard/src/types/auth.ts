// Auth Types
export interface User {
  id: string
  email: string
  username: string
  first_name?: string
  last_name?: string
  avatar?: string
  role: 'student' | 'instructor' | 'admin'
  is_active: boolean
  created_at: string
  updated_at: string
  profile?: UserProfile
  preferences?: UserPreferences
}

export interface UserProfile {
  bio?: string
  learning_goals?: string[]
  experience_level: 'beginner' | 'intermediate' | 'advanced'
  interests?: string[]
  languages?: string[]
  timezone?: string
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: string
  notifications: {
    email: boolean
    push: boolean
    in_app: boolean
  }
  privacy: {
    show_profile: boolean
    show_progress: boolean
    share_analytics: boolean
  }
}

export interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
  token: string | null
}

export interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string; user?: User }>
  logout: () => void
  register: (userData: {
    email: string
    password: string
    username: string
    first_name?: string
    last_name?: string
  }) => Promise<{ success: boolean; error?: string; user?: User }>
  updateProfile: (profileData: Partial<User>) => Promise<{ success: boolean; error?: string; user?: User }>
  refreshToken: () => Promise<{ success: boolean; error?: string; token?: string }>
}