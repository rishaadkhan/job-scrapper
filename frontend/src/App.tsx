import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import OverviewPage from './pages/OverviewPage'
import CompaniesPage from './pages/CompaniesPage'
import FiltersPage from './pages/FiltersPage'
import JobsPage from './pages/JobsPage'
import RunsPage from './pages/RunsPage'
import ExportsPage from './pages/ExportsPage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-content">
        <Routes>
          <Route path="/"          element={<OverviewPage />} />
          <Route path="/companies" element={<CompaniesPage />} />
          <Route path="/filters"   element={<FiltersPage />} />
          <Route path="/jobs"      element={<JobsPage />} />
          <Route path="/runs"      element={<RunsPage />} />
          <Route path="/exports"   element={<ExportsPage />} />
          <Route path="*"          element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  )
}

export default function App() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={
        isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
      } />
      <Route path="/*" element={
        <RequireAuth>
          <AppShell />
        </RequireAuth>
      } />
    </Routes>
  )
}
