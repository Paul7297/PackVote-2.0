import { useState } from 'react'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/useAuth'
import { LoadingState } from './components/LoadingState'
import { AuthPage } from './pages/AuthPage'
import { DashboardPage } from './pages/DashboardPage'
import { TripDetailsPage } from './pages/TripDetailsPage'
import type { Trip } from './types/models'
import './App.css'

function Brand() {
  return (
    <div className="brand" aria-label="PackVote">
      <span className="brand-mark" aria-hidden="true">P</span>
      <span>packvote</span>
    </div>
  )
}

function Workspace() {
  const { user, isInitializing, sessionNotice, logout } = useAuth()
  const [selectedTripId, setSelectedTripId] = useState<string | null>(null)

  if (isInitializing) {
    return <LoadingState />
  }

  if (!user) {
    return <AuthPage notice={sessionNotice} />
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Brand />
          <div className="topbar-right">
            <span className="workspace-label"><span className="workspace-indicator" /> Your travel workspace</span>
            <span className="topbar-divider" />
            <span className="user-greeting">Hey, {user.full_name.split(' ')[0]}</span>
            <span className="user-avatar" aria-hidden="true">
              {user.full_name.trim().charAt(0).toUpperCase()}
            </span>
            <button className="signout-button" type="button" onClick={() => {
              setSelectedTripId(null)
              logout()
            }}>
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="workspace-main">
        {selectedTripId ? (
          <TripDetailsPage
            key={selectedTripId}
            tripId={selectedTripId}
            user={user}
            onBack={() => setSelectedTripId(null)}
          />
        ) : (
          <DashboardPage
            onOpenTrip={(trip: Trip) => setSelectedTripId(trip.id)}
          />
        )}
      </main>
      <footer className="app-footer">
        <Brand />
        <span>Better trips happen when everyone has a say.</span>
        <span className="footer-spark" aria-hidden="true">✳</span>
      </footer>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <Workspace />
    </AuthProvider>
  )
}

export default App
