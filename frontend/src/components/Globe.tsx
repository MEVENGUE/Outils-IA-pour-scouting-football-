import { useEffect, useRef, useState } from 'react'
import GlobeGL from 'react-globe.gl'
import type { GlobeMethods } from 'react-globe.gl'
import type { Player } from '../App'
import './Globe.css'
import { countryCoords } from '../utils/countryCoords'

interface GlobeProps {
  player: Player | null
}

interface Point {
  lat: number
  lng: number
  size: number
  color: string
  name: string
}

function resolveCountryCoords(countryName: string): { lat: number; lng: number } | null {
  if (countryCoords[countryName]) {
    return countryCoords[countryName]
  }

  const normalizedName = countryName.toLowerCase().replace(/\s+/g, '')
  const exactMatch = Object.entries(countryCoords).find(
    ([key]) => key.toLowerCase().replace(/\s+/g, '') === normalizedName,
  )
  if (exactMatch) {
    return exactMatch[1]
  }

  return null
}

export default function Globe({ player }: GlobeProps) {
  const globeEl = useRef<GlobeMethods | undefined>(undefined)
  const [points, setPoints] = useState<Point[]>([])

  useEffect(() => {
    if (player?.nationality) {
      const coords = resolveCountryCoords(player.nationality)

      if (coords) {
        const newPoints: Point[] = [
          {
            lat: coords.lat,
            lng: coords.lng,
            size: 1.5,
            color: '#ff3333',
            name: player.name,
          },
        ]
        setPoints(newPoints)

        if (globeEl.current) {
          globeEl.current.pointOfView({ lat: coords.lat, lng: coords.lng, altitude: 1.5 }, 1000)
        }
      } else {
        setPoints([])
      }
    } else {
      setPoints([])
      if (globeEl.current) {
        globeEl.current.pointOfView({ lat: 0, lng: 0, altitude: 1.5 }, 1000)
      }
    }
  }, [player])

  return (
    <div className="globe-container">
      <GlobeGL
        ref={globeEl}
        globeImageUrl="https://unpkg.com/three-globe/example/img/earth-dark.jpg"
        backgroundImageUrl="https://unpkg.com/three-globe/example/img/night-sky.png"
        pointsData={points}
        pointColor={(d: object) => (d as Point).color || '#ff3333'}
        pointRadius={(d: object) => (d as Point).size || 1.5}
        pointResolution={25}
        pointLabel={(d: object) => (d as Point).name || ''}
        pointAltitude={0.02}
        arcsData={[]}
        arcColor={() => '#ff3333'}
        arcDashLength={0.4}
        arcDashGap={0.2}
        arcDashAnimateTime={2000}
        arcStroke={1.5}
        ringsData={points}
        ringColor={() => '#ff3333'}
        ringMaxRadius={5}
        ringPropagationSpeed={5}
        ringRepeatPeriod={1000}
        ringResolution={64}
        ringAltitude={0.02}
        showAtmosphere={true}
        atmosphereColor="#ff3333"
        atmosphereAltitude={0.25}
        onGlobeReady={() => {
          if (globeEl.current) {
            globeEl.current.pointOfView({ lat: 0, lng: 0, altitude: 1.5 }, 0)
          }
        }}
      />
      {player && (
        <div className="globe-overlay">
          <div className="globe-info">
            <span className="globe-player-name">{player.name}</span>
            <span className="globe-country">{player.nationality}</span>
          </div>
        </div>
      )}
      {!player && (
        <div className="globe-empty-state">
          <p>Recherchez un joueur pour voir sa localisation</p>
        </div>
      )}
    </div>
  )
}
