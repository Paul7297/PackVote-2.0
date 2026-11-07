import { apiRequest } from './client'
import type { RecommendationItem, WeatherResponse, CostEstimate, AiResponse } from '../types/models'

// ── ML Recommendations ──────────────────────────────────────────────────────

export function getRecommendations(tripId: string, originCity = 'delhi'): Promise<RecommendationItem[]> {
  const query = new URLSearchParams({ origin_city: originCity }).toString()
  return apiRequest<RecommendationItem[]>(
    `/trips/${encodeURIComponent(tripId)}/recommendations?${query}`,
  )
}

export function promoteRecommendation(
  tripId: string,
  destinationId: string,
): Promise<unknown> {
  return apiRequest<unknown>(
    `/trips/${encodeURIComponent(tripId)}/recommendations/${encodeURIComponent(destinationId)}/promote`,
    {
      method: 'POST',
    },
  )
}

// ── Weather ─────────────────────────────────────────────────────────────────

export function getDestinationWeather(
  tripId: string,
  destinationId: string,
): Promise<WeatherResponse> {
  return apiRequest<WeatherResponse>(
    `/trips/${encodeURIComponent(tripId)}/recommendations/${encodeURIComponent(destinationId)}/weather`,
  )
}

// ── Cost Estimates ───────────────────────────────────────────────────────────

export function getCostEstimate(
  tripId: string,
  destinationId: string,
  originCity = 'delhi',
): Promise<CostEstimate> {
  const query = new URLSearchParams({ origin_city: originCity }).toString()
  return apiRequest<CostEstimate>(
    `/trips/${encodeURIComponent(tripId)}/destinations/${encodeURIComponent(destinationId)}/cost-estimate?${query}`,
  )
}

// ── AI Assistant ─────────────────────────────────────────────────────────────

export function aiExplainDestination(
  tripId: string,
  destinationId: string,
  weatherSummary?: string,
  costSummary?: string,
  originCity = 'delhi',
): Promise<AiResponse> {
  return apiRequest<AiResponse>(
    `/trips/${encodeURIComponent(tripId)}/ai/explain`,
    {
      method: 'POST',
      body: JSON.stringify({
        destination_id: destinationId,
        weather_summary: weatherSummary ?? null,
        cost_summary: costSummary ?? null,
        origin_city: originCity,
      }),
    },
  )
}

export function aiCompareDestinations(
  tripId: string,
  destinationIdA: string,
  destinationIdB: string,
  weatherSummaryA?: string,
  weatherSummaryB?: string,
  costSummaryA?: string,
  costSummaryB?: string,
  originCity = 'delhi',
): Promise<AiResponse> {
  return apiRequest<AiResponse>(
    `/trips/${encodeURIComponent(tripId)}/ai/compare`,
    {
      method: 'POST',
      body: JSON.stringify({
        destination_id: destinationIdA,
        destination_id_b: destinationIdB,
        weather_summary: weatherSummaryA ?? null,
        weather_summary_b: weatherSummaryB ?? null,
        cost_summary: costSummaryA ?? null,
        cost_summary_b: costSummaryB ?? null,
        origin_city: originCity,
      }),
    },
  )
}

export function aiTripSummary(tripId: string): Promise<AiResponse> {
  return apiRequest<AiResponse>(
    `/trips/${encodeURIComponent(tripId)}/ai/summary`,
    { method: 'POST', body: JSON.stringify({}) },
  )
}
