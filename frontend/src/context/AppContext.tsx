import { createContext, useContext, type Dispatch, type SetStateAction } from 'react'
import type {
  ActivityEvent,
  AiStatus,
  AppView,
  CopilotMessage,
  Player,
  StoredDocument,
} from '../types/player'

export interface AppContextValue {
  activeView: AppView
  setActiveView: (view: AppView) => void
  player: Player | null
  loading: boolean
  error: string | null
  aiStatus: AiStatus
  searchPlayer: (name: string) => Promise<void>
  compareA: Player | null
  compareB: Player | null
  setCompareA: (player: Player | null) => void
  setCompareB: (player: Player | null) => void
  watchlistIds: number[]
  toggleWatchlist: (id: number) => void
  activities: ActivityEvent[]
  pushActivity: (label: string, playerName?: string) => void
  documents: StoredDocument[]
  setDocuments: Dispatch<SetStateAction<StoredDocument[]>>
  copilotMessages: CopilotMessage[]
  setCopilotMessages: Dispatch<SetStateAction<CopilotMessage[]>>
  copilotLoading: boolean
  sendCopilotMessage: (content: string) => Promise<void>
}

export const AppContext = createContext<AppContextValue | null>(null)

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
