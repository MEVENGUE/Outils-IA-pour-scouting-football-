import { useEffect, useRef, useState } from 'react'
import GlobeGL from 'react-globe.gl'
import type { GlobeMethods } from 'react-globe.gl'
import type { Player } from '../../types/player'
import { countryCoords } from '../../utils/countryCoords'
import './IntelligenceGlobe.css'

interface Marker {
  lat: number
  lng: number
  name: string
  country: string
  club: string
}

interface Props {
  markers: Marker[]
  focusPlayer: Player | null
}

interface Point extends Marker {
  size: number
  color: string
}

function resolveCountryCoords(countryName?: string) {
  if (!countryName) return null
  if (countryCoords[countryName]) return countryCoords[countryName]
  const normalized = countryName.toLowerCase().replace(/\s+/g, '')
  const match = Object.entries(countryCoords).find(
    ([key]) => key.toLowerCase().replace(/\s+/g, '') === normalized,
  )
  return match?.[1] ?? null
}

export default function IntelligenceGlobe({ markers, focusPlayer }: Props) {
  const globeRef = useRef<GlobeMethods | undefined>(undefined)
  const [points, setPoints] = useState<Point[]>([])

  useEffect(() => {
    const mapped: Point[] = markers.map((marker) => ({
      ...marker,
      size: focusPlayer?.name === marker.name ? 1.8 : 1.1,
      color: focusPlayer?.name === marker.name ? '#FF2D2D' : '#FF5C5C',
    }))
    setPoints(mapped)

    if (focusPlayer?.nationality) {
      const coords = resolveCountryCoords(focusPlayer.nationality)
      if (coords && globeRef.current) {
        globeRef.current.pointOfView({ lat: coords.lat, lng: coords.lng, altitude: 1.4 }, 1200)
      }
    }
  }, [markers, focusPlayer])

  return (
    <div className="intel-globe">
      <GlobeGL
        ref={globeRef}
        globeImageUrl="https://unpkg.com/three-globe/example/img/earth-dark.jpg"
        backgroundImageUrl="https://unpkg.com/three-globe/example/img/night-sky.png"
        pointsData={points}
        pointColor={(d: object) => (d as Point).color}
        pointRadius={(d: object) => (d as Point).size}
        pointLabel={(d: object) => {
          const p = d as Point
          return `${p.name}<br/>${p.country}<br/>${p.club}`
        }}
        pointAltitude={0.03}
        ringsData={points.filter((p) => p.name === focusPlayer?.name)}
        ringColor={() => '#FF2D2D'}
        ringMaxRadius={4}
        ringPropagationSpeed={4}
        ringRepeatPeriod={900}
        arcsData={points.slice(0, 6).flatMap((source, i, arr) =>
          i === 0
            ? []
            : [
                {
                  startLat: arr[0].lat,
                  startLng: arr[0].lng,
                  endLat: source.lat,
                  endLng: source.lng,
                },
              ],
        )}
        arcColor={() => '#FF2D2D'}
        arcDashLength={0.4}
        arcDashGap={0.25}
        arcDashAnimateTime={2000}
        showAtmosphere
        atmosphereColor="#FF2D2D"
        atmosphereAltitude={0.2}
        onGlobeReady={() => {
          globeRef.current?.pointOfView({ lat: 20, lng: 0, altitude: 2.2 }, 0)
        }}
      />
    </div>
  )
}
