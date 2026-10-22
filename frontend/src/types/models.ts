export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: string
  full_name: string
  email: string
  phone_number: string | null
  profile_image: string | null
  is_verified: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserRegister {
  full_name: string
  email: string
  password: string
  phone_number?: string
}

export interface UserLogin {
  email: string
  password: string
}

export type TripStatus = 'planning' | 'voting' | 'finalized' | 'cancelled'
export type TravelerType = 'solo' | 'couple' | 'family' | 'friends'
export type MemberRole = 'organizer' | 'member'
export type MemberStatus =
  | 'invited'
  | 'joined'
  | 'declined'
  | 'left'
  | 'removed'

export interface Trip {
  id: string
  name: string
  organizer_id: string
  description: string | null
  budget_min: number | null
  budget_max: number | null
  start_date: string | null
  end_date: string | null
  status: TripStatus
  traveler_type: TravelerType | null
  created_at: string
  updated_at: string
  archived_at?: string | null
}

export interface TripCreate {
  name: string
  description?: string | null
  budget_min?: number | null
  budget_max?: number | null
  start_date?: string | null
  end_date?: string | null
  traveler_type?: TravelerType | null
}

export interface TripMember {
  id: string
  trip_id: string
  user_id: string
  role: MemberRole
  status: MemberStatus
  created_at: string
}

export interface DestinationSearchResult {
  external_place_id: string
  name: string
  country: string | null
  region: string | null
  latitude: number | null
  longitude: number | null
  display_name: string
}

export interface Destination {
  id: string
  name: string
  country?: string | null
  region?: string | null
}

export interface TripDestination {
  id: string
  trip_id: string
  destination_id: string
  added_by: string
  source: string
  status: string
  created_at: string
  updated_at: string
}

export interface TripVote {
  trip_destination_id: string
}

export interface TripVoteResults {
  trip_id: string
  total_votes: number
  results: {
    trip_destination_id: string
    vote_count: number
  }[]
}

export interface PreferenceCompletionStatus {
  submitted: number
  total: number
  complete: boolean
}

export type BudgetRange = '5k_10k' | '10k_20k' | '20k_40k' | '40k_plus'
export type ClimatePreference = 'cold' | 'moderate' | 'warm' | 'no_preference'
export type AccommodationPref = 'budget' | 'mid' | 'luxury'
export type TransportPref = 'flight' | 'train' | 'bus' | 'car'
export type FoodPref = 'veg' | 'non_veg' | 'vegan' | 'no_preference'
export type TravelPriority = 'cheapest' | 'balanced' | 'comfort' | 'experience'
export type TravelStyle =
  | 'adventure'
  | 'nature'
  | 'relaxation'
  | 'cultural'
  | 'nightlife'
  | 'food'
export type Activity =
  | 'trekking'
  | 'beach'
  | 'historical_places'
  | 'shopping'
  | 'local_food'
  | 'camping'
  | 'sightseeing'
  | 'water_sports'
  | 'wildlife'
  | 'photography'
  | 'nightlife'
  | 'spa_wellness'

export interface TripPreference {
  id: string
  trip_id: string
  user_id: string
  budget_range: BudgetRange
  travel_style: TravelStyle[]
  preferred_activities: Activity[]
  climate_preference: ClimatePreference
  accommodation_pref: AccommodationPref
  transport_pref: TransportPref
  food_pref: FoodPref
  travel_priority: TravelPriority
  notes: string | null
  created_at: string
  updated_at: string
}

export type TripPreferenceInput = Omit<
  TripPreference,
  'id' | 'trip_id' | 'user_id' | 'created_at' | 'updated_at'
>
