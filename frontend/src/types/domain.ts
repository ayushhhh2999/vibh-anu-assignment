export type UserRole = 'marketing' | 'communication' | 'vigilance' | 'support' | 'sales'
export type LeadStatus = 'communication' | 'vigilance' | 'support' | 'sales' | 'claimed'

export interface User {
  id: number | string
  name?: string | null
  email: string
  role: UserRole | string
}

export interface Lead {
  id: number | string
  name?: string | null
  contact_number?: string | null
  postal_address?: string | null
  meeting_date?: string | null
  meeting_time?: string | null
  remark?: string | null
  status?: LeadStatus | string | null
  created_at?: string | null
  updated_at?: string | null
  audio_available?: boolean | null
  audio_filename?: string | null
  audio_size?: number | null
  claimed_by?: number | string | null
  claimed_by_name?: string | null
  [key: string]: unknown
}

export interface LoginRequest { email: string; password: string }
export interface LoginResponse { access_token: string; token_type?: string }
export interface CommunicationUpdate {
  name?: string
  postal_address?: string
  meeting_date?: string
  meeting_time?: string
  remark?: string
}
export interface ApiErrorBody { detail?: string | Array<{ msg?: string; loc?: unknown }>; message?: string }
export interface ApiError extends Error { status: number; body?: ApiErrorBody }

export const roleLabels: Record<string, string> = {
  marketing: 'Marketing',
  communication: 'Communication',
  vigilance: 'Vigilance',
  support: 'Support',
  sales: 'Sales',
}

export const statusLabels: Record<string, string> = {
  communication: 'Communication',
  vigilance: 'Vigilance',
  support: 'Support',
  sales: 'Ready for sales',
  claimed: 'Claimed',
}
