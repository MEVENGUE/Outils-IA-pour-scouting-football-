import { Suspense, lazy, useCallback, useEffect, useState } from 'react'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import InsightsStrip from './InsightsStrip'
import CopilotPanel from './CopilotPanel'
import MobileNav from './MobileNav'
import { useApp } from '../context/AppContext'
import './AppShell.css'

const DashboardView = lazy(() => import('../features/dashboard/DashboardView'))
const GlobeView = lazy(() => import('../features/globe/GlobeView'))
const ReportsView = lazy(() => import('../features/reports/ReportsView'))
const WatchlistView = lazy(() => import('../features/watchlist/WatchlistView'))
const CompareView = lazy(() => import('../features/compare/CompareView'))
const TalentView = lazy(() => import('../features/talent/TalentDiscoveryView'))
const DocumentsView = lazy(() => import('../features/documents/DocumentCenterView'))
const AuthorView = lazy(() => import('../features/author/AuthorView'))
const SearchView = lazy(() => import('../features/search/SearchView'))

function ViewFallback() {
  return <div className="view-fallback skeleton" />
}

export default function AppShell() {
  const { activeView } = useApp()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [copilotOpen, setCopilotOpen] = useState(false)

  const closeSidebar = useCallback(() => setSidebarOpen(false), [])
  const closeCopilot = useCallback(() => setCopilotOpen(false), [])

  useEffect(() => {
    document.body.classList.toggle('sidebar-open', sidebarOpen)
    document.body.classList.toggle('copilot-open', copilotOpen)
    return () => {
      document.body.classList.remove('sidebar-open', 'copilot-open')
    }
  }, [sidebarOpen, copilotOpen])

  useEffect(() => {
    closeSidebar()
  }, [activeView, closeSidebar])

  const renderView = () => {
    switch (activeView) {
      case 'search':
        return <SearchView />
      case 'dashboard':
        return <DashboardView />
      case 'globe':
        return <GlobeView />
      case 'reports':
        return <ReportsView />
      case 'watchlist':
        return <WatchlistView />
      case 'compare':
        return <CompareView />
      case 'talent':
        return <TalentView />
      case 'documents':
        return <DocumentsView />
      case 'author':
        return <AuthorView />
      default:
        return <DashboardView />
    }
  }

  return (
    <div className="app-shell">
      {sidebarOpen && (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="Fermer le menu"
          onClick={closeSidebar}
        />
      )}
      <Sidebar open={sidebarOpen} onNavigate={closeSidebar} />
      <div className="app-main">
        <TopBar
          onMenuClick={() => setSidebarOpen(true)}
          onCopilotClick={() => setCopilotOpen(true)}
        />
        <div className="app-content">
          <Suspense fallback={<ViewFallback />}>{renderView()}</Suspense>
        </div>
        <InsightsStrip />
      </div>
      <CopilotPanel open={copilotOpen} onClose={closeCopilot} />
      <MobileNav onOpenMenu={() => setSidebarOpen(true)} onOpenCopilot={() => setCopilotOpen(true)} />
    </div>
  )
}
