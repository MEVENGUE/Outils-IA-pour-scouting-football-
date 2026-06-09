import AppShell from './layout/AppShell'
import { AppProvider } from './context/AppProvider'

export default function App() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  )
}
