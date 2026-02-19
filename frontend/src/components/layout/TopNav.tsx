import React from 'react'
import { Bell, ChevronDown, Clock, RefreshCw } from 'lucide-react'
import { mockScanResult } from '../../data/mockData'
import { format } from 'date-fns'

export default function TopNav() {
  const lastScan = format(new Date(mockScanResult.completedAt), 'MMM d, yyyy · HH:mm')

  return (
    <header className="h-14 fixed top-0 right-0 left-60 z-30 flex items-center justify-between px-6 bg-navy-950/90 backdrop-blur-sm border-b border-navy-700/50">
      {/* Left — breadcrumb/context */}
      <div className="flex items-center gap-2 text-sm text-navy-300">
        <Clock size={14} className="text-cyan-400" />
        <span>Last scan:</span>
        <span className="text-white font-medium">{lastScan}</span>
        <span className="mx-2 text-navy-600">|</span>
        <span className="text-cyan-400 font-medium">{mockScanResult.accountName}</span>
        <span className="text-xs text-navy-500 font-mono">({mockScanResult.accountId})</span>
      </div>

      {/* Right — actions */}
      <div className="flex items-center gap-3">
        {/* Score pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/20">
          <div className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
          <span className="text-xs font-semibold text-red-400">
            Score: {mockScanResult.overallScore}%
          </span>
        </div>

        {/* Refresh */}
        <button className="p-2 rounded-lg text-navy-300 hover:text-white hover:bg-navy-800 transition-all">
          <RefreshCw size={16} />
        </button>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg text-navy-300 hover:text-white hover:bg-navy-800 transition-all">
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-400 rounded-full" />
        </button>

        {/* Account */}
        <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-navy-800 transition-all">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-500 to-cyan-700 flex items-center justify-center">
            <span className="text-xs font-bold text-navy-900">EP</span>
          </div>
          <span className="text-sm text-white font-medium">EU-Prod</span>
          <ChevronDown size={14} className="text-navy-400" />
        </button>
      </div>
    </header>
  )
}
