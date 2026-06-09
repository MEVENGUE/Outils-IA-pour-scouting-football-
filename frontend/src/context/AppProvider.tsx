import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { askCopilot } from '../api/ai'
import { scrapePlayer } from '../api/players'
import { AppContext } from './AppContext'
import { getStoredDocuments, getWatchlistIds, toggleWatchlistId } from '../utils/storage'
import type {
  ActivityEvent,
  AiStatus,
  AppView,
  CopilotMessage,
  Player,
  StoredDocument,
} from '../types/player'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

function AppStateProvider({ children }: { children: ReactNode }) {
  const [activeView, setActiveView] = useState<AppView>('dashboard')
  const [player, setPlayer] = useState<Player | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [aiStatus, setAiStatus] = useState<AiStatus>('unconfigured')
  const [compareA, setCompareA] = useState<Player | null>(null)
  const [compareB, setCompareB] = useState<Player | null>(null)
  const [watchlistIds, setWatchlistIds] = useState<number[]>(() => getWatchlistIds())
  const [activities, setActivities] = useState<ActivityEvent[]>([])
  const [documents, setDocuments] = useState<StoredDocument[]>(() => getStoredDocuments())
  const [copilotMessages, setCopilotMessages] = useState<CopilotMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'X-SCOUT AI Copilot prêt. Recherchez un joueur puis posez vos questions scouting, marché, comparaison ou projection.',
    },
  ])
  const [copilotLoading, setCopilotLoading] = useState(false)

  const pushActivity = useCallback((label: string, playerName?: string) => {
    setActivities((prev) => [
      {
        id: `${Date.now()}-${Math.random()}`,
        label,
        timestamp: Date.now(),
        playerName,
      },
      ...prev.slice(0, 19),
    ])
  }, [])

  const searchPlayer = useCallback(
    async (name: string) => {
      if (!name.trim()) {
        setError('Veuillez entrer un nom de joueur')
        return
      }
      setLoading(true)
      setError(null)
      try {
        const result = await scrapePlayer(name.trim())
        setPlayer(result.player)
        setAiStatus(result.ai_status ?? 'unconfigured')
        setCompareA((prev) => prev ?? result.player)
        pushActivity('Profil chargé', result.player.name)
        setActiveView('dashboard')
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erreur de recherche'
        if (err instanceof DOMException && err.name === 'AbortError') {
          setError('La recherche a expiré. Réessayez.')
        } else {
          setError(message)
        }
      } finally {
        setLoading(false)
      }
    },
    [pushActivity],
  )

  const toggleWatchlist = useCallback(
    (id: number) => {
      const next = toggleWatchlistId(id)
      setWatchlistIds(next)
      pushActivity(next.includes(id) ? 'Ajouté à la watchlist' : 'Retiré de la watchlist')
    },
    [pushActivity],
  )

  const sendCopilotMessage = useCallback(
    async (content: string) => {
      const userMessage: CopilotMessage = {
        id: `u-${Date.now()}`,
        role: 'user',
        content,
      }
      const thinkingId = `t-${Date.now()}`
      setCopilotMessages((prev) => [
        ...prev,
        userMessage,
        { id: thinkingId, role: 'assistant', content: '', thinking: true },
      ])
      setCopilotLoading(true)

      try {
        const { content: answer, sources } = await askCopilot(content, player)
        setCopilotMessages((prev) =>
          prev
            .filter((m) => m.id !== thinkingId)
            .concat({
              id: `a-${Date.now()}`,
              role: 'assistant',
              content: answer,
              sources,
              confidence: player?.stats_available ? 0.86 : 0.72,
            }),
        )
        pushActivity('Analyse IA générée', player?.name)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erreur Copilot'
        setCopilotMessages((prev) =>
          prev
            .filter((m) => m.id !== thinkingId)
            .concat({ id: `e-${Date.now()}`, role: 'assistant', content: message }),
        )
      } finally {
        setCopilotLoading(false)
      }
    },
    [player, pushActivity],
  )

  const value = useMemo(
    () => ({
      activeView,
      setActiveView,
      player,
      loading,
      error,
      aiStatus,
      searchPlayer,
      compareA,
      compareB,
      setCompareA,
      setCompareB,
      watchlistIds,
      toggleWatchlist,
      activities,
      pushActivity,
      documents,
      setDocuments,
      copilotMessages,
      setCopilotMessages,
      copilotLoading,
      sendCopilotMessage,
    }),
    [
      activeView,
      player,
      loading,
      error,
      aiStatus,
      searchPlayer,
      compareA,
      compareB,
      watchlistIds,
      toggleWatchlist,
      activities,
      pushActivity,
      documents,
      copilotMessages,
      copilotLoading,
      sendCopilotMessage,
    ],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function AppProvider({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AppStateProvider>{children}</AppStateProvider>
    </QueryClientProvider>
  )
}
