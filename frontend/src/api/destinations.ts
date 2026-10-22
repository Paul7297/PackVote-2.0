import { apiRequest } from './client'
import type {
  Destination,
  DestinationSearchResult,
  TripDestination,
} from '../types/models'

export function searchDestinations(
  query: string,
  limit = 8,
): Promise<DestinationSearchResult[]> {
  const params = new URLSearchParams({ query, limit: String(limit) })
  return apiRequest<DestinationSearchResult[]>(
    `/destinations/search?${params.toString()}`,
  )
}

export function listDestinations(): Promise<Destination[]> {
  return apiRequest<Destination[]>('/destinations')
}

export function confirmDestination(
  tripId: string,
  externalPlaceId: string,
): Promise<TripDestination> {
  return apiRequest<TripDestination>(
    `/trips/${encodeURIComponent(tripId)}/destinations/confirm`,
    {
      method: 'POST',
      body: JSON.stringify({ external_place_id: externalPlaceId }),
    },
  )
}

export function listTripDestinations(
  tripId: string,
): Promise<TripDestination[]> {
  return apiRequest<TripDestination[]>(
    `/trips/${encodeURIComponent(tripId)}/destinations`,
  )
}

export function addTripDestinationCandidate(
  tripId: string,
  destinationId: string,
): Promise<unknown> {
  return apiRequest<unknown>(
    `/trips/${encodeURIComponent(tripId)}/destinations`,
    {
      method: 'POST',
      body: JSON.stringify({ destination_id: destinationId }),
    },
  )
}

export function finalizeTripDestination(
  tripId: string,
  tripDestinationId: string,
): Promise<unknown> {
  return apiRequest<unknown>(
    `/trips/${encodeURIComponent(tripId)}/destinations/${encodeURIComponent(tripDestinationId)}/finalize`,
    { method: 'POST' },
  )
}

export function rejectTripDestination(
  tripId: string,
  tripDestinationId: string,
): Promise<unknown> {
  return apiRequest<unknown>(
    `/trips/${encodeURIComponent(tripId)}/destinations/${encodeURIComponent(tripDestinationId)}/reject`,
    { method: 'POST' },
  )
}
