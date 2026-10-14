import type { UserRole } from '../types/domain'
export const roleRoutes: Record<string, string> = { marketing: '/marketing', communication: '/communication', vigilance: '/vigilance', support: '/support', sales: '/sales' }
export function dashboardForRole(role?: string | null) { return roleRoutes[role ?? ''] ?? '/login' }
export const roleOrder: UserRole[] = ['marketing', 'communication', 'vigilance', 'support', 'sales']
