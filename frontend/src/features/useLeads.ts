import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, normalizeLeads } from '../api/client'
import { useAuth } from '../app/auth'

export function useLeads(enabled = true) {
  const { user } = useAuth(); const queryClient = useQueryClient(); const queryKey = ['leads', user?.id ?? 'anonymous', user?.role ?? 'none']
  const query = useQuery({ queryKey, queryFn: async () => normalizeLeads(await api.listLeads()), enabled: enabled && !!user })
  return { ...query, leads: query.data ?? [], refresh: () => queryClient.invalidateQueries({ queryKey }) }
}
