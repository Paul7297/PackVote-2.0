import { useState, type FormEvent } from 'react'
import { createTrip } from '../api/trips'
import { Notice } from './Notice'
import type { TravelerType, Trip } from '../types/models'

const travelerTypes: { value: TravelerType; label: string }[] = [
  { value: 'solo', label: 'Solo' },
  { value: 'couple', label: 'Couple' },
  { value: 'family', label: 'Family' },
  { value: 'friends', label: 'Friends' },
]

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Could not create the trip.'
}

export function TripCreateForm({ onCreated, onCancel }: {
  onCreated: (trip: Trip) => void
  onCancel: () => void
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [budgetMin, setBudgetMin] = useState('')
  const [budgetMax, setBudgetMax] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [travelerType, setTravelerType] = useState<TravelerType | ''>('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (budgetMin && budgetMax && Number(budgetMax) < Number(budgetMin)) {
      setError('Maximum budget must be at least the minimum budget.')
      return
    }
    if (startDate && endDate && endDate < startDate) {
      setError('End date must be on or after the start date.')
      return
    }

    setIsSubmitting(true)
    try {
      const trip = await createTrip({
        name: name.trim(),
        description: description.trim() || null,
        budget_min: budgetMin ? Number(budgetMin) : null,
        budget_max: budgetMax ? Number(budgetMax) : null,
        start_date: startDate || null,
        end_date: endDate || null,
        traveler_type: travelerType || null,
      })
      onCreated(trip)
    } catch (createError) {
      setError(errorMessage(createError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="panel create-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">A new adventure</span>
          <h2>Create a trip</h2>
        </div>
        <button className="icon-button" type="button" onClick={onCancel} aria-label="Close trip form">×</button>
      </div>
      {error && <Notice>{error}</Notice>}
      <form className="form-stack" onSubmit={handleSubmit}>
        <label className="field">
          <span>Trip name</span>
          <input
            required
            minLength={2}
            maxLength={100}
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Summer in the mountains"
          />
        </label>
        <label className="field">
          <span>Description <small>Optional</small></span>
          <textarea
            rows={3}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="What are you dreaming up?"
          />
        </label>
        <div className="form-row">
          <label className="field">
            <span>Minimum budget</span>
            <input
              type="number"
              min="0"
              step="1"
              value={budgetMin}
              onChange={(event) => setBudgetMin(event.target.value)}
              placeholder="0"
            />
          </label>
          <label className="field">
            <span>Maximum budget</span>
            <input
              type="number"
              min="0"
              step="1"
              value={budgetMax}
              onChange={(event) => setBudgetMax(event.target.value)}
              placeholder="0"
            />
          </label>
        </div>
        <div className="form-row">
          <label className="field">
            <span>Start date</span>
            <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </label>
          <label className="field">
            <span>End date</span>
            <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          </label>
        </div>
        <label className="field">
          <span>Travel group</span>
          <select
            value={travelerType}
            onChange={(event) => setTravelerType(event.target.value as TravelerType | '')}
          >
            <option value="">Choose a group type</option>
            {travelerTypes.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
          </select>
        </label>
        <div className="form-actions">
          <button className="button button--quiet" type="button" onClick={onCancel}>Cancel</button>
          <button className="button button--primary" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating…' : 'Create trip'} <span aria-hidden="true">→</span>
          </button>
        </div>
      </form>
    </section>
  )
}
