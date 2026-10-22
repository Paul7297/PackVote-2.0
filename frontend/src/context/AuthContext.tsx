import {
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import { getCurrentUser, loginUser, registerUser } from '../api/auth'
import {
  clearSessionTokens,
  hasRefreshToken,
  restoreSessionTokens,
  setSessionTokens,
} from '../api/client'
import { AuthContext } from './contextValue'
import type { User, UserRegister } from '../types/models'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isInitializing, setIsInitializing] = useState(
    hasRefreshToken,
  )
  const [sessionNotice, setSessionNotice] = useState<string | null>(null)

  const logout = useCallback(() => {
    clearSessionTokens()
    setUser(null)
    setSessionNotice(null)
  }, [])

  const handleSessionExpired = useCallback(() => {
    clearSessionTokens()
    setUser(null)
    setSessionNotice('Your session expired. Please sign in again.')
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await loginUser({ email, password })
    setSessionTokens(tokens)

    try {
      setUser(await getCurrentUser())
      setSessionNotice(null)
    } catch (error) {
      clearSessionTokens()
      throw error
    }
  }, [])

  const register = useCallback(async (data: UserRegister) => {
    await registerUser(data)
    await login(data.email, data.password)
  }, [login])

  useEffect(() => {
    if (!hasRefreshToken()) {
      return
    }

    let active = true
    void restoreSessionTokens()
      .then(() => getCurrentUser())
      .then((currentUser) => {
        if (active) {
          setUser(currentUser)
        }
      })
      .catch((restoreError: unknown) => {
        if (active) {
          setSessionNotice(
            restoreError instanceof Error
              ? `${restoreError.message} Please sign in again.`
              : 'Your session could not be restored. Please sign in again.',
          )
        }
      })
      .finally(() => {
        if (active) {
          setIsInitializing(false)
        }
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    window.addEventListener('packvote:session-expired', handleSessionExpired)
    return () => window.removeEventListener('packvote:session-expired', handleSessionExpired)
  }, [handleSessionExpired])

  return (
    <AuthContext.Provider value={{ user, isInitializing, sessionNotice, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
