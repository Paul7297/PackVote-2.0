import { apiRequest } from './client'
// import type { Trip, TripCreate, TripMember } from '../types/models'
import type { Trip, TripCreate, TripMember, TripStatus } from '../types/models'

export function listTrips(): Promise<Trip[]> {
  return apiRequest<Trip[]>('/trips')
}

export function listInvitations(): Promise<Trip[]> {
  return apiRequest<Trip[]>('/trips/invitations')
}

export function getTrip(tripId: string): Promise<Trip> {
  return apiRequest<Trip>(`/trips/${encodeURIComponent(tripId)}`)
}

export function updateTripStatus(tripId: string, status: TripStatus): Promise<Trip> {
  return apiRequest<Trip>(`/trips/${encodeURIComponent(tripId)}`, {
    method: 'PUT',
    body: JSON.stringify({ status }),
  })
}

export function createTrip(data: TripCreate): Promise<Trip> {
  return apiRequest<Trip>('/trips', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function listTripMembers(tripId: string): Promise<TripMember[]> {
  return apiRequest<TripMember[]>(
    `/trips/${encodeURIComponent(tripId)}/members`,
  )
}

export function inviteMember(tripId: string, email: string): Promise<TripMember> {
  return apiRequest<TripMember>(
    `/trips/${encodeURIComponent(tripId)}/invite`,
    { method: 'POST', body: JSON.stringify({ email }) },
  )
}

export function respondToInvitation(
  tripId: string,
  accept: boolean,
): Promise<TripMember> {
  return apiRequest<TripMember>(
    `/trips/${encodeURIComponent(tripId)}/respond`,
    { method: 'POST', body: JSON.stringify({ accept }) },
  )
}


export function removeTripMember(
  tripId: string,
  userId: string,
): Promise<TripMember> {
  return apiRequest<TripMember>(
    `/trips/${encodeURIComponent(tripId)}/members/${encodeURIComponent(userId)}`,
    { method: 'DELETE' },
  )
}


export function deleteTrip(tripId: string): Promise<void> {
  return apiRequest<void>(
    `/trips/${encodeURIComponent(tripId)}`,
    { method: 'DELETE' },
  )
}


export function archiveTrip(tripId: string): Promise<Trip> {
  return apiRequest<Trip>(
    `/trips/${encodeURIComponent(tripId)}/archive`,
    { method: 'POST' },
  )
}

export function listTripHistory(): Promise<Trip[]> {
  return apiRequest<Trip[]>('/trips/history')
}

export function restoreTrip(tripId: string): Promise<Trip> {
  return apiRequest<Trip>(
    `/trips/${encodeURIComponent(tripId)}/restore`,
    { method: 'POST' },
  )
}
