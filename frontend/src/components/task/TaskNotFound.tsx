import React from 'react'
import { AlertTriangle, Mail } from 'lucide-react'

export default function TaskNotFound() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="max-w-md mx-auto text-center space-y-6">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-amber-100 rounded-full mb-4">
          <AlertTriangle size={48} className="text-amber-600" />
        </div>

        <div>
          <h1 className="text-3xl font-bold text-navy-900 mb-3">
            Task Not Found
          </h1>
          <p className="text-lg text-gray-600 leading-relaxed">
            This task link appears to be invalid or has expired.
          </p>
        </div>

        <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-2xl p-6 text-left">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">What to do next:</h2>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start gap-2">
              <span className="text-cyan-500 font-bold">•</span>
              <span>Check your email for the correct task link</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-cyan-500 font-bold">•</span>
              <span>Make sure you're using the full URL (don't cut off any characters)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-cyan-500 font-bold">•</span>
              <span>Contact your IT security team if you continue to have issues</span>
            </li>
          </ul>
        </div>

        <div className="pt-4">
          <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
            <Mail size={14} />
            <span>Need help? Contact your IT team</span>
          </div>
        </div>
      </div>
    </div>
  )
}
