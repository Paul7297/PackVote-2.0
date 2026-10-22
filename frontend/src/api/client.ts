import type { TokenResponse } from '../types/models'

const REFRESH_TOKEN_KEY = 'packvote.refresh_token'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '') ?? ''

let accessToken: string | null = null
let refreshInFlight: Promise<void> | null = null

export class ApiError extends Error {
  public readonly status: number

  constructor(
    message: string,
    status: number,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function parseTokenResponse(payload: unknown, status: number): TokenResponse {
  if (
    typeof payload === 'object'
    && payload !== null
    && 'access_token' in payload
    && typeof payload.access_token === 'string'
    && 'refresh_token' in payload
    && typeof payload.refresh_token === 'string'
    && 'token_type' in payload
    && typeof payload.token_type === 'string'
  ) {
    return payload as TokenResponse
  }

  throw new ApiError('The authentication response did not contain valid tokens.', status)
}

export function hasRefreshToken(): boolean {
  return Boolean(window.sessionStorage.getItem(REFRESH_TOKEN_KEY))
}

export function setSessionTokens(tokens: TokenResponse): void {
  accessToken = tokens.access_token
  window.sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
}

export function clearSessionTokens(): void {
  accessToken = null
  window.sessionStorage.removeItem(REFRESH_TOKEN_KEY)
}

function apiUrl(path: string): string {
  if (!API_BASE_URL) {
    throw new Error(
      'Set VITE_API_BASE_URL in frontend/.env.local before connecting to PackVote API.',
    )
  }

  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

async function readResponse(response: Response): Promise<unknown> {
  const text = await response.text()

  if (!text) {
    return undefined
  }

  try {
    return JSON.parse(text) as unknown
  } catch {
    throw new ApiError('The server returned an invalid response.', response.status)
  }
}

function responseErrorMessage(payload: unknown, status: number): string {
  if (
    typeof payload === 'object'
    && payload !== null
    && 'detail' in payload
  ) {
    const detail = payload.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail)) {
      const messages = detail.flatMap((item) => {
        if (
          typeof item === 'object'
          && item !== null
          && 'msg' in item
          && typeof item.msg === 'string'
        ) {
          return [item.msg]
        }
        return []
      })
      if (messages.length > 0) {
        return messages.join(' ')
      }
    }
    if (detail !== undefined) {
      return JSON.stringify(detail)
    }
  }

  return `Request failed (${status}).`
}

async function refreshStoredSession(): Promise<void> {
  const refreshToken = window.sessionStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refreshToken) {
    throw new ApiError('Your session has expired. Please sign in again.', 401)
  }

  const expireSession = () => {
    clearSessionTokens()
    window.dispatchEvent(new Event('packvote:session-expired'))
  }

  const response = await fetch(apiUrl('/auth/refresh'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  let payload: unknown
  try {
    payload = await readResponse(response)
  } catch (error) {
    if (response.status === 401) {
      expireSession()
    }
    throw error
  }

  if (!response.ok) {
    if (response.status === 401) {
      expireSession()
    }
    throw new ApiError(responseErrorMessage(payload, response.status), response.status)
  }

  try {
    setSessionTokens(parseTokenResponse(payload, response.status))
  } catch (error) {
    expireSession()
    throw error
  }
}

export function restoreSessionTokens(): Promise<void> {
  return refreshOnce()
}

async function refreshOnce(): Promise<void> {
  if (!refreshInFlight) {
    refreshInFlight = refreshStoredSession().finally(() => {
      refreshInFlight = null
    })
  }

  return refreshInFlight
}

export interface RequestOptions {
  auth?: boolean
  retryOnUnauthorized?: boolean
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
): Promise<T> {
  const useAuth = options.auth ?? true
  const retryOnUnauthorized = options.retryOnUnauthorized ?? true
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')

  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (useAuth && accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(apiUrl(path), { ...init, headers })
  if (
    response.status === 401
    && useAuth
    && retryOnUnauthorized
    && window.sessionStorage.getItem(REFRESH_TOKEN_KEY)
  ) {
    await refreshOnce()
    return apiRequest<T>(path, init, { auth: useAuth, retryOnUnauthorized: false })
  }

  const payload = await readResponse(response)
  if (!response.ok) {
    throw new ApiError(responseErrorMessage(payload, response.status), response.status)
  }

  return payload as T
}
