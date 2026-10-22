import { useCallback, useEffect, useState } from 'react'
import {
  archiveTrip,
  listInvitations,
  listTripHistory,
  listTrips,
  respondToInvitation,
  restoreTrip,
} from '../api/trips'
import { useAuth } from '../context/useAuth'
import { LoadingState } from '../components/LoadingState'
import { Notice } from '../components/Notice'
import { TripCreateForm } from '../components/TripCreateForm'
import type { Trip } from '../types/models'

function formatDate(date: string | null): string {
  if (!date) {
    return 'Dates to be decided'
  }
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    .format(new Date(`${date}T12:00:00`))
}

function TripCard({ trip, onOpen }: { trip: Trip; onOpen: (trip: Trip) => void }) {
  return (
    <button className="trip-card" type="button" onClick={() => onOpen(trip)}>
      <span className="trip-card-art" aria-hidden="true">
        <span className="trip-card-sun" />
        <span className="trip-card-hill trip-card-hill--back" />
        <span className="trip-card-hill trip-card-hill--front" />
        <span className="trip-card-art-label">PACKVOTE<br />GETAWAY</span>
      </span>
      <span className="trip-card-content">
        <span className="trip-card-meta">
          <span className={`status-dot status-dot--${trip.status}`} />
          {trip.status}
        </span>
        <strong>{trip.name}</strong>
        <span className="trip-card-date">{formatDate(trip.start_date)}{trip.end_date ? ` — ${formatDate(trip.end_date)}` : ''}</span>
        <span className="trip-card-link">Open trip <span aria-hidden="true">→</span></span>
      </span>
    </button>
  )
}

export function DashboardPage({
  onOpenTrip,
}: {
  onOpenTrip: (trip: Trip) => void
}) {
  const { user } = useAuth()
  const [notice, setNotice] = useState<string | null>(null)
  const [isArchiving, setIsArchiving] = useState<string | null>(null)
  const [isRestoring, setIsRestoring] = useState<string | null>(null)
  const [showHistory, setShowHistory] = useState(false)
  const [historyTrips, setHistoryTrips] = useState<Trip[]>([])
  const [isHistoryLoading, setIsHistoryLoading] = useState(false)
  const [trips, setTrips] = useState<Trip[]>([])
  const [invitations, setInvitations] = useState<Trip[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isResponding, setIsResponding] = useState<string | null>(null)

  const loadDashboard = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [myTrips, myInvitations] = await Promise.all([listTrips(), listInvitations()])
      setTrips(myTrips)
      setInvitations(myInvitations)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Could not load your trips.')
    } finally {
      setIsLoading(false)
    }
  }, [])
  useEffect(() => {
    let active = true
    void Promise.all([listTrips(), listInvitations()])
      .then(([myTrips, myInvitations]) => {
        if (active) {
          setTrips(myTrips)
          setInvitations(myInvitations)
        }
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : 'Could not load your trips.')
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [])
  useEffect(() => {
    let active = true;
    let refreshing = false;

    async function refreshDashboardSilently() {
      if (refreshing) return;

      refreshing = true;

      try {
        const [myTrips, myInvitations] = await Promise.all([
          listTrips(),
          listInvitations(),
        ]);

        if (!active) return;

        setTrips(myTrips);
        setInvitations(myInvitations);
      } catch {
        // Keep the existing dashboard data if a background refresh fails.
      } finally {
        refreshing = false;
      }
    }

    const intervalId = window.setInterval(() => {
      void refreshDashboardSilently();
    }, 5000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, []);


useEffect(() => {
  if (!showHistory) return

  let active = true
  let refreshing = false

  async function refreshHistory() {
    if (refreshing) return
    refreshing = true

    try {
      const archivedTrips = await listTripHistory()

      if (!active) return

      setHistoryTrips(archivedTrips)
      setError(null)
    } catch (historyError: unknown) {
      if (active) {
        setError(
          historyError instanceof Error
            ? historyError.message
            : 'Could not load trip history.',
        )
      }
    } finally {
      refreshing = false
      if (active) setIsHistoryLoading(false)
    }
  }

  void refreshHistory()

  const intervalId = window.setInterval(() => {
    void refreshHistory()
  }, 5000)

  return () => {
    active = false
    window.clearInterval(intervalId)
  }
}, [showHistory])


async function handleArchiveTrip(trip: Trip) {
  if (trip.organizer_id !== user?.id) return

  const confirmed = window.confirm(
    `Archive "${trip.name}"? It will move to Trip History and can be restored later.`,
  )

  if (!confirmed) return

  setError(null)
  setNotice(null)
  setIsArchiving(trip.id)

  try {
    const archivedTrip = await archiveTrip(trip.id)

    setTrips((current) =>
      current.filter((item) => item.id !== trip.id),
    )
    setInvitations((current) =>
      current.filter((item) => item.id !== trip.id),
    )
    setHistoryTrips((current) => [
      archivedTrip,
      ...current.filter((item) => item.id !== trip.id),
    ])
    setNotice(`"${trip.name}" was moved to Trip History.`)
  } catch (archiveError: unknown) {
    setError(
      archiveError instanceof Error
        ? archiveError.message
        : 'Could not archive this trip.',
    )
  } finally {
    setIsArchiving(null)
  }
}

async function handleRestoreTrip(trip: Trip) {
  if (trip.organizer_id !== user?.id) return

  setError(null)
  setNotice(null)
  setIsRestoring(trip.id)

  try {
    const restoredTrip = await restoreTrip(trip.id)

    setHistoryTrips((current) =>
      current.filter((item) => item.id !== trip.id),
    )
    setTrips((current) => [
      restoredTrip,
      ...current.filter((item) => item.id !== trip.id),
    ])
    setNotice(`"${trip.name}" was restored to Active Trips.`)
  } catch (restoreError: unknown) {
    setError(
      restoreError instanceof Error
        ? restoreError.message
        : 'Could not restore this trip.',
    )
  } finally {
    setIsRestoring(null)
  }
}

  async function handleInviteResponse(tripId: string, accept: boolean) {
    setIsResponding(tripId)
    setError(null)
    try {
      await respondToInvitation(tripId, accept)
      await loadDashboard()
    } catch (responseError) {
      setError(responseError instanceof Error ? responseError.message : 'Could not update the invitation.')
    } finally {
      setIsResponding(null)
    }
  }

  return (
    <div className="dashboard-page">
      <section className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <span className="eyebrow">Your next chapter starts here</span>
          <h1>Let’s make<br /><em>somewhere</em> happen.</h1>
          <p>Gather your favorite people and turn “we should go sometime” into a plan.</p>
          <button className="button button--primary" type="button" onClick={() => setShowCreate(true)}>
            <span className="button-plus" aria-hidden="true">+</span> Plan a trip
          </button>
        </div>
        <div className="hero-illustration" aria-hidden="true">
          <div className="hero-sun" />
          <div className="hero-cloud hero-cloud--one" />
          <div className="hero-cloud hero-cloud--two" />
          <div className="hero-mountain hero-mountain--back" />
          <div className="hero-mountain hero-mountain--front" />
          <div className="hero-trail" />
          <span className="hero-stamp">GO<br />TOGETHER</span>
        </div>
      </section>

      {error && (
        <div className="dashboard-error">
          <Notice>{error}</Notice>
          <button className="button button--outline button--small" type="button" onClick={() => void loadDashboard()}>
            Try again
          </button>
        </div>
      )}

      {/* ✅ Notice is now independent and will display properly on success */}
      {notice && <Notice tone="success">{notice}</Notice>}

      {invitations.length > 0 && (
        <section className="section-block">
          <div className="section-heading">
            <div>
              <span className="eyebrow">You’re invited</span>
              <h2>Trips waiting for you</h2>
            </div>
            <span className="count-badge">{invitations.length}</span>
          </div>
          <div className="invitation-list">
            {invitations.map((trip) => (
              <article className="invitation-card" key={trip.id}>
                <div className="invitation-icon" aria-hidden="true">✳</div>
                <div className="invitation-copy">
                  <strong>{trip.name}</strong>
                  <span>{trip.description || 'A friend would love to have you along.'}</span>
                </div>
                <div className="invitation-actions">
                  <button
                    className="button button--primary button--small"
                    type="button"
                    disabled={isResponding === trip.id}
                    onClick={() => void handleInviteResponse(trip.id, true)}
                  >
                    Join
                  </button>
                  <button
                    className="button button--quiet button--small"
                    type="button"
                    disabled={isResponding === trip.id}
                    onClick={() => void handleInviteResponse(trip.id, false)}
                  >
                    Decline
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="section-block trips-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">
              {showHistory ? 'Your past adventures' : 'Your shared plans'}
            </span>
            <h2>{showHistory ? 'Trip History' : 'Trips in the making'}</h2>
          </div>

          <div className="trip-view-controls">
            <button
              className={`button ${!showHistory ? 'button--outline' : 'button--quiet'}`}
              type="button"
              onClick={() => {
                  setIsHistoryLoading(true)
                  setShowHistory(true)
                }}
            >
              Active Trips
            </button>

            <button
              className={`button ${showHistory ? 'button--outline' : 'button--quiet'}`}
              type="button"
              onClick={() => setShowHistory(true)}
            >
              Trip History
            </button>

            {!showHistory && !isLoading && trips.length > 0 && (
              <button
                className="button button--outline"
                type="button"
                onClick={() => setShowCreate(true)}
              >
                <span aria-hidden="true">+</span> New trip
              </button>
            )}
          </div>
        </div>

        {showCreate && !showHistory && (
          <TripCreateForm
            onCancel={() => setShowCreate(false)}
            onCreated={(trip) => {
              setShowCreate(false)
              onOpenTrip(trip)
            }}
          />
        )}

        {(showHistory ? isHistoryLoading : isLoading) ? (
          <LoadingState label={showHistory ? 'Loading trip history…' : 'Gathering your trips…'} />
        ) : (showHistory ? historyTrips : trips).length > 0 ? (
          <div className="trip-grid">
            {(showHistory ? historyTrips : trips).map((trip) => (
              <div className="trip-card-item" key={trip.id}>
                <TripCard trip={trip} onOpen={onOpenTrip} />

                {showHistory ? (
                  trip.organizer_id === user?.id && (
                    <div className="trip-card-actions">
                      <button
                        className="button button--outline button--small"
                        type="button"
                        disabled={isRestoring === trip.id}
                        onClick={() => void handleRestoreTrip(trip)}
                      >
                        {isRestoring === trip.id ? 'Restoring…' : 'Restore trip'}
                      </button>
                    </div>
                  )
                ) : (
                  trip.organizer_id === user?.id && (
                    <div className="trip-card-actions">
                      <button
                        className="button button--quiet button--small"
                        type="button"
                        disabled={isArchiving === trip.id}
                        onClick={() => void handleArchiveTrip(trip)}
                      >
                        {isArchiving === trip.id ? 'Archiving…' : 'Archive trip'}
                      </button>
                    </div>
                  )
                )}
              </div>
            ))}
          </div>
        ) : showHistory ? (
          <div className="empty-state">
            <div className="empty-state-icon" aria-hidden="true">✳</div>
            <h3>No archived trips yet.</h3>
            <p>Trips you archive will appear here.</p>
            <button className="button button--primary" type="button" onClick={() => setShowHistory(false)}>
              Back to Active Trips
            </button>
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon" aria-hidden="true">✳</div>
            <h3>Your next favorite memory is waiting.</h3>
            <p>Start a trip, invite your people, and figure out the details together.</p>
            <button className="button button--primary" type="button" onClick={() => setShowCreate(true)}>
              Create your first trip <span aria-hidden="true">→</span>
            </button>
          </div>
        )}
      </section>

      <div className="dashboard-footnote">
        <span aria-hidden="true">✳</span> Better trips happen when everyone has a say.
      </div>
    </div>
  )
}
