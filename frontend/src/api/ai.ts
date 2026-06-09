import { apiFetch } from './client'
import type { Player } from '../types/player'

export async function askCopilot(
  prompt: string,
  player?: Player | null,
): Promise<{ content: string; sources: string[] }> {
  const systemContext = player
    ? `Joueur analysé: ${JSON.stringify({
        name: player.name,
        age: player.age,
        nationality: player.nationality,
        club: player.current_club,
        position: player.position,
        market_value: player.market_value,
        goals: player.goals,
        assists: player.assists,
        appearances: player.appearances,
        stats_season: player.stats_season,
        scouting_report: player.scouting_report,
      })}`
    : 'Aucun joueur sélectionné.'

  const response = await apiFetch<{
    choices?: { message?: { content?: string } }[]
  }>('/ai', {
    method: 'POST',
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      temperature: 0.4,
      max_tokens: 1200,
      messages: [
        {
          role: 'system',
          content:
            'Tu es X-SCOUT AI Copilot, expert en scouting football. Réponds en français, de façon structurée et professionnelle. Utilise uniquement les données fournies; indique clairement si une information manque.',
        },
        { role: 'system', content: systemContext },
        { role: 'user', content: prompt },
      ],
    }),
  })

  const content = response.choices?.[0]?.message?.content?.trim() ?? ''
  const sources = ['OpenAI', 'X-SCOUT Database']
  if (player?.stats_source) sources.push(player.stats_source)
  if (player?.source_transfermarkt) sources.push('Transfermarkt')

  return { content, sources }
}

export async function analyzeDocumentText(
  fileName: string,
  text: string,
): Promise<{ summary: string; insights: string[] }> {
  const response = await apiFetch<{
    choices?: { message?: { content?: string } }[]
  }>('/ai', {
    method: 'POST',
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      temperature: 0.3,
      max_tokens: 900,
      messages: [
        {
          role: 'system',
          content:
            'Analyse ce document football/scouting. Réponds en JSON strict: {"summary":"...","insights":["...","..."]}. Pas de markdown.',
        },
        {
          role: 'user',
          content: `Document: ${fileName}\n\n${text.slice(0, 12000)}`,
        },
      ],
    }),
  })

  const raw = response.choices?.[0]?.message?.content?.trim() ?? ''
  try {
    const parsed = JSON.parse(raw.replace(/```json|```/g, '').trim()) as {
      summary?: string
      insights?: string[]
    }
    return {
      summary: parsed.summary ?? raw,
      insights: parsed.insights ?? [],
    }
  } catch {
    return { summary: raw, insights: [] }
  }
}
