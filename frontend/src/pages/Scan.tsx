import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Radar,
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  Terminal,
  ChevronRight,
  AlertTriangle,
  Eye,
  EyeOff,
  Play,
  RotateCcw,
} from 'lucide-react'
import { useScan } from '../hooks/useScan'
import { AWSCredentials } from '../types'
import { Card, Button, Input, Select, SeverityBadge, ProgressBar } from '../components/ui'

const REGIONS = [
  'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
  'eu-north-1', 'us-east-1', 'us-east-2', 'us-west-2', 'ap-southeast-1',
]

function ScanTerminal({ checks, currentIndex, progress, status }: {
  checks: ReturnType<typeof useScan>['checks']
  currentIndex: number
  progress: number
  status: string
}) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [checks])

  const started = checks.filter(c => c.status !== 'pending')

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      {/* Terminal header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-navy-900 border-b border-navy-700">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/70" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/70" />
          </div>
          <span className="ml-2 text-xs text-navy-400 font-mono">konforme-scanner — bash</span>
        </div>
        <div className="flex items-center gap-2">
          <Terminal size={13} className="text-cyan-400" />
          <span className="text-xs text-cyan-400 font-mono">
            {status === 'scanning' ? `Running check ${currentIndex + 1}/${checks.length}` :
             status === 'complete' ? `Scan complete · ${checks.length} checks` : 'Ready'}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      {status === 'scanning' && (
        <div className="px-4 py-2 bg-navy-950">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-navy-400 font-mono">Progress</span>
            <span className="text-xs text-cyan-400 font-mono font-bold">{progress}%</span>
          </div>
          <ProgressBar value={progress} animated height="h-1" color="bg-cyan-500" />
        </div>
      )}

      {/* Terminal body */}
      <div className="h-96 overflow-y-auto bg-navy-950 p-4 font-mono text-xs space-y-1.5">
        {/* Boot messages */}
        <div className="text-navy-400 mb-3">
          <p className="text-cyan-500 font-bold">$ konforme scan --framework nis2 --region eu-west-1</p>
          <p className="mt-1 text-navy-500">Initializing AWS session...</p>
          <p className="text-navy-500">Loading NIS2 Article 21 ruleset (15 checks)...</p>
          <p className="text-navy-500">Starting compliance scan...</p>
          <p className="text-navy-500 mb-3">─────────────────────────────────────────</p>
        </div>

        {started.map((check, i) => (
          <div
            key={check.id}
            className="flex items-start gap-3"
            style={{
              animation: 'fadeIn 0.3s ease-out forwards',
            }}
          >
            {/* Icon */}
            <div className="mt-0.5 flex-shrink-0">
              {check.status === 'scanning' && (
                <span className="inline-block w-4 h-4">
                  <svg className="animate-spin" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" stroke="#00C2D4" strokeWidth="2" strokeDasharray="18" strokeDashoffset="6" />
                  </svg>
                </span>
              )}
              {check.status === 'pass' && (
                <CheckCircle size={14} className="text-emerald-400" />
              )}
              {check.status === 'fail' && (
                <XCircle size={14} className={
                  check.severity === 'critical' ? 'text-red-400' :
                  check.severity === 'high' ? 'text-orange-400' :
                  'text-yellow-400'
                } />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3">
                <span className={
                  check.status === 'scanning' ? 'text-cyan-300 animate-pulse' :
                  check.status === 'pass' ? 'text-emerald-300' :
                  check.status === 'fail' ? 'text-red-300' : 'text-navy-400'
                }>
                  {check.checkName}
                </span>
                <span className="text-navy-600">·</span>
                <span className="text-navy-500 text-xs">{check.resource}</span>
              </div>

              {check.status !== 'scanning' && (
                <div className="flex items-center gap-3 mt-0.5">
                  <span className={`text-xs ${check.status === 'pass' ? 'text-emerald-500' : 'text-red-400'}`}>
                    {check.status === 'pass' ? '[PASS]' : '[FAIL]'}
                  </span>
                  {check.severity && (
                    <span className={`text-xs ${
                      check.severity === 'critical' ? 'text-red-400' :
                      check.severity === 'high' ? 'text-orange-400' :
                      'text-yellow-400'
                    }`}>
                      severity:{check.severity}
                    </span>
                  )}
                  {check.duration && (
                    <span className="text-navy-600">{check.duration}ms</span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Cursor */}
        {status === 'scanning' && (
          <div className="text-cyan-400">
            <span className="cursor-blink">█</span>
          </div>
        )}

        {/* Completion summary */}
        {status === 'complete' && (
          <div className="mt-4 pt-4 border-t border-navy-800">
            <p className="text-navy-500">─────────────────────────────────────────</p>
            <p className="text-white font-bold mt-2">Scan Complete</p>
            <p className="text-navy-400">Total: {checks.length} checks · <span className="text-emerald-400">4 passed</span> · <span className="text-red-400">11 failed</span></p>
            <p className="text-navy-400">Critical: <span className="text-red-400">3</span> · High: <span className="text-orange-400">4</span> · Medium: <span className="text-yellow-400">4</span></p>
            <p className="text-navy-400 mt-1">Overall NIS2 Score: <span className="text-red-400 font-bold">47%</span> (Non-Compliant)</p>
            <p className="text-cyan-500 mt-2">$ _<span className="cursor-blink">█</span></p>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}

function ScanComplete({ onReset }: { onReset: () => void }) {
  const navigate = useNavigate()

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Score banner */}
      <div className="p-5 rounded-xl bg-red-500/8 border border-red-500/20">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle size={18} className="text-red-400" />
              <h3 className="font-bold font-syne text-red-400">Scan Complete — Action Required</h3>
            </div>
            <p className="text-sm text-navy-300">
              Your AWS environment scored <span className="font-bold text-red-400">47%</span> — below the minimum compliance threshold.
              11 of 15 checks failed.
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold font-syne text-red-400">47%</div>
            <div className="text-xs text-red-500 font-semibold">Non-Compliant</div>
          </div>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Critical', value: 3, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'High', value: 4, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' },
          { label: 'Medium', value: 4, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
          { label: 'Passed', value: 4, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
        ].map(item => (
          <div key={item.label} className={`rounded-lg p-3 border ${item.bg} text-center`}>
            <div className={`text-2xl font-bold font-syne ${item.color}`}>{item.value}</div>
            <div className="text-xs text-navy-400 mt-0.5">{item.label}</div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button onClick={() => navigate('/findings')} size="lg" className="flex-1">
          View All Findings <ChevronRight size={16} />
        </Button>
        <Button onClick={() => navigate('/')} variant="secondary" size="lg">
          <Shield size={16} />
          Dashboard
        </Button>
        <Button onClick={onReset} variant="ghost" size="lg">
          <RotateCcw size={16} />
          New Scan
        </Button>
      </div>
    </div>
  )
}

export default function Scan() {
  const [credentials, setCredentials] = useState<AWSCredentials>({
    accessKey: '',
    secretKey: '',
    region: 'eu-west-1',
    accountName: '',
  })
  const [showSecret, setShowSecret] = useState(false)
  const { status, checks, currentCheckIndex, progress, startScan, resetScan } = useScan()

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault()
    startScan(credentials)
  }

  const handleDemo = () => {
    startScan({
      accessKey: 'DEMO_ACCESS_KEY',
      secretKey: 'DEMO_SECRET_KEY',
      region: 'eu-west-1',
      accountName: 'EU-Production',
    })
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold font-syne text-white">NIS2 Compliance Scan</h1>
        <p className="text-sm text-navy-300 mt-1">
          Connect your AWS account to scan against NIS2 Article 21 requirements
        </p>
      </div>

      {status === 'idle' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Credentials form */}
          <Card className="lg:col-span-2">
            <h2 className="text-base font-bold font-syne text-white mb-5 flex items-center gap-2">
              <Shield size={16} className="text-cyan-400" />
              AWS Credentials
            </h2>

            <form onSubmit={handleStart} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Account Name"
                  placeholder="e.g. EU-Production"
                  value={credentials.accountName}
                  onChange={e => setCredentials(p => ({ ...p, accountName: e.target.value }))}
                />
                <Select
                  label="AWS Region"
                  value={credentials.region}
                  onChange={e => setCredentials(p => ({ ...p, region: e.target.value }))}
                  options={REGIONS.map(r => ({ value: r, label: r }))}
                />
              </div>
              <Input
                label="Access Key ID"
                placeholder="AKIAIOSFODNN7EXAMPLE"
                value={credentials.accessKey}
                onChange={e => setCredentials(p => ({ ...p, accessKey: e.target.value }))}
              />
              <div className="relative">
                <Input
                  label="Secret Access Key"
                  type={showSecret ? 'text' : 'password'}
                  placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                  value={credentials.secretKey}
                  onChange={e => setCredentials(p => ({ ...p, secretKey: e.target.value }))}
                />
                <button
                  type="button"
                  onClick={() => setShowSecret(!showSecret)}
                  className="absolute right-3 top-8 text-navy-400 hover:text-white transition-colors"
                >
                  {showSecret ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              <div className="p-3 rounded-lg bg-navy-900/60 border border-navy-700">
                <p className="text-xs text-navy-300">
                  <span className="text-cyan-400 font-semibold">Recommended:</span> Create a read-only IAM role with{' '}
                  <span className="font-mono text-white">SecurityAudit</span> policy attached.
                  Credentials are never stored.
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="submit" size="lg" className="flex-1">
                  <Play size={16} />
                  Start Scan
                </Button>
                <Button type="button" variant="secondary" size="lg" onClick={handleDemo}>
                  <Radar size={16} />
                  Run Demo
                </Button>
              </div>
            </form>
          </Card>

          {/* What we scan */}
          <Card>
            <h2 className="text-sm font-bold font-syne text-white mb-4 flex items-center gap-2">
              <Terminal size={14} className="text-cyan-400" />
              What Gets Scanned
            </h2>
            <div className="space-y-2">
              {[
                { article: 'Art 21(2)(i)', label: 'IAM & Access Control', checks: 5, color: 'text-cyan-400' },
                { article: 'Art 21(2)(a)', label: 'Monitoring & Logging', checks: 3, color: 'text-purple-400' },
                { article: 'Art 21(2)(h)', label: 'Encryption', checks: 4, color: 'text-blue-400' },
                { article: 'Art 21(2)(b/e)', label: 'Business Continuity', checks: 3, color: 'text-emerald-400' },
              ].map(item => (
                <div key={item.article} className="flex items-center justify-between p-2.5 rounded-lg bg-navy-900/40">
                  <div>
                    <span className={`text-xs font-mono font-bold ${item.color}`}>{item.article}</span>
                    <p className="text-xs text-white mt-0.5">{item.label}</p>
                  </div>
                  <span className="text-xs text-navy-400">{item.checks} checks</span>
                </div>
              ))}
            </div>

            <div className="mt-4 p-3 rounded-lg bg-cyan-500/8 border border-cyan-500/15">
              <div className="flex items-center gap-2 mb-1">
                <Clock size={13} className="text-cyan-400" />
                <span className="text-xs font-semibold text-cyan-400">Est. duration</span>
              </div>
              <p className="text-xs text-navy-300">~2-5 minutes depending on account size</p>
            </div>
          </Card>
        </div>
      )}

      {(status === 'scanning' || status === 'complete') && (
        <div className="space-y-6">
          {/* Account info bar */}
          <div className="flex items-center gap-4 p-3 rounded-lg bg-navy-900/60 border border-navy-700">
            <Shield size={16} className="text-cyan-400" />
            <div className="flex items-center gap-4 text-sm">
              <span className="text-white font-medium">EU-Production</span>
              <span className="text-navy-500">·</span>
              <span className="text-navy-400 font-mono">123456789012</span>
              <span className="text-navy-500">·</span>
              <span className="text-navy-400">eu-west-1</span>
            </div>
            {status === 'scanning' && (
              <div className="ml-auto flex items-center gap-2 text-xs text-cyan-400">
                <span className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
                Scanning in progress...
              </div>
            )}
          </div>

          {/* Terminal */}
          <ScanTerminal
            checks={checks}
            currentIndex={currentCheckIndex}
            progress={progress}
            status={status}
          />

          {/* Check list */}
          <Card>
            <h2 className="text-sm font-bold font-syne text-white mb-4 flex items-center gap-2">
              <Radar size={14} className="text-cyan-400" />
              Check Status
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {checks.map((check, i) => (
                <div
                  key={check.id}
                  className={`flex items-center gap-3 p-2.5 rounded-lg border transition-all duration-300 ${
                    check.status === 'scanning'
                      ? 'bg-cyan-500/8 border-cyan-500/20'
                      : check.status === 'pass'
                      ? 'bg-emerald-500/5 border-emerald-500/15'
                      : check.status === 'fail'
                      ? 'bg-red-500/5 border-red-500/10'
                      : 'bg-navy-900/40 border-navy-800'
                  }`}
                >
                  <div className="flex-shrink-0">
                    {check.status === 'pending' && <div className="w-2 h-2 rounded-full bg-navy-600" />}
                    {check.status === 'scanning' && <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />}
                    {check.status === 'pass' && <CheckCircle size={13} className="text-emerald-400" />}
                    {check.status === 'fail' && <XCircle size={13} className={
                      check.severity === 'critical' ? 'text-red-400' :
                      check.severity === 'high' ? 'text-orange-400' : 'text-yellow-400'
                    } />}
                  </div>
                  <span className={`text-xs flex-1 truncate ${
                    check.status === 'pending' ? 'text-navy-500' :
                    check.status === 'scanning' ? 'text-cyan-300' :
                    check.status === 'pass' ? 'text-emerald-300' : 'text-white'
                  }`}>
                    {check.checkName}
                  </span>
                  {check.severity && check.status === 'fail' && (
                    <SeverityBadge severity={check.severity} />
                  )}
                </div>
              ))}
            </div>
          </Card>

          {/* Completion actions */}
          {status === 'complete' && <ScanComplete onReset={resetScan} />}
        </div>
      )}
    </div>
  )
}
