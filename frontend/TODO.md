# Vibh-Anu implementation outcomes

## Authentication and role-aware application shell

- Submit credentials to the existing login endpoint, read its actual response shape, store and attach the JWT according to the backend contract, fetch the authenticated profile, route to the correct departmental dashboard, protect authenticated routes, handle expired/invalid tokens, clear authentication state on logout, redirect unauthenticated users to login, and prevent manual access to another role's dashboard.
- Provide a responsive collapsible sidebar, top navigation, Vibh-Anu branding, current user's name and role, profile/logout actions, breadcrumbs, page titles/descriptions, toast messages, loading/error/empty states, and navigation controls determined by the authenticated role.

## Marketing workflow

- Marketing can create leads through the real API with validated customer name (2–100 characters) and contact number (7–20 characters), see only backend-visible leads created by the authenticated Marketing user, search only where permitted, refresh, see API-derived summaries, and see a success toast only after server confirmation.

## Communication workflow

- Communication can edit only lead name, postal address, meeting date, meeting time, and remark; contact number is read-only, status has no direct UI control, required address/date/time validation is clear, incomplete leads cannot be submitted from the UI, PATCH and submit use the real endpoints, and successful submission refetches the queue.

## Vigilance workflow

- Vigilance can upload supported backend-configured audio through multipart form data using the expected field name, enforce the 20 MB limit and readable type/size errors, show file metadata and request feedback, never manually set multipart Content-Type, and call verification only after upload success. Successful verification refetches the queue.

## Support workflow

- Support sees its queue and details, including meeting information and audio availability, has a clear checklist for address/date/time/audio prerequisites, calls the actual allocation endpoint, displays server errors, refetches after allocation, and has no Sales-only playback, acknowledgement, or claim controls.

## Sales playback and claim workflow

- Before claim, show only the backend-permitted summary fields and never reveal contact number, address, meeting date/time, or remark. Fetch protected audio with the user's bearer token as binary data, create and revoke object URLs, and provide accessible loading, error, playback, progress, duration, and volume controls.
- A natural audio ended event calls the playback-completion endpoint once for the attempt; pausing, seeking to the end, or pressing Play alone does not count. Claim remains disabled until a successful server acknowledgement, supports a safe retry after acknowledgement failure, prevents duplicate claims, handles backend conflicts with a refresh, and reveals full details only after a successful claim.

## Integration, security, and quality

- Use exact workflow statuses and real documented endpoints, centralize FastAPI errors for 400/401/403/404/409/413/422, display safe backend detail messages, do not invent APIs or fake successful responses, do not log credentials/tokens/sensitive data, do not expose filesystem paths, clear user-specific query caches on logout, configure the API URL via VITE_API_BASE_URL, and document token-storage limitations.
- Keep the route manifest synchronized, typecheck and build successfully, and verify the preview. End-to-end role testing remains dependent on the running FastAPI backend and seeded passwords.
