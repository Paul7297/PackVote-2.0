import { apiRequest, ApiError } from './client'
import type {
  PreferenceCompletionStatus,
  TripPreference,
  TripPreferenceInput,
} from '../types/models'

const preferencePath = (tripId: string) =>
  `/trips/${encodeURIComponent(tripId)}/preferences`

export async function getMyPreference(
  tripId: string,
): Promise<TripPreference | null> {
  try {
    return await apiRequest<TripPreference>(`${preferencePath(tripId)}/me`)
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null
    }
    throw error
  }
}

export function getPreferenceStatus(
  tripId: string,
): Promise<PreferenceCompletionStatus> {
  return apiRequest<PreferenceCompletionStatus>(
    `${preferencePath(tripId)}/status`,
  )
}

export function createPreference(
  tripId: string,
  data: TripPreferenceInput,
): Promise<TripPreference> {
  return apiRequest<TripPreference>(preferencePath(tripId), {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updatePreference(
  tripId: string,
  data: Partial<TripPreferenceInput>,
): Promise<TripPreference> {
  return apiRequest<TripPreference>(preferencePath(tripId), {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}
