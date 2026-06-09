import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '../api/system'

export function useSystemHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 60_000,
  })
}
