import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, authStore, onUnauthorized } from '../api/client'
import type { User } from '../types/domain'

type AuthContextValue = { user: User | null; isLoading: boolean; isAuthenticated: boolean; signIn: (token: string, nextUser: User) => void; logout: () => void; refresh: () => void }
const AuthContext = createContext<AuthContextValue | null>(null)
export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient(); const [token, setToken] = useState<string | null>(() => authStore.get()); const [user, setUser] = useState<User | null>(null)
  const me = useQuery({ queryKey: ['me'], queryFn: api.me, enabled: !!token })
  useEffect(() => { const unsubscribe = onUnauthorized(() => { setToken(null); setUser(null); queryClient.clear() }); return () => { unsubscribe() } }, [queryClient])
  useEffect(() => { if (me.data) setUser(me.data); if (me.isError) { authStore.clear(); setToken(null); setUser(null) } }, [me.data, me.isError])
  const value = useMemo(() => ({ user, isLoading: !!token && me.isLoading, isAuthenticated: !!user && !!token, signIn: (nextToken: string, nextUser: User) => { authStore.set(nextToken); setToken(nextToken); setUser(nextUser); queryClient.setQueryData(['me'], nextUser); queryClient.removeQueries({ queryKey: ['leads'] }) }, logout: () => { authStore.clear(); setToken(null); setUser(null); queryClient.clear() }, refresh: () => { void me.refetch() } }), [user, me.isLoading, me.refetch, queryClient, token])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('useAuth must be used inside AuthProvider'); return value }
