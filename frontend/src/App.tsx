import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import * as TooltipPrimitive from '@radix-ui/react-tooltip'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/auth/ProtectedRoute'
import Layout from './components/layout/Layout'
import NIS2Overview from './pages/NIS2Overview'
import ControlsLibrary from './pages/ControlsLibrary'
import PeopleTasks from './pages/PeopleTasks'
import Scan from './pages/Scan'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import EmployeeTaskPage from './pages/EmployeeTaskPage'
import Assessment from './pages/Assessment'
import AssessmentHistory from './pages/AssessmentHistory'
import Remediation from './pages/Remediation'
import Login from './pages/Login'
import Register from './pages/Register'
import ResetPassword from './pages/ResetPassword'

export default function App() {
  return (
    <TooltipPrimitive.Provider delayDuration={300}>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          {/* Employee task page - no layout wrapper (separate experience) */}
          <Route path="/task/:taskId" element={<EmployeeTaskPage />} />

          {/* Admin dashboard routes - protected */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<NIS2Overview />} />
            <Route path="controls" element={<ControlsLibrary />} />
            <Route path="assessment" element={<Assessment />} />
            <Route path="assessment/history" element={<AssessmentHistory />} />
            <Route path="remediation" element={<Remediation />} />
            <Route path="people-tasks" element={<PeopleTasks />} />
            <Route path="scan" element={<Scan />} />
            <Route path="reports" element={<Reports />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </TooltipPrimitive.Provider>
  )
}
