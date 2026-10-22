import { useState, type FormEvent } from 'react'
import { useAuth } from '../context/useAuth'
import { Notice } from '../components/Notice'

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}

export function AuthPage({ notice }: { notice: string | null }) {
  const { login, register } = useAuth()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const isRegistering = mode === 'register'

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      if (isRegistering) {
        await register({
          full_name: fullName,
          email,
          password,
          ...(phoneNumber ? { phone_number: phoneNumber } : {}),
        })
      } else {
        await login(email, password)
      }
    } catch (submitError) {
      setError(errorMessage(submitError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-intro">
        <div className="brand brand--large">
          <span className="brand-mark" aria-hidden="true">P</span>
          <span>packvote</span>
        </div>
        <div className="auth-copy">
          <span className="eyebrow">A better way to plan together</span>
          <h1>Make the trip <em>everyone</em> wants.</h1>
          <p>Bring your people together, share what matters, and find a plan that feels right for the whole group.</p>
        </div>
        <div className="auth-note">
          <span className="auth-note-icon" aria-hidden="true">✳</span>
          <span>Good trips start with good conversations.</span>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-form-wrap">
          <div className="mobile-brand">
            <div className="brand">
              <span className="brand-mark" aria-hidden="true">P</span>
              <span>packvote</span>
            </div>
          </div>
          <span className="eyebrow">{isRegistering ? 'Create your account' : 'Welcome back'}</span>
          <h2>{isRegistering ? 'Start planning together' : 'Sign in to PackVote'}</h2>
          <p className="muted">
            {isRegistering
              ? 'Create an account to start your next group trip.'
              : 'Your next great group trip is one sign-in away.'}
          </p>

          {notice && <Notice tone="info">{notice}</Notice>}
          {error && <Notice>{error}</Notice>}

          <form className="form-stack" onSubmit={handleSubmit}>
            {isRegistering && (
              <label className="field">
                <span>Full name</span>
                <input
                  autoComplete="name"
                  required
                  minLength={2}
                  maxLength={100}
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Your name"
                />
              </label>
            )}
            <label className="field">
              <span>Email address</span>
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
              />
            </label>
            {isRegistering && (
              <label className="field">
                <span>Phone number <small>Optional</small></span>
                <input
                  type="tel"
                  autoComplete="tel"
                  value={phoneNumber}
                  onChange={(event) => setPhoneNumber(event.target.value)}
                  placeholder="+1 555 0100"
                />
              </label>
            )}
            <label className="field">
              <span>Password</span>
              <input
                type="password"
                autoComplete={isRegistering ? 'new-password' : 'current-password'}
                required
                minLength={isRegistering ? 8 : undefined}
                maxLength={100}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={isRegistering ? 'At least 8 characters' : 'Enter your password'}
              />
            </label>
            <button className="button button--primary button--wide" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Please wait…' : isRegistering ? 'Create account' : 'Sign in'}
              {!isSubmitting && <span aria-hidden="true">→</span>}
            </button>
          </form>

          <p className="auth-toggle">
            {isRegistering ? 'Already planning with us?' : 'New to PackVote?'}{' '}
            <button
              className="text-button"
              type="button"
              onClick={() => {
                setError(null)
                setMode(isRegistering ? 'login' : 'register')
              }}
            >
              {isRegistering ? 'Sign in' : 'Create an account'}
            </button>
          </p>
        </div>
        <p className="auth-legal">By continuing, you agree to plan thoughtfully and travel kindly.</p>
      </section>
    </main>
  )
}
