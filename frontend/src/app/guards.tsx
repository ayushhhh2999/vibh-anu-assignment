import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './auth'
import { dashboardForRole } from './routes'
import type { UserRole } from '../types/domain'

export function ProtectedRoute({ role }: { role?: UserRole }) {
  const { isAuthenticated, isLoading, user } = useAuth(); const location = useLocation()
  if (isLoading) return <div className="route-loading"><div className="loading-logo"><span /></div><p>Restoring your secure session…</p></div>
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />
  if (role && user?.role !== role) return <Navigate to={dashboardForRole(user?.role)} replace />
  return <Outlet />
}
