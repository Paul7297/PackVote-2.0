import { useCallback, useEffect, useState } from 'react'
import {
  getRecommendations,
  getDestinationWeather,
  getCostEstimate,
  aiExplainDestination,
  aiCompareDestinations,
  promoteRecommendation,
} from '../api/intelligence'
import { Notice } from './Notice'
import type {
  RecommendationItem,
  WeatherResponse,
  CostEstimate,
  AiResponse,
} from '../types/models'

interface Props {
  tripId: string
  isOrganizer: boolean
  onCandidateAdded: () => void
  onGoToPreferences?: () => void
}

const ORIGIN_CITIES = [
  { id: 'delhi', label: 'Delhi (NCR)' },
  { id: 'mumbai', label: 'Mumbai' },
  { id: 'bengaluru', label: 'Bengaluru' },
  { id: 'kolkata', label: 'Kolkata' },
  { id: 'chennai', label: 'Chennai' },
  { id: 'hyderabad', label: 'Hyderabad' },
  { id: 'pune', label: 'Pune' },
  { id: 'ahmedabad', label: 'Ahmedabad' },
  { id: 'jaipur', label: 'Jaipur' },
]

function MatchScoreBadge({ score }: { score: number | null }) {
  if (score === null) {
    return <span className="score-badge score-badge--none">Pending Preferences</span>
  }
  const matchPct = Math.min(99, Math.max(10, Math.round(score * 2.2)))
  const level = matchPct >= 70 ? 'high' : matchPct >= 45 ? 'mid' : 'low'
  return (
    <span className={`score-badge score-badge--${level}`}>
      🎯 {matchPct}% Match
    </span>
  )
}

function WeatherMiniCard({ weather }: { weather: WeatherResponse }) {
  if (!weather.weather_data_available || weather.days.length === 0) {
    return <p className="weather-no-data">{weather.message}</p>
  }

  const avgMax =
    weather.days.reduce((s, d) => s + (d.temperature_max_c ?? 0), 0) / weather.days.length
  const avgMin =
    weather.days.reduce((s, d) => s + (d.temperature_min_c ?? 0), 0) / weather.days.length
  const totalRain = weather.days.reduce((s, d) => s + (d.precipitation_mm ?? 0), 0)
  const condition = weather.days[0]?.description ?? 'Clear Sky'

  return (
    <div className="weather-summary">
      <div className="weather-stat-row">
        <div className="weather-stat">
          <span className="weather-stat-label">Weather</span>
          <span className="weather-stat-value">⛅ {condition}</span>
        </div>
        <div className="weather-stat">
          <span className="weather-stat-label">Temperature</span>
          <span className="weather-stat-value">
            {avgMin.toFixed(0)}°–{avgMax.toFixed(0)}°C
          </span>
        </div>
        <div className="weather-stat">
          <span className="weather-stat-label">Rainfall</span>
          <span className="weather-stat-value">{totalRain.toFixed(0)} mm</span>
        </div>
      </div>
      <p className="weather-note">
        {weather.forecast_available ? '📅 Live Open-Meteo forecast' : '📚 Historical climate reanalysis'}
      </p>
    </div>
  )
}

function CostDetailedCard({ cost }: { cost: CostEstimate }) {
  return (
    <div className="cost-summary">
      <div className="cost-stat-row">
        <div className="cost-stat">
          <span className="cost-stat-label">Estimated Total (Flight)</span>
          <span className="cost-stat-value">₹{cost.per_person_cost.toLocaleString('en-IN')}/person</span>
        </div>
        {cost.alternatives && (
          <>
            <div className="cost-stat">
              <span className="cost-stat-label">With Train (3AC)</span>
              <span className="cost-stat-value">₹{Math.round(cost.alternatives.total_with_train_per_person).toLocaleString('en-IN')}/person</span>
            </div>
            <div className="cost-stat">
              <span className="cost-stat-label">With Car & Petrol</span>
              <span className="cost-stat-value">₹{Math.round(cost.alternatives.total_with_car_per_person).toLocaleString('en-IN')}/person</span>
            </div>
          </>
        )}
      </div>

      <div className="cost-breakdown-chips">
        <span>🏨 Hotel: ₹{cost.components.hotel.total.toLocaleString('en-IN')} ({cost.components.hotel.rooms} rooms)</span>
        <span>🍽️ Food: ₹{cost.components.food.total.toLocaleString('en-IN')}</span>
        <span>🚕 Local: ₹{cost.components.local_transport.total.toLocaleString('en-IN')}</span>
        <span>🎯 Activities: ₹{cost.components.activities.total.toLocaleString('en-IN')}</span>
      </div>

      {cost.transit_details && (
        <div className="fuel-toll-box">
          <span className="fuel-toll-title">
            🚗 Road Transit Breakdown from {cost.origin_city || 'Origin'} (~{cost.transit_details.one_way_km} km one-way)
          </span>
          <p>
            Petrol @ ₹{cost.transit_details.car.petrol_price_per_litre}/L ({cost.transit_details.car.litres_needed} Litres = ₹{cost.transit_details.car.fuel_cost.toLocaleString('en-IN')})
            {' + '}
            Expressway Tolls (~₹{cost.transit_details.car.toll_charges.toLocaleString('en-IN')})
            {' = '}
            <strong>₹{cost.transit_details.car.per_person.toLocaleString('en-IN')}/person</strong> (Group of {cost.member_count})
          </p>
        </div>
      )}
    </div>
  )
}

export function RecommendationsPanel({ tripId, isOrganizer, onCandidateAdded, onGoToPreferences }: Props) {
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([])
  const [originCity, setOriginCity] = useState('delhi')
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  // Expanded destination state
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [weatherData, setWeatherData] = useState<Record<string, WeatherResponse>>({})
  const [costData, setCostData] = useState<Record<string, CostEstimate>>({})
  const [aiData, setAiData] = useState<Record<string, AiResponse>>({})
  const [loadingWeather, setLoadingWeather] = useState<Set<string>>(new Set())
  const [loadingCost, setLoadingCost] = useState<Set<string>>(new Set())
  const [loadingAi, setLoadingAi] = useState<Set<string>>(new Set())
  const [promotingId, setPromotingId] = useState<string | null>(null)

  // Comparison state
  const [compareA, setCompareA] = useState<string | null>(null)
  const [compareB, setCompareB] = useState<string | null>(null)
  const [compareResult, setCompareResult] = useState<AiResponse | null>(null)
  const [isComparing, setIsComparing] = useState(false)

  const loadData = useCallback(
    async (showRefreshNotice = false, city = originCity) => {
      if (showRefreshNotice) {
        setIsRefreshing(true)
      } else {
        setIsLoading(true)
      }
      setError(null)

      try {
        const data = await getRecommendations(tripId, city)
        setRecommendations(data)
        if (showRefreshNotice) {
          const cityLabel = ORIGIN_CITIES.find((c) => c.id === city)?.label || city
          setMessage(`✨ Recommendations updated for departure from ${cityLabel}.`)
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Could not load recommendations.')
      } finally {
        setIsLoading(false)
        setIsRefreshing(false)
      }
    },
    [originCity, tripId],
  )

  function handleOriginCityChange(newCity: string) {
    setOriginCity(newCity)
    setCostData({}) // clear cached cost estimates since departure city changed
    void loadData(true, newCity)
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData(false, originCity)
    }, 0)

    return () => window.clearTimeout(timer)
  }, [loadData, originCity])

  async function toggleExpand(destId: string) {
    if (expandedId === destId) {
      setExpandedId(null)
      return
    }
    setExpandedId(destId)

    // Load weather and full cost in parallel if not cached
    if (!weatherData[destId] && !loadingWeather.has(destId)) {
      setLoadingWeather((s) => new Set(s).add(destId))
      getDestinationWeather(tripId, destId)
        .then((w) => setWeatherData((d) => ({ ...d, [destId]: w })))
        .catch(() => {})
        .finally(() => setLoadingWeather((s) => { const n = new Set(s); n.delete(destId); return n }))
    }

    if (!costData[destId] && !loadingCost.has(destId)) {
      setLoadingCost((s) => new Set(s).add(destId))
      getCostEstimate(tripId, destId, originCity)
        .then((c) => setCostData((d) => ({ ...d, [destId]: c })))
        .catch(() => {})
        .finally(() => setLoadingCost((s) => { const n = new Set(s); n.delete(destId); return n }))
    }
  }

  async function loadAiExplanation(destId: string, destName: string) {
    if (aiData[destId] || loadingAi.has(destId)) return
    const rec = recommendations.find((r) => r.destination_id === destId)
    const w = weatherData[destId]
    const c = costData[destId]
    const weatherSummary = w?.days?.[0]
      ? `${w.days[0].description}, ${(w.days.reduce((s, d) => s + (d.temperature_max_c ?? 0), 0) / w.days.length).toFixed(0)}°C avg`
      : rec?.summary?.weather_summary || undefined
    const costSummary = c
      ? `₹${c.per_person_cost.toLocaleString('en-IN')}/person (${c.trip_nights} nights from ${c.origin_city || originCity})`
      : rec?.summary?.estimated_budget_per_person
        ? `₹${rec.summary.estimated_budget_per_person.toLocaleString('en-IN')}/person`
        : undefined

    setLoadingAi((s) => new Set(s).add(destId))
    try {
      const result = await aiExplainDestination(tripId, destId, weatherSummary, costSummary, originCity)
      setAiData((d) => ({ ...d, [destId]: result }))
    } catch {
      setAiData((d) => ({
        ...d,
        [destId]: {
          content: null,
          error: `Could not generate explanation for ${destName}.`,
        },
      }))
    } finally {
      setLoadingAi((s) => { const n = new Set(s); n.delete(destId); return n })
    }
  }

  async function handlePromote(destId: string, destName: string) {
    setPromotingId(destId)
    setMessage(null)
    setError(null)
    try {
      await promoteRecommendation(tripId, destId)
      setMessage(`🎉 ${destName} has been added as a candidate for group voting!`)
      onCandidateAdded()
      void loadData(false, originCity)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not add this destination.')
    } finally {
      setPromotingId(null)
    }
  }

  async function handleCompare() {
    if (!compareA || !compareB) return
    setIsComparing(true)
    setCompareResult(null)
    try {
      const recA = recommendations.find((r) => r.destination_id === compareA)
      const recB = recommendations.find((r) => r.destination_id === compareB)
      const wA = weatherData[compareA]?.message || recA?.summary?.weather_summary || undefined
      const wB = weatherData[compareB]?.message || recB?.summary?.weather_summary || undefined
      const cA = costData[compareA]
        ? `₹${costData[compareA].per_person_cost.toLocaleString('en-IN')}/person`
        : recA?.summary?.estimated_budget_per_person
          ? `₹${recA.summary.estimated_budget_per_person.toLocaleString('en-IN')}/person`
          : undefined
      const cB = costData[compareB]
        ? `₹${costData[compareB].per_person_cost.toLocaleString('en-IN')}/person`
        : recB?.summary?.estimated_budget_per_person
          ? `₹${recB.summary.estimated_budget_per_person.toLocaleString('en-IN')}/person`
          : undefined

      const result = await aiCompareDestinations(
        tripId,
        compareA,
        compareB,
        wA,
        wB,
        cA,
        cB,
        originCity,
      )
      setCompareResult(result)
    } catch (err: unknown) {
      setCompareResult({ content: null, error: err instanceof Error ? err.message : 'Comparison failed.' })
    } finally {
      setIsComparing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="recs-panel">
        <div className="recs-loading">
          <span className="spinner" aria-hidden="true" />
          <span>Analyzing group preferences, distance & travel pricing…</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="recs-panel">
        <Notice tone="error">{error}</Notice>
        <button className="button button--outline" type="button" onClick={() => void loadData()}>
          Try Again
        </button>
      </div>
    )
  }

  if (recommendations.length === 0) {
    return (
      <div className="recs-panel">
        <Notice tone="info">
          No recommendations yet. Make sure at least one joined member has submitted their preferences.
        </Notice>
        <button className="button button--outline" type="button" onClick={() => void loadData(true)}>
          🔄 Refresh
        </button>
      </div>
    )
  }

  const scored = recommendations.filter((r) => r.compatibility_score !== null)
  const unscored = recommendations.filter((r) => r.compatibility_score === null)
  const hasScored = scored.length > 0
  const displayList = hasScored ? scored : recommendations

  return (
    <div className="recs-panel">
      {/* Top action toolbar with Departure City selector and Refresh */}
      <div className="recs-toolbar">
        <div className="toolbar-stats">
          <span className="toolbar-stat-pill">
            {hasScored
              ? `✨ ${scored.length} Personalized Recommendations`
              : `📍 ${recommendations.length} Destinations Available`}
          </span>
          <span className="toolbar-stat-sub">
            {hasScored
              ? 'Ranked by group preferences, real transit pricing and live weather'
              : 'Showing catalog options · Submit preferences to activate ML ranking'}
          </span>
        </div>
        <div className="toolbar-actions">
          <div className="origin-city-selector">
            <label htmlFor="origin-city-select" className="origin-label">
              <span>📍 Traveling from:</span>
              <select
                id="origin-city-select"
                value={originCity}
                onChange={(e) => handleOriginCityChange(e.target.value)}
                className="origin-select"
                aria-label="Departure city hub"
              >
                {ORIGIN_CITIES.map((c) => (
                  <option key={c.id} value={c.id}>{c.label}</option>
                ))}
              </select>
            </label>
          </div>
          <button
            className="button button--outline button--small refresh-button"
            type="button"
            disabled={isRefreshing}
            onClick={() => void loadData(true)}
            title="Recalculate recommendations using latest member preferences and selected departure city"
          >
            {isRefreshing ? '🔄 Refreshing…' : '🔄 Refresh Recommendations'}
          </button>
        </div>
      </div>

      {message && <Notice tone="success">{message}</Notice>}

      {!hasScored && (
        <div className="no-preferences-banner">
          <div className="no-preferences-content">
            <span className="no-preferences-icon" aria-hidden="true">💡</span>
            <div>
              <h4>No Group Preferences Submitted Yet</h4>
              <p>
                Showing destination catalog with transit pricing and live weather from <strong>{ORIGIN_CITIES.find(c => c.id === originCity)?.label || originCity}</strong>. Submit your preferences in the <strong>My Preferences</strong> tab to calculate personalized ML TF-IDF similarity scores.
              </p>
            </div>
          </div>
          {onGoToPreferences && (
            <button className="button button--primary button--small" type="button" onClick={onGoToPreferences}>
              ✏️ Go to My Preferences
            </button>
          )}
        </div>
      )}

      {/* Compare tool */}
      {scored.length >= 2 && (
        <div className="compare-tool panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Smart Comparison</span>
              <h3>Compare two destinations side-by-side</h3>
            </div>
          </div>
          <div className="compare-selects">
            <select
              value={compareA ?? ''}
              onChange={(e) => setCompareA(e.target.value || null)}
              aria-label="First destination"
            >
              <option value="">Pick first destination…</option>
              {scored.map((r) => (
                <option key={r.destination_id} value={r.destination_id}>{r.name}</option>
              ))}
            </select>
            <span className="compare-vs" aria-hidden="true">vs</span>
            <select
              value={compareB ?? ''}
              onChange={(e) => setCompareB(e.target.value || null)}
              aria-label="Second destination"
            >
              <option value="">Pick second destination…</option>
              {scored.map((r) => (
                <option key={r.destination_id} value={r.destination_id}>{r.name}</option>
              ))}
            </select>
            <button
              className="button button--primary button--small"
              type="button"
              disabled={!compareA || !compareB || compareA === compareB || isComparing}
              onClick={() => void handleCompare()}
            >
              {isComparing ? 'Comparing…' : 'Compare'}
            </button>
          </div>
          {compareResult && (
            <div className="ai-result">
              {compareResult.error ? (
                <Notice tone="error">{compareResult.error}</Notice>
              ) : (
                <div className="ai-content">
                  <span className="eyebrow">AI Comparison Result</span>
                  <p>{compareResult.content}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Destination cards */}
      <div className="recs-section">
        <div className="recs-list">
          {displayList.map((rec, index) => {
            const isExpanded = expandedId === rec.destination_id
            const weather = weatherData[rec.destination_id]
            const cost = costData[rec.destination_id]
            const ai = aiData[rec.destination_id]
            const isWeatherLoading = loadingWeather.has(rec.destination_id)
            const isCostLoading = loadingCost.has(rec.destination_id)
            const isAiLoading = loadingAi.has(rec.destination_id)
            const summary = rec.summary

            return (
              <article key={rec.destination_id} className={`rec-card ${index === 0 && hasScored ? 'rec-card--top' : ''}`}>
                <div className="rec-card-header">
                  <div className="rec-rank" aria-label={`Rank ${index + 1}`}>
                    {hasScored ? `#${index + 1}` : '📍'}
                  </div>
                  <div className="rec-info">
                    <div className="rec-title-row">
                      <strong className="rec-name">{rec.name}</strong>
                      <MatchScoreBadge score={rec.compatibility_score} />
                    </div>
                    {summary?.weather_summary && (
                      <span className="rec-climate-tag">📍 {summary.weather_summary} · Route from {summary.origin_city || 'Origin Hub'}</span>
                    )}
                  </div>
                  <div className="rec-actions">
                    {isOrganizer && (
                      <button
                        className="button button--primary button--small"
                        type="button"
                        disabled={promotingId === rec.destination_id}
                        onClick={() => void handlePromote(rec.destination_id, rec.name)}
                      >
                        {promotingId === rec.destination_id ? 'Adding…' : '+ Add to Voting'}
                      </button>
                    )}
                    <button
                      className="button button--quiet button--small"
                      type="button"
                      aria-expanded={isExpanded}
                      onClick={() => void toggleExpand(rec.destination_id)}
                    >
                      {isExpanded ? 'Hide Details ▲' : 'Details & Breakdown ▼'}
                    </button>
                  </div>
                </div>

                {/* Verdict Banner */}
                {summary?.verdict && (
                  <div className={`rec-verdict-banner rec-verdict-banner--${summary.verdict_tone}`}>
                    <span className="verdict-icon">
                      {summary.verdict_tone === 'success' ? '✅' : summary.verdict_tone === 'warning' ? '⚠️' : 'ℹ️'}
                    </span>
                    <span className="verdict-text">{summary.verdict}</span>
                  </div>
                )}

                {/* Key Benefits */}
                {summary && summary.benefits.length > 0 && (
                  <div className="rec-benefits-box">
                    <span className="benefits-label">Why Choose {rec.name}?</span>
                    <ul className="rec-benefits-list">
                      {summary.benefits.map((b, i) => (
                        <li key={i}>{b}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Transport Options Quick Preview */}
                {summary && summary.transport_options.length > 0 && (
                  <div className="transport-preview-bar">
                    <span className="transport-bar-label">Transit Options:</span>
                    <div className="transport-pills">
                      {summary.transport_options.map((opt) => (
                        <div key={opt.mode} className="transport-pill" title={opt.details}>
                          <span className="transport-pill-mode">
                            {opt.mode === 'flight' ? '✈️' : opt.mode === 'train' ? '🚆' : '🚗'} {opt.label}
                          </span>
                          <span className="transport-pill-price">₹{opt.estimated_cost_per_person.toLocaleString('en-IN')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cautions if any */}
                {summary && summary.cautions.length > 0 && (
                  <div className="rec-cautions-box">
                    {summary.cautions.map((c, i) => (
                      <span key={i} className="caution-tag">💡 Note: {c}</span>
                    ))}
                  </div>
                )}

                {/* Expanded Detailed Section */}
                {isExpanded && (
                  <div className="rec-expanded">
                    {/* Live Weather Forecast */}
                    <div className="rec-section">
                      <span className="eyebrow">Weather Forecast (Open-Meteo)</span>
                      {isWeatherLoading ? (
                        <p className="loading-hint">Loading live weather data…</p>
                      ) : weather ? (
                        <WeatherMiniCard weather={weather} />
                      ) : (
                        <p className="loading-hint">Weather forecast unavailable</p>
                      )}
                    </div>

                    {/* Detailed Travel Cost Breakdown */}
                    <div className="rec-section">
                      <span className="eyebrow">Complete Trip Cost Breakdown</span>
                      {isCostLoading ? (
                        <p className="loading-hint">Calculating hotel, food, and transit costs…</p>
                      ) : cost ? (
                        <CostDetailedCard cost={cost} />
                      ) : (
                        <p className="loading-hint">Cost breakdown unavailable</p>
                      )}
                    </div>

                    {/* AI Explanation on Demand */}
                    <div className="rec-section">
                      <span className="eyebrow">AI Travel Explanation</span>
                      {isAiLoading ? (
                        <p className="loading-hint">✨ Gemini is synthesizing an explanation for your group…</p>
                      ) : ai ? (
                        <div className="ai-content">
                          {ai.error ? (
                            <Notice tone="error">{ai.error}</Notice>
                          ) : (
                            <p>{ai.content}</p>
                          )}
                        </div>
                      ) : (
                        <button
                          className="button button--outline button--small"
                          type="button"
                          onClick={() => void loadAiExplanation(rec.destination_id, rec.name)}
                        >
                          ✨ Ask AI for Detailed Analysis of {rec.name}
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </article>
            )
          })}
        </div>
      </div>

      {/* Unscored destinations (if any metadata missing) */}
      {hasScored && unscored.length > 0 && (
        <div className="recs-section recs-section--unscored">
          <div className="recs-section-heading">
            <div>
              <span className="eyebrow">Other Places in Catalog</span>
              <h3>Destinations with incomplete preferences</h3>
            </div>
            <span className="count-badge count-badge--muted">{unscored.length}</span>
          </div>
          <div className="recs-list recs-list--compact">
            {unscored.map((rec) => (
              <article key={rec.destination_id} className="rec-card rec-card--unscored">
                <div className="rec-card-header">
                  <div className="rec-info">
                    <strong className="rec-name">{rec.name}</strong>
                  </div>
                  {isOrganizer && (
                    <button
                      className="button button--quiet button--small"
                      type="button"
                      disabled={promotingId === rec.destination_id}
                      onClick={() => void handlePromote(rec.destination_id, rec.name)}
                    >
                      {promotingId === rec.destination_id ? 'Adding…' : '+ Add to Voting'}
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
