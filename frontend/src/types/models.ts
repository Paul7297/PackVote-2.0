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
    vote_percentage?: number
  }[]
  winner_trip_destination_id?: string | null
  is_tie?: boolean
  tie_trip_destination_ids?: string[]
  participation_count?: number
  total_eligible_members?: number
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


// ── ML Recommendations ───────────────────────────────────────────────────────

export interface TransportOptionSummary {
  mode: 'flight' | 'train' | 'car'
  label: string
  estimated_cost_per_person: number
  details: string
}

export interface DestinationSummary {
  verdict: string
  verdict_tone: 'success' | 'warning' | 'info'
  benefits: string[]
  cautions: string[]
  estimated_budget_per_person: number | null
  budget_status: 'within_budget' | 'stretch' | 'exceeds' | null
  origin_city?: string | null
  weather_summary: string | null
  transport_options: TransportOptionSummary[]
}

export interface RecommendationItem {
  destination_id: string
  name: string
  compatibility_score: number | null
  reasons: string[]
  metadata_status: 'complete' | 'partial' | 'insufficient'
  missing_attributes: string[]
  summary?: DestinationSummary | null
}

// ── Weather ──────────────────────────────────────────────────────────────────

export interface WeatherDay {
  date: string
  data_type: 'forecast' | 'historical_reanalysis'
  source: string
  weather_code: number | null
  description: string
  temperature_max_c: number | null
  temperature_min_c: number | null
  precipitation_mm: number | null
  maximum_wind_speed_kmh: number | null
}

export interface WeatherResponse {
  destination_id: string
  destination_name: string
  source: string[]
  attribution: string
  timezone: string
  trip_dates_set: boolean
  weather_data_available: boolean
  forecast_available: boolean
  historical_data_available: boolean
  covers_full_trip: boolean
  missing_weather_dates: string[]
  days: WeatherDay[]
  message: string
}

// ── Cost Estimates ────────────────────────────────────────────────────────────

export interface HotelCostComponent {
  per_room_per_night: number
  rooms: number
  nights: number
  total: number
}

export interface FoodCostComponent {
  per_person_per_day: number
  total: number
}

export interface SimpleCostComponent {
  per_person: number
  total: number
}

export interface ActivityCostComponent {
  per_person: number
  activity_count: number
  total: number
}

export interface FlightCostComponent {
  per_person_round_trip: number
  total: number
}

export interface RoadTransitDetail {
  one_way_km: number
  car: {
    petrol_price_per_litre: number
    litres_needed: number
    fuel_cost: number
    toll_charges: number
    per_person: number
  }
}

export interface CostEstimate {
  currency: string
  member_count: number
  trip_nights: number
  destination_name: string
  cost_tier_used: string
  estimation_method: string
  assumptions: string[]
  components: {
    hotel: HotelCostComponent
    food: FoodCostComponent
    local_transport: SimpleCostComponent
    activities: ActivityCostComponent
    flights: FlightCostComponent
    train?: SimpleCostComponent
    car_road?: { fuel_cost: number; toll_charges: number; per_person: number; total: number }
  }
  transport_options?: TransportOptionSummary[]
  transit_details?: RoadTransitDetail
  origin_city?: string | null
  alternatives?: {
    total_with_train_per_person: number
    total_with_car_per_person: number
  }
  total_group_cost: number
  per_person_cost: number
  data_sources: string[]
  missing_data: string[]
}

// ── AI Assistant ──────────────────────────────────────────────────────────────

export interface AiResponse {
  type?: string
  destination?: string
  destinations?: string[]
  content: string | null
  error?: string | null
  evidence_used?: string[]
}
