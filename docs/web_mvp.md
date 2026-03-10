# Web MVP

This document defines the first web milestone for Jarvis without replacing the current local-first file persistence.

## Objective
- Expose the current Jarvis flows through a browser-friendly interface.
- Keep the existing CLI and file contracts working.
- Allow responsive use on desktop and mobile browsers.
- Create a safe bridge toward a future hosted frontend and dedicated backend deployment.

## Phase 1 Scope
- FastAPI application under `app/` that reuses the existing Python memory and reminder engine.
- Static responsive frontend under `frontend/`.
- Read and write operations continue using:
  - `memory_log.md`
  - `memory_map.md`
  - `reminders.json`
  - `WORKING_CONTEXT.md`
- Supported browser flows:
  - execute all core actions from one prompt input
  - create log entry
  - create reminder
  - mark reminder as completed
  - search historical records
  - view today's entries
  - view working context
- Performance safeguards:
  - working context reads do not force implicit rewrites
  - active log can be rotated into `archives/` when threshold is exceeded
  - search includes active and archived log slices

## Out Of Scope For Phase 1
- Authentication
- Multi-user support
- Hosted database migration
- Push notifications
- Production hardening for internet exposure
- Background jobs outside the current reminder model

## Initial API Surface
- `GET /health`
- `GET /api/overview`
- `GET /api/today`
- `GET /api/context`
- `GET /api/search?q=<term>`
- `GET /api/reminders`
- `POST /api/log`
- `POST /api/talk`
- `POST /api/reminders`
- `POST /api/reminders/{id}/complete`

## Mobile Expectation
- The frontend must remain usable in a phone browser without depending on desktop-only controls.
- The same API should serve both desktop and mobile clients.

## Deployment Direction
- Short term: run locally with `uvicorn app.main:app`.
- Future hosted path:
  - frontend can move to Netlify
  - backend must be deployed on a Python-capable service
  - file-based persistence should later migrate to a durable data store before public hosting

## Online Test Path
- Backend:
  - Use `render.yaml` for a fast Render deployment.
  - Validate `GET /health` after deploy.
  - Configure `JARVIS_CORS_ORIGINS` according to the frontend origin.
- Frontend:
  - Publish `frontend/` on Netlify (configured in `netlify.toml`).
  - In the hero section, define `URL da API` and run `Testar conexao`.
  - The URL is persisted in browser `localStorage` for subsequent sessions.

## Hosted Risk Notes
- Current persistence remains file-based and local-first by design.
- Hosted instances may lose state if the platform filesystem is not durable.
- This is acceptable for smoke testing only; durable production requires a database migration.

## Migration Principle
- Phase 1 is an interface layer, not a storage rewrite.
- Any future database migration must preserve the current user-visible behaviors first, then replace internal persistence behind stable API contracts.
