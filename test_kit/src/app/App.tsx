import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import { dashboardForRole } from './routes'
import { ProtectedRoute } from './guards'
import { AppShell } from '../components/layout/AppShell'
import { LoginPage } from '../features/auth/LoginPage'
import { MarketingPage } from '../features/marketing/MarketingPage'
import { CommunicationPage } from '../features/communication/CommunicationPage'
import { VigilancePage } from '../features/vigilance/VigilancePage'
import { SupportPage } from '../features/support/SupportPage'
import { SalesPage } from '../features/sales/SalesPage'
import { NotFoundPage } from '../pages/NotFoundPage'

function HomeRedirect() { const { user } = useAuth(); return <Navigate to={dashboardForRole(user?.role)} replace /> }
export function App() { return <Routes><Route path="/login" element={<LoginPage />} /><Route element={<ProtectedRoute />}><Route element={<AppShell />}><Route path="/" element={<HomeRedirect />} /><Route element={<ProtectedRoute role="marketing" />}><Route path="/marketing" element={<MarketingPage />} /></Route><Route element={<ProtectedRoute role="communication" />}><Route path="/communication" element={<CommunicationPage />} /></Route><Route element={<ProtectedRoute role="vigilance" />}><Route path="/vigilance" element={<VigilancePage />} /></Route><Route element={<ProtectedRoute role="support" />}><Route path="/support" element={<SupportPage />} /></Route><Route element={<ProtectedRoute role="sales" />}><Route path="/sales" element={<SalesPage />} /></Route></Route></Route><Route path="*" element={<NotFoundPage />} /></Routes> }
