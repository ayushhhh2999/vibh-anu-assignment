import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { roleLabels, statusLabels, type Lead, type UserRole } from '../types/domain'

export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }
export function roleLabel(role?: string | null) { return roleLabels[role ?? ''] ?? 'Workspace' }
export function statusLabel(status?: string | null) { return statusLabels[status ?? ''] ?? status ?? 'Unknown' }
export function formatDate(value?: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(date)
}
export function formatDateTime(value?: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}
export function formatBytes(value?: number | null) {
  if (!value) return '—'
  if (value < 1024 * 1024) return `${Math.round(value / 1024)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}
export function leadName(lead: Lead) { return lead.name?.trim() || `Lead #${lead.id}` }
export function canAccess(role: string | undefined, allowed: UserRole[]) { return !!role && allowed.includes(role as UserRole) }
export function errorMessage(error: unknown, fallback = 'Something went wrong. Please try again.') {
  if (error && typeof error === 'object' && 'message' in error && typeof error.message === 'string') return error.message
  return fallback
}
