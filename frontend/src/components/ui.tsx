import React from 'react'
import { Severity } from '../types'

// Severity Badge
export function SeverityBadge({ severity }: { severity: Severity }) {
  const styles: Record<Severity, string> = {
    critical: 'bg-red-500/15 text-red-400 border-red-500/25',
    high: 'bg-orange-500/15 text-orange-400 border-orange-500/25',
    medium: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25',
    low: 'bg-blue-500/15 text-blue-400 border-blue-500/25',
    pass: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
  }
  const label: Record<Severity, string> = {
    critical: 'Critical',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
    pass: 'Pass',
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border ${styles[severity]}`}
    >
      {label[severity]}
    </span>
  )
}

// Status Dot
export function StatusDot({ status }: { status: 'pass' | 'fail' | 'review' | 'scanning' | 'pending' }) {
  const colors = {
    pass: 'bg-emerald-400',
    fail: 'bg-red-400',
    review: 'bg-yellow-400',
    scanning: 'bg-cyan-400 animate-pulse',
    pending: 'bg-navy-500',
  }

  return (
    <span className={`inline-block w-2 h-2 rounded-full ${colors[status]}`} />
  )
}

// Card
interface CardProps {
  children: React.ReactNode
  className?: string
  glow?: boolean
  onClick?: () => void
}

export function Card({ children, className = '', glow = false, onClick }: CardProps) {
  return (
    <div
      className={`glass-card rounded-xl p-5 ${glow ? 'glow-cyan' : ''} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

// Stat Card
interface StatCardProps {
  label: string
  value: string | number
  icon?: React.ReactNode
  accent?: string
  trend?: string
  trendUp?: boolean
}

export function StatCard({ label, value, icon, accent, trend }: StatCardProps) {
  return (
    <div className="glass-card rounded-xl p-5 flex items-start justify-between">
      <div>
        <p className="text-xs text-navy-300 font-medium uppercase tracking-wider mb-1">{label}</p>
        <p className={`text-2xl font-bold font-syne ${accent || 'text-white'}`}>{value}</p>
        {trend && <p className="text-xs text-navy-400 mt-1">{trend}</p>}
      </div>
      {icon && (
        <div className="p-2.5 rounded-lg bg-navy-800/60">
          {icon}
        </div>
      )}
    </div>
  )
}

// Progress Bar
interface ProgressBarProps {
  value: number
  max?: number
  color?: string
  height?: string
  animated?: boolean
}

export function ProgressBar({ value, max = 100, color, height = 'h-2', animated = false }: ProgressBarProps) {
  const pct = Math.min(100, (value / max) * 100)
  const barColor = color || (pct >= 75 ? 'bg-emerald-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500')

  return (
    <div className={`w-full ${height} bg-navy-800 rounded-full overflow-hidden`}>
      <div
        className={`h-full rounded-full transition-all duration-700 ${barColor} ${animated ? 'animate-pulse' : ''}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

// Section header
interface SectionHeaderProps {
  title: string
  subtitle?: string
  action?: React.ReactNode
}

export function SectionHeader({ title, subtitle, action }: SectionHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-5">
      <div>
        <h2 className="text-lg font-bold font-syne text-white">{title}</h2>
        {subtitle && <p className="text-sm text-navy-300 mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}

// Button
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  children: React.ReactNode
}

export function Button({ variant = 'primary', size = 'md', loading, children, className = '', ...props }: ButtonProps) {
  const base = 'inline-flex items-center justify-center gap-2 font-semibold rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary: 'bg-cyan-500 hover:bg-cyan-400 text-navy-950 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30',
    secondary: 'bg-navy-800 hover:bg-navy-700 text-white border border-navy-600',
    danger: 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20',
    ghost: 'hover:bg-navy-800 text-navy-300 hover:text-white',
  }
  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }

  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {loading && (
        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  )
}

// Input
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  icon?: React.ReactNode
}

export function Input({ label, error, icon, className = '', ...props }: InputProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="text-xs font-semibold text-navy-200 uppercase tracking-wider">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-navy-400">
            {icon}
          </div>
        )}
        <input
          className={`w-full bg-navy-900 border border-navy-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-navy-400
            focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-all
            ${icon ? 'pl-10' : ''}
            ${error ? 'border-red-500' : ''}
            ${className}`}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}

// Select
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  options: { value: string; label: string }[]
}

export function Select({ label, options, className = '', ...props }: SelectProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="text-xs font-semibold text-navy-200 uppercase tracking-wider">
          {label}
        </label>
      )}
      <select
        className={`w-full bg-navy-900 border border-navy-700 rounded-lg px-3 py-2.5 text-sm text-white
          focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-all
          appearance-none ${className}`}
        {...props}
      >
        {options.map(o => (
          <option key={o.value} value={o.value} className="bg-navy-900">
            {o.label}
          </option>
        ))}
      </select>
    </div>
  )
}
