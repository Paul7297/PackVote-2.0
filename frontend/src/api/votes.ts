import { apiRequest, ApiError } from './client'
import type { TripVote, TripVoteResults } from '../types/models'

function votesPath(tripId: string): string {
  return `/trips/${encodeURIComponent(tripId)}/votes`
}

export async function getMyVote(tripId: string): Promise<TripVote | null> {
  try {
    return await apiRequest<TripVote>(`${votesPath(tripId)}/me`)
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null
    }
    throw error
  }
}

export function submitVote(
  tripId: string,
  tripDestinationId: string,
): Promise<TripVote> {
  return apiRequest<TripVote>(votesPath(tripId), {
    method: 'POST',
    body: JSON.stringify({ trip_destination_id: tripDestinationId }),
  })
}

export function getVoteResults(tripId: string): Promise<TripVoteResults> {
  return apiRequest<TripVoteResults>(`${votesPath(tripId)}/results`)
}
