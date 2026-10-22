import { apiRequest, parseTokenResponse } from './client'
import type { TokenResponse, User, UserLogin, UserRegister } from '../types/models'

export function registerUser(data: UserRegister): Promise<User> {
  return apiRequest<User>(
    '/auth/register',
    { method: 'POST', body: JSON.stringify(data) },
    { auth: false },
  )
}

export function loginUser(data: UserLogin): Promise<TokenResponse> {
  return apiRequest<unknown>(
    '/auth/login',
    { method: 'POST', body: JSON.stringify(data) },
    { auth: false },
  ).then((payload) => parseTokenResponse(payload, 200))
}

export function getCurrentUser(): Promise<User> {
  return apiRequest<User>('/auth/me')
}
