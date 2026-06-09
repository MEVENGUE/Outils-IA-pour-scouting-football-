import { Suspense, lazy } from 'react'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import InsightsStrip from './InsightsStrip'
import CopilotPanel from './CopilotPanel'
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
      <Sidebar />
      <div className="app-main">
        <TopBar />
        <div className="app-content">
          <Suspense fallback={<ViewFallback />}>{renderView()}</Suspense>
        </div>
        <InsightsStrip />
      </div>
      <CopilotPanel />
    </div>
  )
}
