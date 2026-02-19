import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Radar,
  AlertTriangle,
  FileText,
  Settings,
  ChevronRight,
  Shield,
} from 'lucide-react'
import Logo from './Logo'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/scan', label: 'Scan', icon: Radar },
  { path: '/findings', label: 'Findings', icon: AlertTriangle },
  { path: '/reports', label: 'Reports', icon: FileText },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar() {
  return (
    <aside className="w-60 min-h-screen flex flex-col bg-navy-900 border-r border-navy-700/50 fixed left-0 top-0 z-40">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-navy-700/50">
        <Logo size="md" />
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                  : 'text-navy-200 hover:bg-navy-800 hover:text-white border border-transparent'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={18}
                  className={isActive ? 'text-cyan-400' : 'text-navy-300 group-hover:text-white'}
                />
                <span className="flex-1">{label}</span>
                {isActive && (
                  <ChevronRight size={14} className="text-cyan-400 opacity-70" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* NIS2 Badge */}
      <div className="mx-3 mb-4 p-3 rounded-lg bg-navy-800/60 border border-navy-700/50">
        <div className="flex items-center gap-2 mb-2">
          <Shield size={14} className="text-cyan-400" />
          <span className="text-xs font-semibold text-cyan-400 font-syne">NIS2 FRAMEWORK</span>
        </div>
        <p className="text-xs text-navy-300 leading-relaxed">
          EU Directive 2022/2555<br />
          Article 21 — Security measures
        </p>
      </div>

      {/* Version */}
      <div className="px-5 py-3 border-t border-navy-700/50">
        <p className="text-xs text-navy-400">v1.0.0 — Beta</p>
      </div>
    </aside>
  )
}
