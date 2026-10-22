import { useState, type FormEvent } from 'react'
import {
  createPreference,
  updatePreference,
} from '../api/preferences'
import { Notice } from './Notice'
import type {
  AccommodationPref,
  Activity,
  BudgetRange,
  ClimatePreference,
  FoodPref,
  TravelPriority,
  TravelStyle,
  TransportPref,
  TripPreference,
  TripPreferenceInput,
} from '../types/models'

const budgetOptions: { value: BudgetRange; label: string }[] = [
  { value: '5k_10k', label: '5k–10k' },
  { value: '10k_20k', label: '10k–20k' },
  { value: '20k_40k', label: '20k–40k' },
  { value: '40k_plus', label: '40k+' },
]
const climateOptions: { value: ClimatePreference; label: string }[] = [
  { value: 'cold', label: 'Cool & crisp' },
  { value: 'moderate', label: 'Mild & moderate' },
  { value: 'warm', label: 'Sunny & warm' },
  { value: 'no_preference', label: 'No preference' },
]
const accommodationOptions: { value: AccommodationPref; label: string }[] = [
  { value: 'budget', label: 'Keep it simple' },
  { value: 'mid', label: 'A little comfort' },
  { value: 'luxury', label: 'Treat ourselves' },
]
const transportOptions: { value: TransportPref; label: string }[] = [
  { value: 'flight', label: 'Flight' },
  { value: 'train', label: 'Train' },
  { value: 'bus', label: 'Bus' },
  { value: 'car', label: 'Car' },
]
const foodOptions: { value: FoodPref; label: string }[] = [
  { value: 'veg', label: 'Vegetarian' },
  { value: 'non_veg', label: 'No restrictions' },
  { value: 'vegan', label: 'Vegan' },
  { value: 'no_preference', label: 'No preference' },
]
const priorityOptions: { value: TravelPriority; label: string }[] = [
  { value: 'cheapest', label: 'Keep costs low' },
  { value: 'balanced', label: 'A good balance' },
  { value: 'comfort', label: 'Comfort first' },
  { value: 'experience', label: 'Memorable experiences' },
]
const travelStyles: { value: TravelStyle; label: string }[] = [
  { value: 'adventure', label: 'Adventure' },
  { value: 'nature', label: 'Nature' },
  { value: 'relaxation', label: 'Relaxation' },
  { value: 'cultural', label: 'Culture' },
  { value: 'nightlife', label: 'Nightlife' },
  { value: 'food', label: 'Food' },
]
const activities: { value: Activity; label: string }[] = [
  { value: 'trekking', label: 'Trekking' },
  { value: 'beach', label: 'Beach days' },
  { value: 'historical_places', label: 'Historic places' },
  { value: 'shopping', label: 'Shopping' },
  { value: 'local_food', label: 'Local food' },
  { value: 'camping', label: 'Camping' },
  { value: 'sightseeing', label: 'Sightseeing' },
  { value: 'water_sports', label: 'Water sports' },
  { value: 'wildlife', label: 'Wildlife' },
  { value: 'photography', label: 'Photography' },
  { value: 'nightlife', label: 'Nightlife' },
  { value: 'spa_wellness', label: 'Spa & wellness' },
]

type PreferenceFormValues = TripPreferenceInput

function defaultValues(preference: TripPreference | null): PreferenceFormValues {
  return {
    budget_range: preference?.budget_range ?? '10k_20k',
    travel_style: preference?.travel_style ?? [],
    preferred_activities: preference?.preferred_activities ?? [],
    climate_preference: preference?.climate_preference ?? 'no_preference',
    accommodation_pref: preference?.accommodation_pref ?? 'mid',
    transport_pref: preference?.transport_pref ?? 'flight',
    food_pref: preference?.food_pref ?? 'no_preference',
    travel_priority: preference?.travel_priority ?? 'balanced',
    notes: preference?.notes ?? '',
  }
}

function toggleValue<T extends string>(values: T[], value: T): T[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value]
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Could not save your preferences.'
}

export function PreferenceForm({
  tripId,
  preference,
  onSaved,
  readOnly = false,
}: {
  tripId: string
  preference: TripPreference | null
  onSaved: (saved: TripPreference) => void
  readOnly?: boolean
}) {
  const [values, setValues] = useState<PreferenceFormValues>(() => defaultValues(preference))
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  function setValue<K extends keyof PreferenceFormValues>(
    key: K,
    value: PreferenceFormValues[K],
  ) {
    setSuccess(false)
    setValues((current) => ({ ...current, [key]: value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSuccess(false)

    if (values.travel_style.length === 0 || values.preferred_activities.length === 0) {
      setError('Choose at least one travel style and one activity.')
      return
    }

    setIsSubmitting(true)
    try {
      const saved = preference
        ? await updatePreference(tripId, values)
        : await createPreference(tripId, values)
      onSaved(saved)
      setSuccess(true)
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form className="form-stack preference-form" onSubmit={handleSubmit}>
      <p className="form-intro">A few quick picks help your group plan a trip that works for everyone.</p>
      {error && <Notice>{error}</Notice>}
      {success && (
        <Notice tone="success">
          Preferences saved. You can update them anytime.
        </Notice>
      )}

      <label className="field">
        <span>Budget range</span>
        <select
          disabled={readOnly}
          value={values.budget_range}
          onChange={(event) => setValue('budget_range', event.target.value as BudgetRange)}
        >
          {budgetOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </label>

      <fieldset disabled={readOnly} className="choice-fieldset">
        <legend>What kind of trip sounds good? <small>Choose at least one</small></legend>
        <div className="choice-grid">
          {travelStyles.map((style) => (
            <label className="choice-chip" key={style.value}>
              <input
                type="checkbox"
                checked={values.travel_style.includes(style.value)}
                onChange={() => setValue('travel_style', toggleValue(values.travel_style, style.value))}
              />
              <span>{style.label}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset disabled={readOnly} className="choice-fieldset">
        <legend>What would you love to do? <small>Choose at least one</small></legend>
        <div className="choice-grid">
          {activities.map((activity) => (
            <label className="choice-chip" key={activity.value}>
              <input
                type="checkbox"
                checked={values.preferred_activities.includes(activity.value)}
                onChange={() => setValue(
                  'preferred_activities',
                  toggleValue(values.preferred_activities, activity.value),
                )}
              />
              <span>{activity.label}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="form-row">
        <label className="field">
          <span>Climate</span>
          <select
            disabled={readOnly}
            value={values.climate_preference}
            onChange={(event) => setValue('climate_preference', event.target.value as ClimatePreference)}
          >
            {climateOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        <label className="field">
          <span>Stay style</span>
          <select
            disabled={readOnly}
            value={values.accommodation_pref}
            onChange={(event) => setValue('accommodation_pref', event.target.value as AccommodationPref)}
          >
            {accommodationOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
      </div>

      <div className="form-row">
        <label className="field">
          <span>Getting around</span>
          <select
            disabled={readOnly}
            value={values.transport_pref}
            onChange={(event) => setValue('transport_pref', event.target.value as TransportPref)}
          >
            {transportOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        <label className="field">
          <span>Food preference</span>
          <select
            disabled={readOnly}
            value={values.food_pref}
            onChange={(event) => setValue('food_pref', event.target.value as FoodPref)}
          >
            {foodOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
      </div>

      <label className="field">
        <span>What matters most?</span>
        <select
          value={values.travel_priority}
          onChange={(event) => setValue('travel_priority', event.target.value as TravelPriority)}
        >
          {priorityOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </label>

      <label className="field">
        <span>Anything else? <small>Optional</small></span>
        <textarea
          disabled={readOnly}
          name="notes"
          rows={3}
          maxLength={1000}
          value={values.notes ?? ''}
          onChange={(event) => setValue('notes', event.target.value)}
          placeholder="A note for the trip organizer…"
        />
      </label>

      <button className="button button--primary" type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Saving preferences…' : preference ? 'Save changes' : 'Submit preferences'}
        {!isSubmitting && <span aria-hidden="true">→</span>}
      </button>
    </form>
  )
}
