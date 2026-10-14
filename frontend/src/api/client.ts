import type { ApiErrorBody, CommunicationUpdate, Lead, LoginRequest, LoginResponse, User } from '../types/domain'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined
const API_BASE_URL = (configuredBaseUrl || (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '')).replace(/\/$/, '')
const TOKEN_KEY = 'vibhanu_access_token'
const unauthorizedListeners = new Set<() => void>()

export const authStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
}
export function onUnauthorized(listener: () => void) { unauthorizedListeners.add(listener); return () => unauthorizedListeners.delete(listener) }

function sanitizeDetail(detail: string) { return detail.replace(/(?:[A-Za-z]:)?\/(?:[\w.\-]+\/)*[\w.\-]+/g, '[redacted path]').replace(/\b(?:token|password|secret)\b\s*[:=]\s*[^\s,;]+/gi, '$1: [redacted]') }
function readableDetail(body: ApiErrorBody | null, status: number) {
  if (typeof body?.detail === 'string') return sanitizeDetail(body.detail)
  if (Array.isArray(body?.detail)) return body.detail.map((item) => item.msg).filter(Boolean).join(', ') || `Request failed (${status})`
  if (typeof body?.message === 'string') return sanitizeDetail(body.message)
  const fallback: Record<number, string> = { 400: 'The backend rejected this workflow action.', 401: 'Your session has expired. Please sign in again.', 403: 'You are not authorized for this action.', 404: 'The requested lead was not found.', 409: 'This lead changed state. Refresh and try again.', 413: 'The upload is too large.', 422: 'Please check the submitted fields.' }
  return fallback[status] || `Request failed (${status})`
}
async function parseBody(response: Response): Promise<ApiErrorBody | null> { const text = await response.text(); if (!text) return null; try { return JSON.parse(text) as ApiErrorBody } catch { return { detail: text } } }
async function request<T>(path: string, init: RequestInit = {}, options: { auth?: boolean; binary?: boolean } = {}): Promise<T> {
  if (!API_BASE_URL) throw new Error('VITE_API_BASE_URL is not configured for this build.')
  const headers = new Headers(init.headers)
  if (!(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (options.auth !== false) { const token = authStore.get(); if (token) headers.set('Authorization', `Bearer ${token}`) }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  if (!response.ok) { const body = await parseBody(response); const error = new Error(readableDetail(body, response.status)) as import('../types/domain').ApiError; error.status = response.status; error.body = body ?? undefined; if (response.status === 401) { authStore.clear(); unauthorizedListeners.forEach((listener) => listener()) } throw error }
  if (options.binary) return (await response.blob()) as T
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
export const api = {
  login: (payload: LoginRequest) => request<LoginResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) }, { auth: false }),
  me: () => request<User>('/api/auth/me'),
  listLeads: () => request<Lead[] | { leads?: Lead[] }>('/api/leads'),
  createLead: (payload: { name: string; contact_number: string }) => request<Lead>('/api/leads', { method: 'POST', body: JSON.stringify(payload) }),
  updateCommunication: (id: number | string, payload: CommunicationUpdate) => request<Lead>(`/api/leads/${id}/communication`, { method: 'PATCH', body: JSON.stringify(payload) }),
  submitCommunication: (id: number | string) => request<Lead>(`/api/leads/${id}/communication/submit`, { method: 'POST' }),
  uploadAudio: (id: number | string, file: File) => { const body = new FormData(); body.append('file', file); return request<Lead>(`/api/leads/${id}/vigilance/audio`, { method: 'POST', body }) },
  verifyAudio: (id: number | string) => request<Lead>(`/api/leads/${id}/vigilance/verify`, { method: 'POST' }),
  allocateLead: (id: number | string) => request<Lead>(`/api/leads/${id}/support/allocate`, { method: 'POST' }),
  salesAudio: (id: number | string) => request<Blob>(`/api/leads/${id}/sales/audio`, {}, { binary: true }),
  playbackComplete: (id: number | string) => request<unknown>(`/api/leads/${id}/sales/playback-complete`, { method: 'POST' }),
  claimLead: async (id: number | string) => (await request<{ lead: Lead }>(`/api/leads/${id}/sales/claim`, { method: 'POST' })).lead,
}
export function normalizeLeads(data: Lead[] | { leads?: Lead[] }): Lead[] { return Array.isArray(data) ? data : data.leads ?? [] }
export { API_BASE_URL }
