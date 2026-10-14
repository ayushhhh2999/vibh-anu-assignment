# Vibh-Anu Lead Management System — Implementation Plan

## Scope

Build a production-quality React + TypeScript + Vite frontend for the existing FastAPI lead workflow. The frontend will call the existing backend only, with no mock data, replacement database, invented endpoints, or alternate authentication provider.

## Implementation approach

- **Foundation:** Vite + React + TypeScript, Tailwind CSS, accessible shadcn/ui-style primitives, React Router, TanStack Query, React Hook Form + Zod, and Lucide React.
- **API integration:** one typed `apiClient` module using `VITE_API_BASE_URL`, bearer-token attachment, multipart upload support without manually setting the multipart content type, binary audio handling, FastAPI error parsing, and 401 session recovery.
- **Session:** login through `/api/auth/login`, hydrate the user through `/api/auth/me`, keep the token in session-scoped browser storage with documented XSS limitations, protect routes, derive navigation and landing pages from the server-returned role, and clear query caches on logout.
- **Shared shell:** responsive sidebar/topbar, role-aware navigation, breadcrumbs, profile/logout menu, status badges, toast notifications, skeletons, empty/error states, confirmation dialogs, and consistent form/table/card primitives.
- **Role workflows:** separate dashboard modules for Marketing, Communication, Vigilance, Support, and Sales. All transitions call the corresponding existing backend endpoint and update the UI only after server confirmation.
- **Sales security:** render only backend-returned pre-claim fields; fetch protected audio with the bearer token into a revoked Blob URL; acknowledge playback only from a natural `ended` event; gate claim on successful acknowledgement; handle retries, conflicts, duplicate requests, and post-claim details without leaking restricted fields.
- **Verification:** typecheck/build, inspect route manifest, verify the dev server and preview, and run a read-only requirements trace over the final code. Real end-to-end role testing will require the existing FastAPI backend and seeded passwords, which are not present in this workspace.

## Project structure

```text
src/
  api/                 centralized HTTP client and endpoint functions
  app/                 providers, router, auth/session context
  components/          layout, shared UI, lead and audio components
  features/            auth, marketing, communication, vigilance, support, sales
  lib/                 validation, formatting, role/status helpers
  pages/               route-level dashboard and not-found pages
  types/               API/domain types
public/
  manus-routes.json    complete page route manifest
.env.example           VITE_API_BASE_URL documentation
README.md              setup, API contract assumptions, and token-storage limitations
```

## Design direction

- **Design movement:** quiet enterprise control-room / editorial SaaS: precise information density softened by generous whitespace and restrained motion.
- **Core principles:** role clarity, operational calm, progressive disclosure, and server-truth feedback.
- **Color philosophy:** warm off-white and white surfaces keep long queues readable; ink navy communicates trust; one saturated indigo (`#4F46E5`) owns the brand accent; teal, amber, and rose are reserved for workflow meaning rather than decoration.
- **Layout paradigm:** a persistent left rail plus a broad working canvas. The lead list is the anchor, while the selected lead and action panels slide into the same workspace instead of forcing users through unrelated pages.
- **Signature elements:** an indigo “signal notch” in the Vibh-Anu wordmark, compact workflow rail dots showing department progression, and a small “server confirmed” status line after mutations.
- **Interaction philosophy:** controls explain the next authorized action; disabled workflow actions include the missing prerequisite; destructive or state-changing actions ask for a deliberate confirmation; transitions use a brief fade/slide rather than ornamental animation.
- **Animation:** 150–220ms ease-out for drawers, status updates, and toasts; shimmer only for loading skeletons; no looping motion in operational tables.
- **Typography:** Inter for UI and dense data, with a slightly heavier display weight for page titles; tabular numbers for counts and timestamps; a clear 12/14/16/24/32px hierarchy.
- **Brand essence:** “A calm, accountable handoff system for teams that turn leads into action.” Personality: precise, reassuring, disciplined.
- **Brand voice:** direct and operational. Example lines: “Ready for your next handoff.” and “Playback confirmed by the server. Claim is now available.”
- **Wordmark & logo:** `Vibh-Anu` in a custom typographic lockup with a small indigo signal notch separating the two syllables; use the same notch motif in the compact sidebar mark.
- **Signature brand color:** signal indigo `#4F46E5`, used sparingly for focus, active navigation, primary calls to action, and the workflow rail.

## Delivery workflow

1. After plan approval, create a native/project TODO with concrete acceptance clauses from the specification.
2. Add the package/toolchain policy before the first install, then scaffold the application and configure TypeScript diagnostics.
3. Implement API/session and the shared shell first; then role workflows in lifecycle order; then harden Sales audio/claim behavior.
4. Run typecheck/build and fix actionable diagnostics; verify `manus-routes.json` and the preview origin.
5. Commit the finished project to the managed repository and provide the preview URL, clearly labeled as a preview unless publication is explicitly completed.

## Known integration limitation

No FastAPI service or seeded passwords are available in the current sandbox. The frontend will be wired to the exact documented paths and will fail visibly with backend error details when the API is unavailable; end-to-end authentication and workflow verification must be performed once `VITE_API_BASE_URL` points to the running backend.
