# Vibh-Anu Lead Management System

A role-aware React/Vite frontend for the existing FastAPI API.

## Run locally

```bash
cp .env.example .env
# Set VITE_API_BASE_URL to the running FastAPI backend
pnpm install
pnpm dev
```

The app calls the existing `/api/auth/*` and `/api/leads*` endpoints; it does not seed, mock, or replace backend data. The API must allow the frontend origin through CORS.

## Authentication note

The JWT is kept in `sessionStorage` so it is cleared when the browser tab closes. This limits persistence but does not make the token immune to XSS; keep the backend's token lifetime and browser security controls appropriately configured.

## Supported workflow

Marketing → Communication → Vigilance → Support → Sales → Claimed. Workflow transitions are enabled only after successful backend responses. Sales audio is fetched as an authenticated Blob, and claiming is enabled only after the backend acknowledges a natural audio completion.
