import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import Layout from './components/Layout/Layout'
import ProvidersPage from './pages/ProvidersPage'
import ChatPage from './pages/ChatPage'
import DashboardPage from './pages/DashboardPage'
import MemoryPage from './pages/MemoryPage'
import PlannerPage from './pages/PlannerPage'
import WorkflowsPage from './pages/WorkflowsPage'
import WorkspacePage from './pages/WorkspacePage'
import ToolsPage from './pages/ToolsPage'
import SettingsPage from './pages/SettingsPage'
import AgentsPage from './pages/AgentsPage'

function App() {
  return (
    <>
      <Toaster position="bottom-right" richColors closeButton />
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="/providers" element={<ProvidersPage />} />
          <Route path="/memory" element={<MemoryPage />} />
          <Route path="/planner" element={<PlannerPage />} />
          <Route path="/workflows" element={<WorkflowsPage />} />
          <Route path="/workspace" element={<WorkspacePage />} />
          <Route path="/tools" element={<ToolsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </>
  )
}

export default App
