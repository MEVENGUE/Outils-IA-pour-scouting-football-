import type { Player, ScrapePlayerResponse } from '../types/player'
import { apiFetch } from './client'

export async function scrapePlayer(playerName: string): Promise<ScrapePlayerResponse> {
  try {
    return await apiFetch<ScrapePlayerResponse>('/scrape-player', {
      method: 'POST',
      body: JSON.stringify({ player_name: playerName }),
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Erreur inconnue'
    if (message.includes('404') || message.includes('Could not find')) {
      const fallback = await apiFetch<{ player: Player }>(
        `/player-by-name/${encodeURIComponent(playerName)}`,
      )
      return { player: fallback.player, ai_status: 'unconfigured' }
    }
    throw error
  }
}

export async function fetchPlayerById(id: number) {
  return apiFetch<{ player: Player }>(`/players/${id}`)
}

export async function fetchPlayerByName(name: string) {
  return apiFetch<{ player: Player }>(`/player-by-name/${encodeURIComponent(name)}`)
}

export async function fetchPlayers(filters?: {
  name?: string
  country?: string
  position?: string
  max_age?: number
}) {
  const params = new URLSearchParams()
  if (filters?.name) params.set('name', filters.name)
  if (filters?.country) params.set('country', filters.country)
  if (filters?.position) params.set('position', filters.position)
  if (filters?.max_age) params.set('max_age', String(filters.max_age))
  const query = params.toString()
  return apiFetch<{ players: Player[] }>(`/players${query ? `?${query}` : ''}`)
}

export async function fetchPlayerAnalytics(filters?: {
  min_goals?: number
  min_assists?: number
  position?: string
  country?: string
}) {
  const params = new URLSearchParams()
  if (filters?.min_goals) params.set('min_goals', String(filters.min_goals))
  if (filters?.min_assists) params.set('min_assists', String(filters.min_assists))
  if (filters?.position) params.set('position', filters.position)
  if (filters?.country) params.set('country', filters.country)
  const query = params.toString()
  return apiFetch<{
    total_players: number
    average_goals: number
    average_assists: number
    players: Player[]
  }>(`/analytics/player-stats${query ? `?${query}` : ''}`)
}

export async function fetchCountries() {
  return apiFetch<{ countries: { country: string; players_count: number }[] }>('/countries')
}
