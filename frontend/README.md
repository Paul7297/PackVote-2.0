# PackVote frontend

React 19 + TypeScript + Vite client for the PackVote authentication, trips, members, and preferences MVP.

## Local development

1. Start the PackVote FastAPI backend.
2. Copy `.env.example` to `.env.local` and set `VITE_API_BASE_URL` to the backend origin (for example, `http://localhost:8000`).
3. Install packages with `npm ci`, then run `npm run dev`.

The frontend uses the browser's in-memory state for the access token and `sessionStorage` for the refresh token. Do not put tokens, passwords, or the Geoapify API key in Vite environment variables; `VITE_*` values are public in the built client.

## Current scope

- Register/login, refresh-based session restoration, and logout.
- Trip dashboard, trip creation/details, invitations, and member status.
- Preference submission/editing and group completion status.

Trip details include destination search/selection/confirmation, organizer candidate management, and voting/results, wired to the separately verified backend contract. The backend route modules are not present in this frontend worktree, so configure `VITE_API_BASE_URL` to the backend instance that provides those routes. Do not point this build at the stale backend checkout that only exposes auth, trips, users, and preferences.

Live travel data, ML, LLM, and RAG are not part of this frontend phase.

## Checks

Run `npm run lint` and `npm run build`.
