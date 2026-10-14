import { Bell, ChevronDown, Menu, PanelLeftClose, PanelLeftOpen, ShieldCheck, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../app/auth'
import { roleRoutes } from '../../app/routes'
import { roleLabel } from '../../lib/utils'
import type { UserRole } from '../../types/domain'

const navItems: Array<{ role: UserRole; label: string; icon: string }> = [
  { role: 'marketing', label: 'Marketing desk', icon: '01' },
  { role: 'communication', label: 'Communication', icon: '02' },
  { role: 'vigilance', label: 'Vigilance', icon: '03' },
  { role: 'support', label: 'Support queue', icon: '04' },
  { role: 'sales', label: 'Sales floor', icon: '05' },
]

export function AppShell() {
  const { user, logout } = useAuth(); const location = useLocation(); const navigate = useNavigate(); const [collapsed, setCollapsed] = useState(false); const [mobileOpen, setMobileOpen] = useState(false)
  const currentRole = user?.role as UserRole | undefined
  const currentLabel = navItems.find((item) => location.pathname.startsWith(roleRoutes[item.role]))?.label ?? 'Workspace'
  return <div className={cnShell(collapsed)}>
    {mobileOpen && <button className="mobile-scrim" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
      <div className="brand"><div className="brand-mark"><span /></div>{!collapsed && <div><strong>Vibh-Anu</strong><small>Lead operations</small></div>}<button className="mobile-close" onClick={() => setMobileOpen(false)}><X size={19} /></button></div>
      <div className="rail-label">{!collapsed && 'YOUR WORKSPACE'}</div>
      <nav>{navItems.filter((item) => item.role === currentRole).map((item) => <NavLink key={item.role} to={roleRoutes[item.role]} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'nav-active' : ''}`}><span className="nav-number">{item.icon}</span>{!collapsed && <span>{item.label}</span>}</NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="secure-note"><ShieldCheck size={16} />{!collapsed && <span>Server-truth workflow</span>}</div><button className="collapse-button" onClick={() => setCollapsed((value) => !value)}>{collapsed ? <PanelLeftOpen size={18} /> : <><PanelLeftClose size={18} /><span>Collapse rail</span></>}</button></div>
    </aside>
    <main className="main-shell"><header className="topbar"><button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20} /></button><div className="crumbs"><span>Workspace</span><b>/</b><strong>{currentLabel}</strong></div><div className="top-actions"><button className="notification-button" aria-label="Notifications"><Bell size={18} /><i /></button><div className="profile"><div className="profile-avatar">{(user?.name?.[0] ?? user?.email?.[0] ?? 'U').toUpperCase()}</div><div className="profile-copy"><strong>{user?.name || user?.email?.split('@')[0] || 'User'}</strong><span>{roleLabel(user?.role)}</span></div><button className="profile-menu" onClick={() => { logout(); navigate('/login') }} title="Sign out"><ChevronDown size={16} /></button></div></div></header><div className="content-wrap"><Outlet /></div></main>
  </div>
}
function cnShell(collapsed: boolean) { return `app-shell ${collapsed ? 'shell-collapsed' : ''}` }
