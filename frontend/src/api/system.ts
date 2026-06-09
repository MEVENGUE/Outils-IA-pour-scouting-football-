import type { HealthResponse } from '../types/player'
import { apiFetch } from './client'

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health', {}, 15_000)
}
