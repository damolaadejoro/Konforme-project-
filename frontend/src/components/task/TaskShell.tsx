import React from 'react'
import { Shield } from 'lucide-react'

interface TaskShellProps {
  companyName: string
  currentStep: number
  totalSteps: number
  children: React.ReactNode
}

export default function TaskShell({ companyName, currentStep, totalSteps, children }: TaskShellProps) {
  const progressPercentage = (currentStep / totalSteps) * 100

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield size={24} className="text-cyan-500" />
            <span className="font-bold text-lg text-navy-900 font-syne">Konforme</span>
          </div>
          <div className="text-sm text-gray-600">
            <span className="font-medium text-navy-900">{companyName}</span>
            <span className="mx-2 text-gray-400">·</span>
            <span>Security Compliance</span>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="h-1 bg-gray-100">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400 transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 px-4 py-8 sm:py-12">
        <div className="max-w-[480px] mx-auto">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-4 py-6">
        <div className="max-w-6xl mx-auto text-center space-y-2">
          <p className="text-sm text-gray-500">
            Powered by <span className="font-semibold text-gray-700">Konforme</span>
          </p>
          <p className="text-xs text-gray-400">
            Your response is recorded securely
          </p>
        </div>
      </footer>
    </div>
  )
}
