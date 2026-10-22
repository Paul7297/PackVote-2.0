import { useEffect, useState, type FormEvent } from 'react'
import { getMyPreference, getPreferenceStatus } from '../api/preferences'
import {
  getTrip,
  inviteMember,
  listTripMembers,
  removeTripMember,
} from '../api/trips'
import { LoadingState } from '../components/LoadingState'
import { Notice } from '../components/Notice'
import { PreferenceForm } from '../components/PreferenceForm'
import { DestinationPlanningPanel } from '../components/DestinationPlanningPanel'
import type {
  PreferenceCompletionStatus,
  Trip,
  TripMember,
  TripPreference,
  User,
} from '../types/models'

function formatDate(date: string | null): string {
  if (!date) {
    return 'To be decided'
  }
  return new Intl.DateTimeFormat(undefined, { month: 'long', day: 'numeric', year: 'numeric' })
    .format(new Date(`${date}T12:00:00`))
}

function formatAmount(amount: number | null): string {
  return amount === null ? 'Flexible' : new Intl.NumberFormat().format(amount)
}

function humanize(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function TripDetailsPage({
  tripId,
  user,
  onBack,
}: {
  tripId: string
  user: User
  onBack: () => void
}) {
  const [trip, setTrip] = useState<Trip | null>(null)
  const [members, setMembers] = useState<TripMember[]>([])
  const [preference, setPreference] = useState<TripPreference | null>(null)
  const [completion, setCompletion] = useState<PreferenceCompletionStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteMessage, setInviteMessage] = useState<string | null>(null)
  const [isInviting, setIsInviting] = useState(false)
  const [isRemovingMember, setIsRemovingMember] = useState<string | null>(null)
  const [memberMessage, setMemberMessage] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    void Promise.all([
      getTrip(tripId),
      listTripMembers(tripId),
      getMyPreference(tripId),
      getPreferenceStatus(tripId),
    ])
      .then(([tripData, memberData, preferenceData, completionData]) => {
        if (active) {
          setTrip(tripData)
          setMembers(memberData)
          setPreference(preferenceData)
          setCompletion(completionData)
        }
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : 'Could not load this trip.')
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
  }, [tripId])
  useEffect(() => {
    let active = true;
    let refreshing = false;

    async function refreshMembers() {
      if (refreshing) return;

      refreshing = true;

      try {
        const latestMembers = await listTripMembers(tripId);

        if (!active) return;

        setMembers(latestMembers);
      } catch {
        // Keep the existing member list if a background refresh fails.
      } finally {
        refreshing = false;
      }
    }

    const intervalId = window.setInterval(() => {
      void refreshMembers();
    }, 5000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, [tripId]);

async function handleRemoveMember(member: TripMember) {
  if (!trip || !isOrganizer) return

  const confirmed = window.confirm(
    `Remove this member from "${trip.name}"? They will lose access to this trip.`,
  )

  if (!confirmed) return

  setError(null)
  setMemberMessage(null)
  setIsRemovingMember(member.user_id)

  try {
    await removeTripMember(tripId, member.user_id)

    const updatedMembers = await listTripMembers(tripId)
    setMembers(updatedMembers)
    setMemberMessage('Member removed from the trip.')
  } catch (removeError: unknown) {
    setError(
      removeError instanceof Error
        ? removeError.message
        : 'Could not remove this member.',
    )
  } finally {
    setIsRemovingMember(null)
  }
}

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setInviteMessage(null)
    setError(null)
    setIsInviting(true)
    try {
      const member = await inviteMember(tripId, inviteEmail.trim())
      setInviteEmail('')
      setInviteMessage(`Invitation created for member ${member.user_id}.`)
      const updatedMembers = await listTripMembers(tripId)
      setMembers(updatedMembers)
    } catch (inviteError) {
      setError(inviteError instanceof Error ? inviteError.message : 'Could not invite this member.')
    } finally {
      setIsInviting(false)
    }
  }

  function handlePreferenceSaved(saved: TripPreference) {
    setPreference(saved)
    void getPreferenceStatus(tripId)
      .then(setCompletion)
      .catch((statusError: unknown) => {
        setError(statusError instanceof Error ? statusError.message : 'Could not update preference status.')
      })
  }

  if (isLoading) {
    return <LoadingState label="Opening your trip…" />
  }
  if (!trip) {
    return (
      <div className="page-state">
        <button className="button button--quiet" type="button" onClick={onBack}>← Back to trips</button>
        {error && <Notice>{error}</Notice>}
      </div>
    )
  }

  const isOrganizer = trip.organizer_id === user.id
  const joinedMembers = members.filter((member) => member.status === 'joined')
  const ownMembership = members.find((member) => member.user_id === user.id)
  const completionPercent = completion && completion.total > 0
    ? Math.min(100, completion.submitted / completion.total * 100)
    : 0

  return (
    <div className="trip-details-page">
      <button className="back-link" type="button" onClick={onBack}>
        <span aria-hidden="true">←</span> All trips
      </button>
      {error && <Notice>{error}</Notice>}

      <section className="trip-detail-hero">
        <div className="trip-detail-art" aria-hidden="true">
          <div className="detail-art-sun" />
          <div className="detail-art-mountain detail-art-mountain--one" />
          <div className="detail-art-mountain detail-art-mountain--two" />
          <span className="detail-art-caption">THE GOOD<br />STUFF STARTS HERE</span>
        </div>
        <div className="trip-detail-heading">
          <span className="eyebrow">Trip workspace <span className={`status-pill status-pill--${trip.status}`}>{humanize(trip.status)}</span></span>
          <h1>{trip.name}</h1>
          <p>{trip.description || 'A little space for the group to start planning.'}</p>
          <div className="trip-detail-meta">
            <span><span aria-hidden="true">◷</span> {formatDate(trip.start_date)}{trip.end_date ? ` – ${formatDate(trip.end_date)}` : ''}</span>
            <span><span aria-hidden="true">◇</span> {humanize(trip.traveler_type ?? 'group type not set')}</span>
          </div>
        </div>
      </section>

      <DestinationPlanningPanel
        readOnly={trip?.archived_at != null}
        tripId={tripId}
        tripStatus={trip.status}
        isOrganizer={isOrganizer}
        onTripUpdated={async () => {
          setTrip(await getTrip(tripId))
        }}
      />

      <div className="trip-content-grid">
        <div className="trip-main-column">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">The people coming along</span>
                <h2>Your trip crew <span className="heading-count">{joinedMembers.length}</span></h2>
              </div>
              {ownMembership && <span className={`role-tag role-tag--${ownMembership.role}`}>{humanize(ownMembership.role)}</span>}
            </div>
            <div className="member-list">
              {members.length === 0 ? (
                <p className="muted">No member details are available for this trip yet.</p>
              ) : members.map((member) => (
                <div className="member-row" key={member.id}>
                  <span className="member-avatar" aria-hidden="true">{member.role === 'organizer' ? '✳' : '•'}</span>
                  <div className="member-info">
                    <strong>{member.role === 'organizer' ? 'Trip organizer' : 'Member'}</strong>
                    <span className="member-id">ID · {member.user_id}</span>
                  </div>
                  <div className="member-tags">
                    <span className={`member-status member-status--${member.status}`}>{humanize(member.status)}</span>
                    <span className="member-role">{humanize(member.role)}</span>
                  </div>
                    {isOrganizer &&
                      member.user_id !== user.id &&
                      (member.status === 'invited' || member.status === 'joined') && (
                        <button
                          className="button button--quiet button--small"
                          type="button"
                          disabled={isRemovingMember === member.user_id}
                          onClick={() => void handleRemoveMember(member)}
                        >
                          {isRemovingMember === member.user_id ? 'Removing…' : 'Remove'}
                        </button>
                      )}
                </div>
              ))}
            </div>
            {isOrganizer && (
              <form className="invite-form" onSubmit={handleInvite}>
                <div>
                  <label className="field" htmlFor="invite-email">
                    <span>Invite someone by email</span>
                    <input
                      id="invite-email"
                      type="email"
                      required
                      value={inviteEmail}
                      onChange={(event) => setInviteEmail(event.target.value)}
                      placeholder="friend@example.com"
                    />
                  </label>
                </div>
                <button className="button button--outline" type="submit" disabled={isInviting}>
                  {isInviting ? 'Sending…' : 'Send invite'} <span aria-hidden="true">→</span>
                </button>
              </form>
            )}
            {inviteMessage && <Notice tone="success">{inviteMessage}</Notice>}
            {memberMessage && <Notice tone="success">{memberMessage}</Notice>}
          </section>

          <section className="panel preference-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">Make room for everyone</span>
                <h2>Your travel preferences</h2>
              </div>
              <span className={`completion-badge ${preference ? 'completion-badge--done' : ''}`}>
                {preference ? 'Submitted' : 'Not submitted'}
              </span>
            </div>
            <PreferenceForm
              tripId={tripId}
              preference={preference}
              onSaved={handlePreferenceSaved}
              readOnly={trip?.archived_at != null}
            />
          </section>
        </div>

        <aside className="trip-side-column">
          <section className="panel trip-summary">
            <span className="eyebrow">A few trip details</span>
            <h2>At a glance</h2>
            <dl className="summary-list">
              <div>
                <dt>Budget per person</dt>
                <dd>{formatAmount(trip.budget_min)} – {formatAmount(trip.budget_max)}</dd>
              </div>
              <div>
                <dt>Trip dates</dt>
                <dd>{formatDate(trip.start_date)}{trip.end_date ? ` – ${formatDate(trip.end_date)}` : ''}</dd>
              </div>
              <div>
                <dt>Travel group</dt>
                <dd>{humanize(trip.traveler_type ?? 'Not set')}</dd>
              </div>
            </dl>
          </section>

          <section className="panel progress-panel">
            <div className="progress-icon" aria-hidden="true">✳</div>
            <span className="eyebrow">Getting everyone on the same page</span>
            <h2>Preference check-in</h2>
            {completion ? (
              <>
                <p>{completion.submitted} of {completion.total} joined members have shared their preferences.</p>
                <div
                  className="progress-track"
                  role="progressbar"
                  aria-label="Trip preference completion"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Math.round(completionPercent)}
                >
                  <span style={{ width: `${completionPercent}%` }} />
                </div>
                <span className="progress-caption">
                  {completion.complete ? 'Everyone has checked in. Nice!' : 'A little more input makes a better plan.'}
                </span>
              </>
            ) : (
              <p>Preference progress is not available right now.</p>
            )}
          </section>
        </aside>
      </div>
    </div>
  )
}
