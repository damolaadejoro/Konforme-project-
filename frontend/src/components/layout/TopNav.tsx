import React from 'react'
import { Bell, ChevronDown, Clock, RefreshCw, Save } from 'lucide-react'
import { mockScanResult } from '../../data/mockData'
import { format, formatDistanceToNow } from 'date-fns'
import { useControls } from '../../hooks/useControls'

export default function TopNav() {
  const { lastSaved, complianceScore } = useControls()

  const lastSavedText = lastSaved
    ? formatDistanceToNow(new Date(lastSaved), { addSuffix: true })
    : 'Never'

  const score = complianceScore.overall

  return (
    <header className="h-14 fixed top-0 right-0 left-60 z-30 flex items-center justify-between px-6 bg-navy-950/90 backdrop-blur-sm border-b border-navy-700/50">
      {/* Left — breadcrumb/context */}
      <div className="flex items-center gap-2 text-sm text-navy-300">
        <Save size={14} className="text-emerald-400" />
        <span>Saved:</span>
        <span className="text-emerald-400 font-medium">{lastSavedText}</span>
        <span className="mx-2 text-navy-600">|</span>
        <span className="text-cyan-400 font-medium">{mockScanResult.accountName}</span>
        <span className="text-xs text-navy-500 font-mono">({mockScanResult.accountId})</span>
      </div>

      {/* Right — actions */}
      <div className="flex items-center gap-3">
        {/* Score pill */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
          score >= 75
            ? 'bg-emerald-500/10 border border-emerald-500/20'
            : score >= 50
            ? 'bg-yellow-500/10 border border-yellow-500/20'
            : 'bg-red-500/10 border border-red-500/20'
        }`}>
          <div className={`w-2 h-2 rounded-full animate-pulse ${
            score >= 75 ? 'bg-emerald-400' : score >= 50 ? 'bg-yellow-400' : 'bg-red-400'
          }`} />
          <span className={`text-xs font-semibold ${
            score >= 75 ? 'text-emerald-400' : score >= 50 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            Score: {score}%
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
