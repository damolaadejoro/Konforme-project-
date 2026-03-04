import React from 'react'
import { AlertTriangle, Mail } from 'lucide-react'

export default function TaskNotFound() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4 py-8">
      <div className="max-w-md mx-auto w-full text-center space-y-5 sm:space-y-6">
        <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 bg-amber-100 rounded-full mb-2 sm:mb-4">
          <AlertTriangle size={40} className="text-amber-600 sm:w-12 sm:h-12" />
        </div>

        <div>
          <h1 className="text-[26px] sm:text-3xl md:text-4xl font-bold text-navy-900 mb-3 leading-tight">
            Task Not Found
          </h1>
          <p className="text-base sm:text-lg text-gray-600 leading-relaxed px-2">
            This task link appears to be invalid or has expired.
          </p>
        </div>

        <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-lg sm:rounded-2xl p-5 sm:p-6 text-left">
          <h2 className="text-sm sm:text-base font-semibold text-gray-900 mb-3">What to do next:</h2>
          <ul className="space-y-2.5 text-sm sm:text-[15px] text-gray-600">
            <li className="flex items-start gap-2.5">
              <span className="text-cyan-500 font-bold flex-shrink-0 mt-0.5">•</span>
              <span className="leading-relaxed">Check your email for the correct task link</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-cyan-500 font-bold flex-shrink-0 mt-0.5">•</span>
              <span className="leading-relaxed">Make sure you're using the full URL (don't cut off any characters)</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-cyan-500 font-bold flex-shrink-0 mt-0.5">•</span>
              <span className="leading-relaxed">Contact your IT security team if you continue to have issues</span>
            </li>
          </ul>
        </div>

        <div className="pt-4">
          <div className="flex items-center justify-center gap-2 text-sm sm:text-[15px] text-gray-500">
            <Mail size={14} className="sm:w-4 sm:h-4" />
            <span>Need help? Contact your IT team</span>
          </div>
        </div>
      </div>
    </div>
  )
}
