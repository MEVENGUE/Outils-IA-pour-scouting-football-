import {
  BarChart3,
  FileText,
  Globe2,
  LayoutDashboard,
  Radar,
  Search,
  UserCircle,
  Star,
  Users,
  type LucideIcon,
} from 'lucide-react'
import type { AppView } from '../types/player'

export interface NavItem {
  id: AppView
  title: string
  description: string
  icon: LucideIcon
  mobileLabel?: string
}

export const NAV_ITEMS: NavItem[] = [
  { id: 'search', title: 'Search Players', description: 'Recherche globale', icon: Search, mobileLabel: 'Search' },
  { id: 'dashboard', title: 'Dashboard', description: 'Analyse joueur', icon: LayoutDashboard, mobileLabel: 'Dashboard' },
  { id: 'globe', title: '3D Globe Intelligence', description: 'Cartographie', icon: Globe2, mobileLabel: 'Globe' },
  { id: 'reports', title: 'AI Reports', description: 'Rapports scouting', icon: FileText, mobileLabel: 'Reports' },
  { id: 'watchlist', title: 'Watchlist', description: 'Joueurs suivis', icon: Star, mobileLabel: 'Watchlist' },
  { id: 'compare', title: 'Compare Players', description: 'Comparaison', icon: Users, mobileLabel: 'Compare' },
  { id: 'talent', title: 'Talent Discovery', description: 'Base de données', icon: Radar, mobileLabel: 'Talent' },
  { id: 'documents', title: 'Document Analysis', description: 'Centre documentaire', icon: BarChart3, mobileLabel: 'Docs' },
  { id: 'author', title: 'Informations auteur', description: 'FRANCK MEVENGUE', icon: UserCircle, mobileLabel: 'Author' },
]

export const MOBILE_NAV_ITEMS = NAV_ITEMS.filter((item) =>
  ['search', 'dashboard', 'globe', 'reports', 'watchlist'].includes(item.id),
)
