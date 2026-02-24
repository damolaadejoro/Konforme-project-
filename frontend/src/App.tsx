import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import NIS2Overview from './pages/NIS2Overview'
import ControlsLibrary from './pages/ControlsLibrary'
import PeopleTasks from './pages/PeopleTasks'
import Scan from './pages/Scan'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import EmployeeTaskPage from './pages/EmployeeTaskPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Employee task page - no layout wrapper (separate experience) */}
        <Route path="/task/:taskId" element={<EmployeeTaskPage />} />

        {/* Admin dashboard routes */}
        <Route path="/" element={<Layout />}>
          <Route index element={<NIS2Overview />} />
          <Route path="controls" element={<ControlsLibrary />} />
          <Route path="people-tasks" element={<PeopleTasks />} />
          <Route path="scan" element={<Scan />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
