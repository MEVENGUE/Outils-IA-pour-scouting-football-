export interface Player {
  id?: number
  name: string
  age?: number
  nationality?: string
  current_club?: string
  position?: string
  position_tm?: string
  position_fbref?: string
  height?: string
  weight?: string
  market_value?: string
  goals?: number
  assists?: number
  appearances?: number
  minutes_played?: number
  yellow_cards?: number
  red_cards?: number
  goals_per_match?: number
  assists_per_match?: number
  contract_expires?: string
  image_url?: string
  scouting_report?: string
  stats_available?: boolean
  stats_season?: string
  stats_source?: string
  source_transfermarkt?: string
}

export type AiStatus = 'ready' | 'unconfigured' | 'report_unavailable'

export type AppView =
  | 'search'
  | 'dashboard'
  | 'globe'
  | 'reports'
  | 'watchlist'
  | 'compare'
  | 'talent'
  | 'documents'
  | 'author'

export interface ScrapePlayerResponse {
  player: Player
  ai_status?: AiStatus
}

export interface HealthResponse {
  status: string
  database: string
  openai: string
}

export interface ActivityEvent {
  id: string
  label: string
  timestamp: number
  playerName?: string
}

export interface StoredDocument {
  id: string
  name: string
  type: string
  size: number
  uploadedAt: number
  status: 'pending' | 'analyzing' | 'complete' | 'error'
  summary?: string
  insights?: string[]
  error?: string
}

export interface CopilotMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  thinking?: boolean
  sources?: string[]
  confidence?: number
}
