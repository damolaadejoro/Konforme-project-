import React from 'react'
import {
  ChevronDown,
  ChevronUp,
  Search,
  Filter,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ExternalLink,
  ChevronRight,
  BookOpen,
  Wrench,
  FileText,
} from 'lucide-react'
import { useFindings } from '../hooks/useFindings'
import { SeverityBadge, Card, Button, ProgressBar } from '../components/ui'
import { Severity, FindingStatus, Finding } from '../types'

const SEVERITY_OPTIONS = [
  { value: 'all', label: 'All Severities' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
  { value: 'pass', label: 'Pass' },
]

const STATUS_OPTIONS = [
  { value: 'all', label: 'All Status' },
  { value: 'fail', label: 'Failed' },
  { value: 'pass', label: 'Passed' },
  { value: 'review', label: 'Review' },
]

function FindingRow({ finding, expanded, onToggle }: {
  finding: Finding
  expanded: boolean
  onToggle: () => void
}) {
  const rowBg = expanded ? 'bg-navy-800/60 border-cyan-500/20' : 'bg-navy-900/40 border-navy-800 hover:border-navy-700 hover:bg-navy-800/40'

  return (
    <>
      <tr
        onClick={onToggle}
        className={`cursor-pointer transition-all duration-200 border-b ${rowBg}`}
      >
        <td className="px-4 py-3">
          <SeverityBadge severity={finding.severity} />
        </td>
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            {finding.status === 'pass' ? (
              <CheckCircle size={13} className="text-emerald-400 flex-shrink-0" />
            ) : (
              <XCircle size={13} className="text-red-400 flex-shrink-0" />
            )}
            <span className={`text-sm font-medium ${expanded ? 'text-cyan-400' : 'text-white'}`}>
              {finding.checkName}
            </span>
          </div>
        </td>
        <td className="px-4 py-3 hidden md:table-cell">
          <span className="text-xs text-navy-300 font-mono truncate max-w-xs block">
            {finding.resource}
          </span>
        </td>
        <td className="px-4 py-3 hidden lg:table-cell">
          <span className="text-xs font-mono font-semibold text-cyan-400/80">
            {finding.article}
          </span>
        </td>
        <td className="px-4 py-3 hidden sm:table-cell">
          <span className="text-xs text-navy-400 font-mono">{finding.region}</span>
        </td>
        <td className="px-4 py-3">
          <div className="flex items-center justify-end gap-2">
            {expanded ? (
              <ChevronUp size={16} className="text-cyan-400" />
            ) : (
              <ChevronRight size={16} className="text-navy-500" />
            )}
          </div>
        </td>
      </tr>

      {/* Expanded detail row */}
      {expanded && (
        <tr className="border-b border-cyan-500/10">
          <td colSpan={6} className="px-0 py-0">
            <div className="bg-navy-800/40 border-l-2 border-cyan-500/40 animate-slide-up">
              <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left — description + evidence */}
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <BookOpen size={13} className="text-cyan-400" />
                      <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider">Description</h4>
                    </div>
                    <p className="text-sm text-navy-200 leading-relaxed">{finding.description}</p>
                  </div>

                  {finding.evidence && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <FileText size={13} className="text-yellow-400" />
                        <h4 className="text-xs font-bold text-yellow-400 uppercase tracking-wider">Evidence</h4>
                      </div>
                      <div className="p-3 rounded-lg bg-navy-950 border border-navy-700 font-mono text-xs text-navy-300 leading-relaxed whitespace-pre-wrap">
                        {finding.evidence}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center gap-4 text-xs">
                    <div>
                      <span className="text-navy-500">Article</span>
                      <span className="ml-2 font-mono font-bold text-cyan-400">{finding.article}</span>
                    </div>
                    <div>
                      <span className="text-navy-500">Domain</span>
                      <span className="ml-2 text-white">{finding.domain}</span>
                    </div>
                    <div>
                      <span className="text-navy-500">Resource type</span>
                      <span className="ml-2 font-mono text-navy-300">{finding.resourceType}</span>
                    </div>
                  </div>
                </div>

                {/* Right — remediation */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Wrench size={13} className="text-emerald-400" />
                    <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Remediation Steps</h4>
                  </div>
                  {finding.remediationSteps.length > 0 ? (
                    <ol className="space-y-2">
                      {finding.remediationSteps.map((step, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <span className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-500/15 border border-emerald-500/25 text-emerald-400 text-xs flex items-center justify-center font-bold">
                            {i + 1}
                          </span>
                          <span className="text-sm text-navy-200 leading-relaxed">{step}</span>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-emerald-500/8 border border-emerald-500/15">
                      <CheckCircle size={14} className="text-emerald-400" />
                      <p className="text-sm text-emerald-300">No action required — control is passing.</p>
                    </div>
                  )}

                  {finding.remediationSteps.length > 0 && (
                    <button className="mt-4 flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
                      <ExternalLink size={12} />
                      View AWS documentation
                    </button>
                  )}
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function Findings() {
  const {
    findings,
    filters,
    setFilters,
    expandedId,
    toggleExpand,
    articles,
    regions,
    total,
  } = useFindings()

  const criticalCount = findings.filter(f => f.severity === 'critical').length
  const highCount = findings.filter(f => f.severity === 'high').length
  const passCount = findings.filter(f => f.status === 'pass').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold font-syne text-white">Findings</h1>
          <p className="text-sm text-navy-300 mt-1">
            {findings.length} of {total} findings shown
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2 py-1 rounded-md bg-red-500/10 border border-red-500/20 text-red-400 font-semibold">
              {criticalCount} Critical
            </span>
            <span className="px-2 py-1 rounded-md bg-orange-500/10 border border-orange-500/20 text-orange-400 font-semibold">
              {highCount} High
            </span>
            <span className="px-2 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-semibold">
              {passCount} Pass
            </span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-navy-300 mr-2">
            <Filter size={14} className="text-cyan-400" />
            <span className="font-semibold text-xs uppercase tracking-wider">Filters</span>
          </div>

          {/* Search */}
          <div className="relative flex-1 min-w-48">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-navy-400" />
            <input
              type="text"
              placeholder="Search findings..."
              value={filters.search}
              onChange={e => setFilters(p => ({ ...p, search: e.target.value }))}
              className="w-full bg-navy-900 border border-navy-700 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-navy-500 focus:outline-none focus:border-cyan-500 transition-all"
            />
          </div>

          {/* Severity filter */}
          <select
            value={filters.severity}
            onChange={e => setFilters(p => ({ ...p, severity: e.target.value as Severity | 'all' }))}
            className="bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 transition-all"
          >
            {SEVERITY_OPTIONS.map(o => (
              <option key={o.value} value={o.value} className="bg-navy-900">{o.label}</option>
            ))}
          </select>

          {/* Status filter */}
          <select
            value={filters.status}
            onChange={e => setFilters(p => ({ ...p, status: e.target.value as FindingStatus | 'all' }))}
            className="bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 transition-all"
          >
            {STATUS_OPTIONS.map(o => (
              <option key={o.value} value={o.value} className="bg-navy-900">{o.label}</option>
            ))}
          </select>

          {/* Article filter */}
          <select
            value={filters.article}
            onChange={e => setFilters(p => ({ ...p, article: e.target.value }))}
            className="bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 transition-all"
          >
            <option value="all" className="bg-navy-900">All Articles</option>
            {articles.map(a => (
              <option key={a} value={a} className="bg-navy-900">{a}</option>
            ))}
          </select>

          {/* Region filter */}
          <select
            value={filters.region}
            onChange={e => setFilters(p => ({ ...p, region: e.target.value }))}
            className="bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 transition-all"
          >
            <option value="all" className="bg-navy-900">All Regions</option>
            {regions.map(r => (
              <option key={r} value={r} className="bg-navy-900">{r}</option>
            ))}
          </select>

          {/* Clear */}
          {(filters.severity !== 'all' || filters.status !== 'all' || filters.article !== 'all' || filters.search) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setFilters({ severity: 'all', status: 'all', article: 'all', region: 'all', search: '' })}
            >
              Clear filters
            </Button>
          )}
        </div>
      </Card>

      {/* Findings table */}
      <div className="glass-card rounded-xl overflow-hidden">
        {findings.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <CheckCircle size={40} className="text-emerald-400 mb-3" />
            <h3 className="font-bold font-syne text-white mb-1">No findings match your filters</h3>
            <p className="text-sm text-navy-400">Try adjusting your filter criteria</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-navy-700">
                <th className="px-4 py-3 text-left text-xs font-semibold text-navy-400 uppercase tracking-wider w-24">Severity</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-navy-400 uppercase tracking-wider">Check Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-navy-400 uppercase tracking-wider hidden md:table-cell">Resource</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-navy-400 uppercase tracking-wider hidden lg:table-cell w-28">Article</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-navy-400 uppercase tracking-wider hidden sm:table-cell w-24">Region</th>
                <th className="px-4 py-3 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {findings.map(finding => (
                <FindingRow
                  key={finding.id}
                  finding={finding}
                  expanded={expandedId === finding.id}
                  onToggle={() => toggleExpand(finding.id)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Summary bar */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-navy-900/40 border border-navy-800">
        <p className="text-xs text-navy-400">
          Showing <span className="text-white font-medium">{findings.length}</span> findings
          {findings.length !== total && (
            <span> (filtered from {total} total)</span>
          )}
        </p>
        <div className="flex items-center gap-2 w-48">
          <AlertTriangle size={12} className="text-red-400 flex-shrink-0" />
          <ProgressBar
            value={total - passCount}
            max={total}
            color="bg-red-500"
            height="h-1.5"
          />
          <span className="text-xs text-red-400 font-semibold">{Math.round(((total - passCount) / total) * 100)}% fail</span>
        </div>
      </div>
    </div>
  )
}
