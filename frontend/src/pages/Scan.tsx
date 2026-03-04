import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Radar,
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  Terminal,
  AlertTriangle,
  Info,
  Play,
  RotateCcw,
  Link,
} from 'lucide-react'
import { useScan } from '../hooks/useScan'
import { useAuth } from '../context/AuthContext'
import { AwsAccountCredentials } from '../types'
import { Card, Button, Input, Select, SeverityBadge, ProgressBar, InfoTooltip, Tooltip as AppTooltip } from '../components/ui'

const REGIONS = [
  'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
  'eu-north-1', 'us-east-1', 'us-east-2', 'us-west-2', 'ap-southeast-1',
]

function ScanTerminal({ checks, currentIndex, progress, status, scanRegion }: {
  checks: ReturnType<typeof useScan>['checks']
  currentIndex: number
  progress: number
  status: string
  scanRegion: string
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
          <p className="text-cyan-500 font-bold">$ konforme scan --framework nis2 --region {scanRegion}</p>
          <p className="mt-1 text-navy-500">Initializing AWS session...</p>
          <p className="text-navy-500">Loading NIS2 Article 21 ruleset (25 checks)...</p>
          <p className="text-navy-500">Starting compliance scan...</p>
          <p className="text-navy-500 mb-3">─────────────────────────────────────────</p>
        </div>

        {started.map((check) => (
          <div
            key={check.id}
            className="flex items-start gap-3"
            style={{ animation: 'fadeIn 0.3s ease-out forwards' }}
          >
            <div className="mt-0.5 flex-shrink-0">
              {check.status === 'scanning' && (
                <span className="inline-block w-4 h-4">
                  <svg className="animate-spin" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" stroke="#00C2D4" strokeWidth="2" strokeDasharray="18" strokeDashoffset="6" />
                  </svg>
                </span>
              )}
              {check.status === 'pass' && <CheckCircle size={14} className="text-emerald-400" />}
              {check.status === 'info' && <Info size={14} className="text-sky-400" />}
              {check.status === 'warn' && <AlertTriangle size={14} className="text-amber-400" />}
              {check.status === 'fail' && (
                <XCircle size={14} className={
                  check.severity === 'critical' ? 'text-red-400' :
                  check.severity === 'high' ? 'text-orange-400' :
                  check.severity === 'medium' ? 'text-yellow-400' :
                  'text-blue-400'
                } />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3">
                <span className={
                  check.status === 'scanning' ? 'text-cyan-300 animate-pulse' :
                  check.status === 'pass' ? 'text-emerald-300' :
                  check.status === 'info' ? 'text-sky-300' :
                  check.status === 'warn' ? 'text-amber-300' :
                  check.status === 'fail' ? (
                    check.severity === 'critical' ? 'text-red-300' :
                    check.severity === 'high' ? 'text-orange-300' :
                    check.severity === 'medium' ? 'text-yellow-300' : 'text-blue-300'
                  ) : 'text-navy-400'
                }>
                  {check.checkName}
                </span>
                <span className="text-navy-600">·</span>
                <span className="text-navy-500 text-xs">{check.resource}</span>
              </div>
              {check.status !== 'scanning' && check.status !== 'pending' && (
                <div className="flex items-center gap-3 mt-0.5">
                  <span className={`text-xs ${
                    check.status === 'pass' ? 'text-emerald-500' :
                    check.status === 'info' ? 'text-sky-400' :
                    check.status === 'warn' ? 'text-amber-400' : 'text-red-400'
                  }`}>
                    {check.status === 'pass' ? '[PASS]' : check.status === 'info' ? '[NOTE]' : check.status === 'warn' ? '[WARN]' : '[FAIL]'}
                  </span>
                  {check.severity && check.status === 'fail' && (
                    <span className={`text-xs ${
                      check.severity === 'critical' ? 'text-red-400' :
                      check.severity === 'high' ? 'text-orange-400' :
                      check.severity === 'medium' ? 'text-yellow-400' :
                      'text-blue-400'
                    }`}>
                      severity:{check.severity}
                    </span>
                  )}
                  {check.duration && <span className="text-navy-600">{check.duration}ms</span>}
                </div>
              )}
            </div>
          </div>
        ))}

        {status === 'scanning' && (
          <div className="text-cyan-400">
            <span className="cursor-blink">█</span>
          </div>
        )}

        {status === 'complete' && (
          <div className="mt-4 pt-4 border-t border-navy-800">
            <p className="text-navy-500">─────────────────────────────────────────</p>
            <p className="text-white font-bold mt-2">Scan Complete</p>
            <p className="text-navy-400">
              Total: {checks.length} checks ·{' '}
              <span className="text-emerald-400">{checks.filter(c => c.status === 'pass').length} passed</span> ·{' '}
              <span className="text-red-400">{checks.filter(c => c.status === 'fail').length} failed</span>
              {checks.filter(c => c.status === 'info').length > 0 && (
                <> · <span className="text-sky-400">{checks.filter(c => c.status === 'info').length} not applicable</span></>
              )}
              {checks.filter(c => c.status === 'warn').length > 0 && (
                <> · <span className="text-amber-400">{checks.filter(c => c.status === 'warn').length} warnings</span></>
              )}
            </p>
            <p className="text-cyan-500 mt-2">$ _<span className="cursor-blink">█</span></p>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}

function ScanComplete({ onReset, scanResult }: { onReset: () => void; scanResult: ReturnType<typeof useScan>['scanResult'] }) {
  const navigate = useNavigate()

  const passed = scanResult?.passed ?? 0
  const failed = scanResult?.failed ?? 0
  const critical = scanResult?.criticalCount ?? 0
  const high = scanResult?.highCount ?? 0
  const medium = scanResult?.mediumCount ?? 0
  const low = scanResult?.lowCount ?? 0
  const score = scanResult?.overallScore ?? 0
  const total = scanResult?.totalChecks ?? 0

  const isCompliant = score >= 70
  const scoreClasses = isCompliant
    ? { bg: 'bg-emerald-500/8 border-emerald-500/20', text: 'text-emerald-400', label: 'text-emerald-500' }
    : score >= 50
    ? { bg: 'bg-yellow-500/8 border-yellow-500/20', text: 'text-yellow-400', label: 'text-yellow-500' }
    : { bg: 'bg-red-500/8 border-red-500/20', text: 'text-red-400', label: 'text-red-500' }

  return (
    <div className="space-y-4 animate-fade-in">
      <div className={`p-5 rounded-xl ${scoreClasses.bg}`}>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              {isCompliant
                ? <CheckCircle size={18} className={scoreClasses.text} />
                : <AlertTriangle size={18} className={scoreClasses.text} />
              }
              <h3 className={`font-bold font-syne ${scoreClasses.text}`}>
                {isCompliant ? 'Scan Complete — Compliant' : 'Scan Complete — Action Required'}
              </h3>
            </div>
            <p className="text-sm text-navy-300">
              Your AWS environment scored <span className={`font-bold ${scoreClasses.text}`}>{score}%</span> — {failed} of {total} checks failed.
            </p>
          </div>
          <div className="text-right">
            <div className={`text-4xl font-bold font-syne ${scoreClasses.text}`}>{score}%</div>
            <div className={`text-xs font-semibold ${scoreClasses.label}`}>{isCompliant ? 'Compliant' : 'Non-Compliant'}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-3">
        {[
          { label: 'Critical', value: critical, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'High', value: high, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' },
          { label: 'Medium', value: medium, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
          { label: 'Low', value: low, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
          { label: 'Passed', value: passed, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
        ].map(item => (
          <div key={item.label} className={`rounded-lg p-3 border ${item.bg} text-center`}>
            <div className={`text-2xl font-bold font-syne ${item.color}`}>{item.value}</div>
            <div className="text-xs text-navy-400 mt-0.5">{item.label}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <Button onClick={() => navigate('/')} variant="secondary" size="lg" className="flex-1">
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
  const { accountName, awsAccounts, selectedAwsAccountId, addAwsAccount, selectAwsAccount } = useAuth()
  const [showAddForm, setShowAddForm] = useState(awsAccounts.length === 0)
  const [addCreds, setAddCreds] = useState<AwsAccountCredentials>({
    alias: '',
    accessKeyId: '',
    secretAccessKey: '',
    sessionToken: '',
    region: 'eu-west-1',
  })
  const [connectError, setConnectError] = useState<string | null>(null)
  const [addingAccount, setAddingAccount] = useState(false)
  const { status, checks, currentCheckIndex, progress, scanResult, error, startScan, resetScan } = useScan()

  const selectedAccount = awsAccounts.find(a => a.id === selectedAwsAccountId)
  const scanRegion = scanResult?.region || selectedAccount?.awsRegion || addCreds.region

  const handleAddAwsAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    setConnectError(null)
    setAddingAccount(true)
    try {
      const newAcc = await addAwsAccount(
        addCreds.alias,
        addCreds.accessKeyId,
        addCreds.secretAccessKey,
        addCreds.sessionToken || null,
        addCreds.region
      )
      selectAwsAccount(newAcc.id)
      setShowAddForm(false)
      setAddCreds({ alias: '', accessKeyId: '', secretAccessKey: '', sessionToken: '', region: 'eu-west-1' })
    } catch (err) {
      setConnectError(err instanceof Error ? err.message : 'Failed to add AWS account')
    } finally {
      setAddingAccount(false)
    }
  }

  const handleRunScan = () => {
    startScan('api', selectedAwsAccountId || undefined)
  }

  const handleDemo = () => {
    startScan('demo')
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-syne text-white flex items-center gap-2">
          NIS2 Compliance Scan
          <InfoTooltip content="Run automated scans against your AWS infrastructure to check compliance with NIS2 Article 21 technical requirements" />
        </h1>
        <p className="text-sm text-navy-300 mt-1">
          Scan your AWS account against NIS2 Article 21 requirements
        </p>
      </div>

      {status === 'idle' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold font-syne text-white flex items-center gap-2">
                  <Link size={16} className="text-emerald-400" />
                  {accountName}
                </h2>
              </div>

              {/* AWS Account selector */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-navy-400 uppercase tracking-wider font-semibold">
                    {awsAccounts.length === 0 ? 'Add Your First AWS Account' : 'AWS Accounts'}
                  </span>
                  {awsAccounts.length > 0 && (
                    <Button variant="ghost" size="sm" onClick={() => setShowAddForm(!showAddForm)} className="text-cyan-400 hover:text-cyan-300">
                      {showAddForm ? 'Cancel' : '+ Add Account'}
                    </Button>
                  )}
                </div>
                {awsAccounts.map(acc => (
                  <div
                    key={acc.id}
                    onClick={() => selectAwsAccount(acc.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      acc.id === selectedAwsAccountId
                        ? 'bg-cyan-500/8 border-cyan-500/30'
                        : 'bg-navy-900/40 border-navy-800 hover:border-navy-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-white">{acc.alias}</p>
                        <p className="text-xs text-navy-400 font-mono mt-0.5">{acc.awsAccountId} · {acc.awsRegion}</p>
                      </div>
                      {acc.id === selectedAwsAccountId && (
                        <div className="w-2 h-2 rounded-full bg-cyan-400" />
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Add AWS Account form */}
              {(showAddForm || awsAccounts.length === 0) && (
                <form onSubmit={handleAddAwsAccount} className="space-y-3 p-4 rounded-lg bg-navy-900/60 border border-navy-700">
                  <h3 className="text-sm font-semibold text-white">
                    {awsAccounts.length === 0 ? 'Add Your First AWS Account' : 'Add AWS Account'}
                  </h3>
                  <Input
                    label="Alias"
                    placeholder="e.g. Production, Staging"
                    value={addCreds.alias}
                    onChange={e => setAddCreds(p => ({ ...p, alias: e.target.value }))}
                    required
                  />
                  <Input
                    label="Access Key ID"
                    placeholder="AKIA..."
                    value={addCreds.accessKeyId}
                    onChange={e => setAddCreds(p => ({ ...p, accessKeyId: e.target.value }))}
                    required
                  />
                  <Input
                    label="Secret Access Key"
                    type="password"
                    placeholder="Enter secret access key"
                    value={addCreds.secretAccessKey}
                    onChange={e => setAddCreds(p => ({ ...p, secretAccessKey: e.target.value }))}
                    required
                  />
                  <Input
                    label="Session Token (optional)"
                    placeholder="Paste session token"
                    value={addCreds.sessionToken}
                    onChange={e => setAddCreds(p => ({ ...p, sessionToken: e.target.value }))}
                  />
                  <Select
                    label="AWS Region"
                    value={addCreds.region}
                    onChange={e => setAddCreds(p => ({ ...p, region: e.target.value }))}
                    options={REGIONS.map(r => ({ value: r, label: r }))}
                  />
                  {connectError && (
                    <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20">
                      <p className="text-xs text-red-400">{connectError}</p>
                    </div>
                  )}
                  <Button type="submit" size="sm" loading={addingAccount} className="w-full">
                    Add AWS Account
                  </Button>
                </form>
              )}

              <div className="flex gap-3">
                <AppTooltip content="Scan the selected AWS account against NIS2 requirements using live API calls">
                  <Button onClick={handleRunScan} size="lg" className="flex-1" disabled={!selectedAwsAccountId}>
                    <Play size={16} />
                    Run Scan
                  </Button>
                </AppTooltip>
                <AppTooltip content="Run a simulated scan with sample data — no AWS credentials needed">
                  <Button type="button" variant="secondary" size="lg" onClick={handleDemo}>
                    <Radar size={16} />
                    Run Demo
                  </Button>
                </AppTooltip>
              </div>
            </div>
          </Card>

          {/* What we scan */}
          <Card>
            <h2 className="text-sm font-bold font-syne text-white mb-4 flex items-center gap-2">
              <Terminal size={14} className="text-cyan-400" />
              What Gets Scanned
              <InfoTooltip content="Each scan checks your AWS resources against specific NIS2 Article 21 requirements and auto-updates control statuses" size={12} />
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

      {/* Error state */}
      {status === 'error' && (
        <Card>
          <div className="p-6 text-center">
            <AlertTriangle size={48} className="text-red-400 mx-auto mb-4" />
            <h3 className="text-lg font-bold font-syne text-white mb-2">Scan Failed</h3>
            <p className="text-sm text-navy-300 mb-4">{error || 'An unexpected error occurred.'}</p>
            <div className="flex gap-3 justify-center">
              <Button onClick={resetScan} variant="secondary">
                <RotateCcw size={16} />
                Try Again
              </Button>
              <Button onClick={handleDemo} variant="ghost">
                <Radar size={16} />
                Run Demo Instead
              </Button>
            </div>
          </div>
        </Card>
      )}

      {(status === 'scanning' || status === 'complete') && (
        <div className="space-y-6">
          <div className="flex items-center gap-4 p-3 rounded-lg bg-navy-900/60 border border-navy-700">
            <Shield size={16} className="text-cyan-400" />
            <div className="flex items-center gap-4 text-sm">
              <span className="text-white font-medium">{selectedAccount?.alias || accountName || 'Demo Account'}</span>
              <span className="text-navy-500">·</span>
              <span className="text-navy-400 font-mono">{selectedAccount?.awsAccountId || '123456789012'}</span>
              <span className="text-navy-500">·</span>
              <span className="text-navy-400">{scanRegion}</span>
            </div>
            {status === 'scanning' && (
              <div className="ml-auto flex items-center gap-2 text-xs text-cyan-400">
                <span className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
                Scanning in progress...
              </div>
            )}
          </div>

          <ScanTerminal
            checks={checks}
            currentIndex={currentCheckIndex}
            progress={progress}
            status={status}
            scanRegion={scanRegion}
          />

          <Card>
            <h2 className="text-sm font-bold font-syne text-white mb-4 flex items-center gap-2">
              <Radar size={14} className="text-cyan-400" />
              Check Status
              <InfoTooltip content="Real-time status of each individual compliance check as the scan runs" size={12} />
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {checks.map((check) => (
                <div
                  key={check.id}
                  className={`flex items-center gap-3 p-2.5 rounded-lg border transition-all duration-300 ${
                    check.status === 'scanning'
                      ? 'bg-cyan-500/8 border-cyan-500/20'
                      : check.status === 'pass'
                      ? 'bg-emerald-500/5 border-emerald-500/15'
                      : check.status === 'info'
                      ? 'bg-sky-500/5 border-sky-500/15'
                      : check.status === 'warn'
                      ? 'bg-amber-500/5 border-amber-500/15'
                      : check.status === 'fail'
                      ? 'bg-red-500/5 border-red-500/10'
                      : 'bg-navy-900/40 border-navy-800'
                  }`}
                >
                  <div className="flex-shrink-0">
                    {check.status === 'pending' && <div className="w-2 h-2 rounded-full bg-navy-600" />}
                    {check.status === 'scanning' && <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />}
                    {check.status === 'pass' && <CheckCircle size={13} className="text-emerald-400" />}
                    {check.status === 'info' && <Info size={13} className="text-sky-400" />}
                    {check.status === 'warn' && <AlertTriangle size={13} className="text-amber-400" />}
                    {check.status === 'fail' && <XCircle size={13} className={
                      check.severity === 'critical' ? 'text-red-400' :
                      check.severity === 'high' ? 'text-orange-400' :
                      check.severity === 'medium' ? 'text-yellow-400' : 'text-blue-400'
                    } />}
                  </div>
                  <span className={`text-xs flex-1 truncate ${
                    check.status === 'pending' ? 'text-navy-500' :
                    check.status === 'scanning' ? 'text-cyan-300' :
                    check.status === 'pass' ? 'text-emerald-300' :
                    check.status === 'info' ? 'text-sky-300' :
                    check.status === 'warn' ? 'text-amber-300' : 'text-white'
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

          {status === 'complete' && <ScanComplete onReset={resetScan} scanResult={scanResult} />}
        </div>
      )}
    </div>
  )
}
