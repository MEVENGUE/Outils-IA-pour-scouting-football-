import { useEffect, useRef, useState } from 'react'
import GlobeGL from 'react-globe.gl'
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

export default function Globe({ player }: GlobeProps) {
  const globeEl = useRef<any>(null)
  const [points, setPoints] = useState<Point[]>([])

  useEffect(() => {
    if (player?.nationality) {
      const countryName = player.nationality
      console.log(`Recherche des coordonnées pour: ${countryName}`)
      
      // Essaie de trouver les coordonnées avec différentes variantes
      let coords = countryCoords[countryName]
      
      // Si pas trouvé directement, cherche une correspondance partielle
      if (!coords) {
        const countryKeys = Object.keys(countryCoords)
        const matchingKey = countryKeys.find(key => {
          const keyLower = key.toLowerCase()
          const nameLower = countryName.toLowerCase()
          return keyLower === nameLower || 
                 keyLower.includes(nameLower) || 
                 nameLower.includes(keyLower) ||
                 keyLower.replace(/\s+/g, '') === nameLower.replace(/\s+/g, '')
        })
        if (matchingKey) {
          coords = countryCoords[matchingKey]
          console.log(`Coordonnées trouvées via correspondance: ${matchingKey} ->`, coords)
        }
      } else {
        console.log(`Coordonnées trouvées directement:`, coords)
      }
      
      if (coords) {
        // Définit les points à afficher sur le globe avec effet fluorescent
        const newPoints: Point[] = [{
          lat: coords.lat,
          lng: coords.lng,
          size: 1.5,
          color: '#ff3333',
          name: player.name
        }]
        console.log(`Point créé pour ${player.name} à:`, newPoints[0])
        setPoints(newPoints)
        
        // Centre le globe sur le pays du joueur avec animation
        if (globeEl.current) {
          globeEl.current.pointOfView(
            { lat: coords.lat, lng: coords.lng, altitude: 1.5 },
            1000
          )
          console.log(`Globe centré sur: lat=${coords.lat}, lng=${coords.lng}`)
        }
      } else {
        // Si pas de coordonnées trouvées, réinitialise mais garde le joueur affiché
        console.warn(`Coordonnées non trouvées pour le pays: ${countryName}`)
        setPoints([])
      }
    } else {
      // Réinitialise le globe si aucun joueur n'est sélectionné
      console.log('Aucun joueur sélectionné, réinitialisation du globe')
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
        pointColor={(d: any) => d.color || '#ff3333'}
        pointRadius={(d: any) => d.size || 1.5}
        pointResolution={25}
        pointsData={points}
        pointLabel={(d: any) => d.name || ''}
        pointLabelSize={2.5}
        pointLabelColor={() => '#ff3333'}
        pointLabelDotRadius={1.2}
        pointLabelDotColor={() => '#ff3333'}
        pointAltitude={0.02}
        pointLabelTextAnchor="middle"
        pointLabelPixelOffset={[0, -15]}
        pointLabelBgColor={() => 'rgba(0, 0, 0, 0.8)'}
        pointLabelBgPadding={[8, 4]}
        pointLabelBgRadius={4}
        showAtmosphere={true}
        atmosphereColor="#ff3333"
        atmosphereAltitude={0.25}
        showGlow={true}
        glowCoefficient={0.1}
        glowPower={2}
        glowColor="#ff3333"
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
        ringWeight={2}
        onGlobeReady={() => {
          if (globeEl.current) {
            globeEl.current.pointOfView({ lat: 0, lng: 0, altitude: 1.5 }, 0)
            // Active les effets de fluorescence
            globeEl.current.scene().children.forEach((child: any) => {
              if (child.material) {
                child.material.emissive = { r: 1, g: 0.2, b: 0.2 }
                child.material.emissiveIntensity = 0.3
              }
            })
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
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: 'rgba(255, 102, 102, 0.7)',
          textAlign: 'center',
          zIndex: 1,
          background: 'rgba(10, 0, 0, 0.6)',
          backdropFilter: 'blur(10px)',
          padding: '2rem 3rem',
          borderRadius: '12px',
          border: '1px solid rgba(255, 68, 68, 0.2)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(255, 0, 0, 0.2)',
          fontSize: '1.1rem',
          fontWeight: 500,
          letterSpacing: '0.5px'
        }}>
          <p>Recherchez un joueur pour voir sa localisation</p>
        </div>
      )}
    </div>
  )
}

