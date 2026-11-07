import { useEffect, useState, type FormEvent } from 'react'
import {
  addTripDestinationCandidate,
  confirmDestination,
  finalizeTripDestination,
  listDestinations,
  listTripDestinations,
  rejectTripDestination,
  searchDestinations,
} from '../api/destinations'
import { updateTripStatus } from '../api/trips'
import { getMyVote, getVoteResults, submitVote } from '../api/votes'
import { Notice } from './Notice'
import type {
  Destination,
  DestinationSearchResult,
  TripDestination,
  TripStatus,
  TripVote,
  TripVoteResults,
} from '../types/models'

interface ConfirmedPlace {
  searchResult: DestinationSearchResult
  tripDestination: TripDestination
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback
}

function destinationLabel(destination: Destination | null | undefined, id?: string | null): string {
  if (destination?.name) {
    return destination.name
  }
  if (id) {
    return `Destination ${id.slice(0, 8)}`
  }
  return 'Selected Destination'
}

function placeDetails(place: Destination | DestinationSearchResult): string {
  return [place.region, place.country].filter(Boolean).join(', ')
}

export function DestinationPlanningPanel({
  tripId,
  tripStatus,
  isOrganizer,
  onTripUpdated,
  readOnly = false,
}: {
  tripId: string
  tripStatus: TripStatus
  isOrganizer: boolean
  onTripUpdated: () => Promise<void>
  readOnly?: boolean
}) {
  const [catalog, setCatalog] = useState<Destination[]>([])
  const [candidates, setCandidates] = useState<TripDestination[]>([])
  const [confirmedPlaces, setConfirmedPlaces] = useState<ConfirmedPlace[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<DestinationSearchResult[]>([])
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null)
  const [vote, setVote] = useState<TripVote | null>(null)
  const [voteResults, setVoteResults] = useState<TripVoteResults | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSearching, setIsSearching] = useState(false)
  const [busyAction, setBusyAction] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const loadData = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const [destinationData, candidateData] = await Promise.all([
          listDestinations(),
          listTripDestinations(tripId),
        ])
        let ownVote: TripVote | null = null
        let results: TripVoteResults | null = null
        if (tripStatus === 'voting') {
          ;[ownVote, results] = await Promise.all([
            getMyVote(tripId),
            getVoteResults(tripId),
          ])
        }
        if (active) {
          setCatalog(destinationData)
          setCandidates(candidateData)
          setVote(ownVote)
          setVoteResults(results)
        }
      } catch (loadError) {
        if (active) {
          setError(errorMessage(loadError, 'Could not load destinations for this trip.'))
        }
      } finally {
        if (active) {
          setIsLoading(false)
        }
      }
    }

    void loadData()
    return () => {
      active = false
    }
  }, [tripId, tripStatus])

  async function refreshCandidates(): Promise<void> {
    const [candidateData, destinationData] = await Promise.all([
      listTripDestinations(tripId),
      listDestinations(),
    ])
    setCandidates(candidateData)
    setCatalog(destinationData)
  }

  async function refreshResults(): Promise<void> {
    const [myVote, results] = await Promise.all([
      getMyVote(tripId),
      getVoteResults(tripId),
    ])
    setVote(myVote)
    setVoteResults(results)
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const query = searchQuery.trim()
    if (query.length < 2) {
      setError('Enter at least 2 characters to search for a destination.')
      return
    }
    if (query.length > 100) {
      setError('Destination search is limited to 100 characters.')
      return
    }

    setError(null)
    setMessage(null)
    setIsSearching(true)
    setSelectedPlaceId(null)
    try {
      setSearchResults(await searchDestinations(query, 8))
    } catch (searchError) {
      setError(errorMessage(searchError, 'Could not search destinations.'))
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  async function handleConfirmPlace(place: DestinationSearchResult) {
    const actionKey = `confirm:${place.external_place_id}`
    setBusyAction(actionKey)
    setError(null)
    setMessage(null)
    try {
      const tripDestination = await confirmDestination(tripId, place.external_place_id)
      setConfirmedPlaces((current) => [
        ...current.filter((item) => item.tripDestination.id !== tripDestination.id),
        { searchResult: place, tripDestination },
      ])
      setSelectedPlaceId(null)
      setMessage(`${place.name} is confirmed. ${isOrganizer ? 'You can add it to the candidate list below.' : 'The trip organizer can add it to the candidate list.'}`)
      try {
        await refreshCandidates()
      } catch (refreshError) {
        setError(`Place confirmed, but the candidate list could not refresh: ${errorMessage(refreshError, 'request failed')}`)
      }
    } catch (confirmError) {
      setError(errorMessage(confirmError, 'Could not confirm this destination.'))
    } finally {
      setBusyAction(null)
    }
  }

  async function handleAddCandidate(confirmed: ConfirmedPlace) {
    const actionKey = `add:${confirmed.tripDestination.destination_id}`
    setBusyAction(actionKey)
    setError(null)
    setMessage(null)
    try {
      await addTripDestinationCandidate(
        tripId,
        confirmed.tripDestination.destination_id,
      )
      setMessage(`${confirmed.searchResult.name} was added to trip candidates.`)
      try {
        await refreshCandidates()
      } catch (refreshError) {
        setError(`Destination added, but the candidate list could not refresh: ${errorMessage(refreshError, 'request failed')}`)
      }
    } catch (addError) {
      setError(errorMessage(addError, 'Could not add this destination to candidates.'))
    } finally {
      setBusyAction(null)
    }
  }

  async function handleCandidateAction(
    candidate: TripDestination,
    action: 'finalize' | 'reject',
  ) {
    const actionKey = `${action}:${candidate.id}`
    setBusyAction(actionKey)
    setError(null)
    setMessage(null)
    try {
      if (action === 'finalize') {
        await finalizeTripDestination(tripId, candidate.id)
      } else {
        await rejectTripDestination(tripId, candidate.id)
      }
      setMessage(
        action === 'finalize'
          ? `${destinationLabel(catalog.find((item) => item.id === candidate.destination_id), candidate.destination_id)} was finalized.`
          : 'Destination candidate was rejected.',
      )
      try {
        await refreshCandidates()
      } catch (refreshError) {
        setError(`Candidate updated, but the list could not refresh: ${errorMessage(refreshError, 'request failed')}`)
      }
      if (action === 'finalize') {
        try {
          await onTripUpdated()
        } catch (refreshError) {
          setError(`Destination finalized, but the trip state could not refresh: ${errorMessage(refreshError, 'request failed')}`)
        }
      }
    } catch (candidateError) {
      setError(errorMessage(candidateError, 'Could not update this candidate.'))
    } finally {
      setBusyAction(null)
    }
  }

  async function handleStartVoting() {
    if (!candidates.some((candidate) => candidate.status.toLowerCase() === 'proposed')) {
      setError('Add at least one proposed destination before starting the vote.')
      return
    }
    setBusyAction('start-voting')
    setError(null)
    setMessage(null)
    try {
      await updateTripStatus(tripId, 'voting')
      await onTripUpdated()
      setMessage('Voting is open. Everyone in the trip can now vote.')
    } catch (startError) {
      setError(errorMessage(startError, 'Could not start voting.'))
    } finally {
      setBusyAction(null)
    }
  }

  async function handleVote(candidate: TripDestination) {
    const actionKey = `vote:${candidate.id}`
    setBusyAction(actionKey)
    setError(null)
    setMessage(null)
    try {
      const savedVote = await submitVote(tripId, candidate.id)
      setVote(savedVote)
      setMessage(
        vote
          ? 'Your vote was changed.'
          : 'Your vote was recorded. You can change it while voting is open.',
      )
      try {
        await refreshResults()
      } catch (refreshError) {
        setError(`Your vote was saved, but the totals could not refresh: ${errorMessage(refreshError, 'request failed')}`)
      }
    } catch (voteError) {
      setError(errorMessage(voteError, 'Could not submit your vote.'))
    } finally {
      setBusyAction(null)
    }
  }

  const candidateDestinationIds = new Set(
    candidates.map((candidate) => candidate.destination_id),
  )
  const destinationById = new Map(catalog.map((destination) => [destination.id, destination]))
  const resultCounts = new Map(
    (voteResults?.results ?? []).map((result) => [
      result.trip_destination_id,
      result.vote_count,
    ]),
  )
  const activeCandidates = tripStatus === 'voting'
    ? candidates.filter((candidate) => candidate.status.toLowerCase() !== 'rejected')
    : candidates
  const hasProposedCandidates = candidates.some(
    (candidate) => candidate.status.toLowerCase() === 'proposed',
  )

  return (
    <section className="panel destination-planning-panel" aria-labelledby="destination-planning-title">
      <div className="destination-panel-heading">
        <div className="destination-compass" aria-hidden="true">✳</div>
        <div>
          <span className="eyebrow">
            {tripStatus === 'voting'
              ? 'The group decides together'
              : tripStatus === 'planning'
                ? 'The next part of planning'
                : 'Trip planning closed'}
          </span>
          <h2 id="destination-planning-title">
            {tripStatus === 'voting'
              ? 'Vote for your destination'
              : tripStatus === 'planning'
                ? 'Choose where you’ll go'
                : 'Trip destinations'}
          </h2>
          <p>
            {tripStatus === 'voting'
              ? 'Choose a trip candidate below. You can change your vote while voting is open.'
              : tripStatus === 'planning'
                ? 'Search for a real place, confirm it through PackVote, and let the organizer add confirmed destinations to the candidate list.'
                : 'This trip is not accepting destination suggestions or votes right now.'}
          </p>
        </div>
      </div>

            {tripStatus === 'finalized' && (
        <div className="finalized-destination-hero">
          <div className="finalized-badge">🎉 Final Destination Confirmed</div>
          {(() => {
            const finalizedCandidate = candidates.find((c) => c.status.toLowerCase() === 'finalized')
            const dest = finalizedCandidate ? destinationById.get(finalizedCandidate.destination_id) : null
            return finalizedCandidate ? (
              <div className="finalized-destination-card">
                <h3>{destinationLabel(dest, finalizedCandidate.destination_id)}</h3>
                <p>{dest ? placeDetails(dest) : ''}</p>
                <span className="finalized-subtext">
                  The group has voted and the organizer has confirmed this destination for the trip!
                </span>
              </div>
            ) : (
              <p>This trip has been finalized.</p>
            )
          })()}
        </div>
      )}

      {error && <Notice>{error}</Notice>}
      {message && <Notice tone="success">{message}</Notice>}

      {!readOnly && tripStatus === 'planning' && (
        <div className="destination-search-block">
          <form className="destination-search-form" onSubmit={handleSearch}>
            <label className="field" htmlFor="destination-search">
              <span>Search destinations</span>
              <input
                id="destination-search"
                minLength={2}
                maxLength={100}
                required
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Try a city, region, or place"
              />
            </label>
            <button className="button button--primary" type="submit" disabled={isSearching}>
              {isSearching ? 'Searching…' : 'Search places'}
            </button>
          </form>

          {searchResults.length > 0 && (
            <div className="destination-search-results" aria-label="Destination search results">
              {searchResults.map((place) => {
                const selected = selectedPlaceId === place.external_place_id
                return (
                  <article
                    className={`destination-search-result ${selected ? 'destination-search-result--selected' : ''}`}
                    key={place.external_place_id}
                  >
                    <div className="destination-result-pin" aria-hidden="true">⌖</div>
                    <div className="destination-result-copy">
                      <strong>{place.name}</strong>
                      <span>{place.display_name || placeDetails(place)}</span>
                    </div>
                    {selected ? (
                      <button
                        className="button button--primary button--small"
                        type="button"
                        disabled={busyAction === `confirm:${place.external_place_id}`}
                        onClick={() => void handleConfirmPlace(place)}
                      >
                        {busyAction === `confirm:${place.external_place_id}` ? 'Confirming…' : 'Confirm place'}
                      </button>
                    ) : (
                      <button
                        className="button button--outline button--small"
                        type="button"
                        onClick={() => setSelectedPlaceId(place.external_place_id)}
                      >
                        Select
                      </button>
                    )}
                  </article>
                )
              })}
            </div>
          )}
          {!isSearching && searchQuery.trim().length >= 2 && searchResults.length === 0 && !error && (
            <p className="destination-empty-hint">No places found. Try a different search.</p>
          )}
        </div>
      )}

      {!readOnly && confirmedPlaces.length > 0 && tripStatus === 'planning' && (
        <div className="confirmed-places">
          <h3>Places confirmed this visit</h3>
          {confirmedPlaces.map((confirmed) => {
            const isAlreadyCandidate = candidateDestinationIds.has(
              confirmed.tripDestination.destination_id,
            )
            return (
              <div className="confirmed-place-row" key={confirmed.tripDestination.id}>
                <div className="destination-result-copy">
                  <strong>{confirmed.searchResult.name}</strong>
                  <span>{confirmed.searchResult.display_name || placeDetails(confirmed.searchResult)}</span>
                </div>
                {isOrganizer && tripStatus === 'planning' && (
                  <button
                    className="button button--outline button--small"
                    type="button"
                    disabled={isAlreadyCandidate || busyAction === `add:${confirmed.tripDestination.destination_id}`}
                    onClick={() => void handleAddCandidate(confirmed)}
                  >
                    {isAlreadyCandidate
                      ? 'In candidate list'
                      : busyAction === `add:${confirmed.tripDestination.destination_id}`
                        ? 'Adding…'
                        : 'Add to candidates'}
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}

      <div className="candidate-section">
        <div className="candidate-section-heading">
          <div>
            <span className="eyebrow">Places being considered</span>
            <h3>Trip candidates</h3>
          </div>
          <div className="candidate-heading-actions">
            <button
              className="button button--quiet button--small"
              type="button"
              disabled={isLoading}
              onClick={() => {
                void refreshCandidates()
                if (tripStatus === 'voting') void refreshResults()
              }}
              title="Refresh candidate list and live votes"
            >
              🔄 Refresh
            </button>
            <span className="count-badge">{activeCandidates.length}</span>
          </div>
        </div>

        {isLoading ? (
          <p className="destination-empty-hint">Loading trip candidates…</p>
        ) : activeCandidates.length === 0 ? (
          <p className="destination-empty-hint">
            No trip candidates yet. Search for a place above, confirm it, then the organizer can add it here.
          </p>
        ) : (
          <div className="candidate-list">
            {activeCandidates.map((candidate) => {
              const destination = destinationById.get(candidate.destination_id)
              const isSelectedVote = vote?.trip_destination_id === candidate.id
              const count = resultCounts.get(candidate.id) ?? 0
              const candidateStatus = candidate.status.toLowerCase()
              const canManageCandidate = !['finalized', 'rejected'].includes(candidateStatus)
              return (
                <article className="candidate-card" key={candidate.id}>
                  <div className="candidate-card-main">
                    <div className="destination-result-pin" aria-hidden="true">⌖</div>
                    <div className="destination-result-copy">
                      <strong>{destinationLabel(destination, candidate.destination_id)}</strong>
                      <span>
                        {destination ? placeDetails(destination) : 'Place details unavailable'}
                        {' · '}
                        {candidate.status}
                      </span>
                    </div>
                    {tripStatus === 'voting' && (
                      <span className="candidate-vote-count">
                        {count} {count === 1 ? 'vote' : 'votes'}
                      </span>
                    )}
                  </div>

                  {!readOnly && isOrganizer && (tripStatus === 'planning' || tripStatus === 'voting') && canManageCandidate && (
                    <div className="candidate-actions">
                      <button
                        className="button button--outline button--small"
                        type="button"
                        disabled={busyAction === `finalize:${candidate.id}`}
                        onClick={() => void handleCandidateAction(candidate, 'finalize')}
                      >
                        {busyAction === `finalize:${candidate.id}` ? 'Finalizing…' : 'Finalize'}
                      </button>
                      <button
                        className="button button--quiet button--small"
                        type="button"
                        disabled={busyAction === `reject:${candidate.id}`}
                        onClick={() => void handleCandidateAction(candidate, 'reject')}
                      >
                        {busyAction === `reject:${candidate.id}` ? 'Rejecting…' : 'Reject'}
                      </button>
                    </div>
                  )}

                  {tripStatus === 'voting' && !readOnly && (
                    <button
                      className={`button ${isSelectedVote ? 'button--outline' : 'button--primary'} button--small`}
                      type="button"
                      disabled={busyAction === `vote:${candidate.id}`}
                      aria-pressed={isSelectedVote}
                      onClick={() => void handleVote(candidate)}
                    >
                      {busyAction === `vote:${candidate.id}`
                        ? 'Saving vote…'
                        : isSelectedVote
                          ? 'Your choice · change vote'
                          : vote
                            ? 'Change vote to this'
                            : 'Vote for this'}
                    </button>
                  )}
                </article>
              )
            })}
          </div>
        )}
      </div>

            {!readOnly && isOrganizer && tripStatus === 'planning' && (
        <div className="candidate-actions">
          <button
            className="button button--primary"
            type="button"
            disabled={!hasProposedCandidates || busyAction === 'start-voting'}
            onClick={() => void handleStartVoting()}
          >
            {busyAction === 'start-voting' ? 'Starting voting…' : 'Start voting'}
          </button>
          {!hasProposedCandidates && (
            <p className="destination-empty-hint">
              Add at least one proposed destination candidate to start voting.
            </p>
          )}
        </div>
      )}

      {tripStatus === 'voting' && (
        <div className="vote-results">
          <div className="candidate-section-heading">
            <div>
              <span className="eyebrow">Live group tally</span>
              <h3>Vote results</h3>
            </div>
            <span className="count-badge">{voteResults?.total_votes ?? 0}</span>
          </div>

          {voteResults && (
            <div className="vote-results-summary">
              {voteResults.participation_count !== undefined && voteResults.total_eligible_members ? (
                <p className="vote-participation-text">
                  👥 <strong>{voteResults.participation_count}</strong> of{' '}
                  <strong>{voteResults.total_eligible_members}</strong> joined members have voted
                  ({Math.round((voteResults.participation_count / voteResults.total_eligible_members) * 100)}% participation).
                </p>
              ) : null}

              {voteResults.is_tie && (
                <div className="vote-tie-alert">
                  <span className="tie-badge">⚖️ Tie Detected</span>
                  <p>
                    Multiple destinations share the highest vote count. Members may change their vote, or the organizer can break the tie by confirming a destination.
                  </p>
                </div>
              )}

              {voteResults.winner_trip_destination_id && !voteResults.is_tie && (
                <div className="vote-winner-banner">
                  <span className="winner-badge">🏆 Leading Candidate</span>
                  <p>
                    <strong>
                      {(() => {
                        const winCand = candidates.find((c) => c.id === voteResults.winner_trip_destination_id);
                        const winDest = winCand ? destinationById.get(winCand.destination_id) : undefined;
                        return destinationLabel(winDest, voteResults.winner_trip_destination_id);
                      })()}
                    </strong>{' '}
                    is currently in the lead!
                    {isOrganizer && ' You can confirm this destination to finalize the trip.'}
                  </p>
                </div>
              )}

              <div className="vote-bars-list">
                {activeCandidates.map((candidate) => {
                  const destination = destinationById.get(candidate.destination_id)
                  const count = resultCounts.get(candidate.id) ?? 0
                  const pct = voteResults.total_votes > 0
                    ? Math.round((count / voteResults.total_votes) * 100)
                    : 0
                  const isLeading = voteResults.winner_trip_destination_id === candidate.id

                  return (
                    <div className={`vote-bar-item ${isLeading ? 'vote-bar-item--lead' : ''}`} key={candidate.id}>
                      <div className="vote-bar-header">
                        <span className="vote-bar-name">
                          {destinationLabel(destination, candidate.destination_id)}
                          {isLeading && ' 🏆'}
                        </span>
                        <span className="vote-bar-stat">
                          {count} {count === 1 ? 'vote' : 'votes'} ({pct}%)
                        </span>
                      </div>
                      <div className="vote-bar-track">
                        <div
                          className="vote-bar-fill"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      {isOrganizer && !readOnly && candidate.status.toLowerCase() !== 'finalized' && (
                        <div className="vote-bar-action">
                          <button
                            className="button button--primary button--small"
                            type="button"
                            disabled={busyAction === `finalize:${candidate.id}`}
                            onClick={() => void handleCandidateAction(candidate, 'finalize')}
                          >
                            {busyAction === `finalize:${candidate.id}`
                              ? 'Confirming…'
                              : 'Confirm as Final Destination'}
                          </button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
