import { createContext } from 'react'
import type { User, UserRegister } from '../types/models'

export interface AuthContextValue {
  user: User | null
  isInitializing: boolean
  sessionNotice: string | null
  login: (email: string, password: string) => Promise<void>
  register: (data: UserRegister) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
