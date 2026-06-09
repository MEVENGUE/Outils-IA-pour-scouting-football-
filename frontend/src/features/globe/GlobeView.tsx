import { lazy, Suspense, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Maximize2, Minimize2, ZoomIn, ZoomOut } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { fetchPlayers } from '../../api/players'
import { countryCoords } from '../../utils/countryCoords'
import './GlobeView.css'

const IntelligenceGlobe = lazy(() => import('./IntelligenceGlobe'))

function resolveCountryCoords(countryName?: string) {
  if (!countryName) return null
  if (countryCoords[countryName]) return countryCoords[countryName]
  const normalized = countryName.toLowerCase().replace(/\s+/g, '')
  const match = Object.entries(countryCoords).find(
    ([key]) => key.toLowerCase().replace(/\s+/g, '') === normalized,
  )
  return match?.[1] ?? null
}

export default function GlobeView() {
  const { player } = useApp()
  const [fullscreen, setFullscreen] = useState(false)
  const { data } = useQuery({ queryKey: ['players-globe'], queryFn: () => fetchPlayers() })

  const markers = useMemo(() => {
    const points = (data?.players ?? [])
      .map((p) => {
        const coords = resolveCountryCoords(p.nationality)
        if (!coords) return null
        return {
          lat: coords.lat,
          lng: coords.lng,
          name: p.name,
          country: p.nationality ?? '',
          club: p.current_club ?? '',
        }
      })
      .filter(Boolean) as {
      lat: number
      lng: number
      name: string
      country: string
      club: string
    }[]

    if (player?.nationality) {
      const coords = resolveCountryCoords(player.nationality)
      if (coords) {
        points.unshift({
          lat: coords.lat,
          lng: coords.lng,
          name: player.name,
          country: player.nationality,
          club: player.current_club ?? '',
        })
      }
    }

    return points
  }, [data?.players, player])

  return (
    <div className={`globe-view card ${fullscreen ? 'fullscreen' : ''}`}>
      <div className="globe-toolbar">
        <div>
          <h3>3D Globe Intelligence</h3>
          <p>{markers.length} live markers from backend database</p>
        </div>
        <div className="globe-controls">
          <button type="button" className="btn" aria-label="Zoom in">
            <ZoomIn size={16} />
          </button>
          <button type="button" className="btn" aria-label="Zoom out">
            <ZoomOut size={16} />
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => setFullscreen((v) => !v)}
            aria-label="Toggle fullscreen"
          >
            {fullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
        </div>
      </div>
      <Suspense fallback={<div className="globe-loader skeleton" />}>
        <IntelligenceGlobe markers={markers} focusPlayer={player} />
      </Suspense>
    </div>
  )
}
