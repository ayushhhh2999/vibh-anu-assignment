import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

type Toast = { id: number; kind: 'success' | 'error' | 'info'; message: string }
const ToastContext = createContext<{ push: (kind: Toast['kind'], message: string) => void }>({ push: () => undefined })
export const useToast = () => useContext(ToastContext)

export function AppProviders({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const queryClient = useMemo(() => new QueryClient({ defaultOptions: { queries: { staleTime: 20_000, retry: 1, refetchOnWindowFocus: false } } }), [])
  const push = (kind: Toast['kind'], message: string) => {
    const id = Date.now() + Math.random()
    setToasts((items) => [...items, { id, kind, message }])
    window.setTimeout(() => setToasts((items) => items.filter((item) => item.id !== id)), 4200)
  }
  return <QueryClientProvider client={queryClient}>
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="toast-stack" aria-live="polite">{toasts.map((toast) => <div key={toast.id} className={`toast toast-${toast.kind}`} role="status">{toast.message}</div>)}</div>
    </ToastContext.Provider>
  </QueryClientProvider>
}
