import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, ChevronDown, RefreshCw, Save, Check, LogOut } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { useControls } from '../../hooks/useControls'
import { useAuth } from '../../context/AuthContext'

export default function TopNav() {
  const { lastSaved, complianceScore } = useControls()
  const { isAuthenticated, accountName, email, awsAccounts, selectedAwsAccountId, selectAwsAccount, logout } = useAuth()
  const navigate = useNavigate()
  const [showAccountDropdown, setShowAccountDropdown] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)

  const lastSavedText = lastSaved
    ? formatDistanceToNow(new Date(lastSaved), { addSuffix: true })
    : 'Never'

  // Use scan score from last scan if available, otherwise controls score
  const lastScan = React.useMemo(() => {
    try {
      const raw = localStorage.getItem('konforme_last_scan')
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  }, [])

  const selectedAccount = awsAccounts.find(a => a.id === selectedAwsAccountId)
  const score = lastScan?.overallScore ?? complianceScore.overall
  const displayName = isAuthenticated ? accountName : lastScan?.accountName ?? 'No Account'
  const displayId = selectedAccount?.awsAccountId ?? lastScan?.accountId ?? '—'
  const initials = displayName
    ? displayName.slice(0, 2).toUpperCase()
    : 'NA'

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowAccountDropdown(false)
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="h-14 fixed top-0 right-0 left-60 z-30 flex items-center justify-between px-6 bg-navy-950/90 backdrop-blur-sm border-b border-navy-700/50">
      {/* Left — breadcrumb/context */}
      <div className="flex items-center gap-2 text-sm text-navy-300">
        <Save size={14} className="text-emerald-400" />
        <span>Saved:</span>
        <span className="text-emerald-400 font-medium">{lastSavedText}</span>
        <span className="mx-2 text-navy-600">|</span>
        <span className="text-cyan-400 font-medium">{displayName}</span>
        {selectedAccount && (
          <>
            <span className="text-navy-600">·</span>
            <span className="text-xs text-navy-400">{selectedAccount.alias}</span>
          </>
        )}
        <span className="text-xs text-navy-500 font-mono">({displayId})</span>
      </div>

      {/* Right — actions */}
      <div className="flex items-center gap-3">
        {/* AWS Account switcher */}
        {isAuthenticated && awsAccounts.length > 1 && (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowAccountDropdown(!showAccountDropdown)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-900/60 border border-navy-700 hover:border-cyan-500/40 transition-all text-xs"
            >
              <span className="text-navy-300">{selectedAccount?.alias || 'Select Account'}</span>
              <ChevronDown size={12} className="text-navy-400" />
            </button>
            {showAccountDropdown && (
              <div className="absolute right-0 top-full mt-1 w-64 bg-navy-900 border border-navy-700 rounded-lg shadow-xl z-50 py-1">
                {awsAccounts.map(acc => (
                  <button
                    key={acc.id}
                    onClick={() => { selectAwsAccount(acc.id); setShowAccountDropdown(false) }}
                    className="w-full flex items-center gap-3 px-3 py-2 hover:bg-navy-800 transition-colors text-left"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{acc.alias}</p>
                      <p className="text-[10px] text-navy-400 font-mono">{acc.awsAccountId} · {acc.awsRegion}</p>
                    </div>
                    {acc.id === selectedAwsAccountId && (
                      <Check size={12} className="text-cyan-400 flex-shrink-0" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

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

        {/* User menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-navy-800 transition-all"
          >
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-500 to-cyan-700 flex items-center justify-center">
              <span className="text-xs font-bold text-navy-900">{initials}</span>
            </div>
            <span className="text-sm text-white font-medium">{displayName || 'Account'}</span>
            <ChevronDown size={14} className="text-navy-400" />
          </button>
          {showUserMenu && (
            <div className="absolute right-0 top-full mt-1 w-56 bg-navy-900 border border-navy-700 rounded-lg shadow-xl z-50 py-1">
              <div className="px-3 py-2 border-b border-navy-800">
                <p className="text-xs font-medium text-white truncate">{displayName}</p>
                <p className="text-[10px] text-navy-400 truncate">{email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 hover:bg-navy-800 transition-colors text-left text-red-400 text-xs"
              >
                <LogOut size={12} />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
