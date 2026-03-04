import React, { useState } from 'react'
import {
  FileText,
  Download,
  Shield,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Calendar,
  Building,
  Globe,
  ChevronRight,
  Printer,
  Eye,
  BarChart2,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { mockScanResult, mockFindings } from '../data/mockData'
import { Card, Button, SeverityBadge, ProgressBar, InfoTooltip } from '../components/ui'
import { format } from 'date-fns'

const priorityFindings = mockFindings.filter(f => f.status === 'fail').slice(0, 6)

function ReportPreview() {
  const date = format(new Date(mockScanResult.completedAt), 'MMMM d, yyyy')
  const score = mockScanResult.overallScore

  const roadmap = [
    {
      priority: 1,
      label: 'Week 1-2',
      title: 'Critical Remediation',
      items: ['Enable MFA on root account', 'Block public S3 buckets (3 buckets)', 'Enable multi-region CloudTrail'],
      severity: 'critical' as const,
    },
    {
      priority: 2,
      label: 'Week 3-4',
      title: 'High Priority Fixes',
      items: ['Encrypt EBS volumes', 'Migrate RDS to encrypted storage', 'Restrict SSH security groups', 'Strengthen IAM password policy'],
      severity: 'high' as const,
    },
    {
      priority: 3,
      label: 'Month 2',
      title: 'Medium Priority',
      items: ['Enable GuardDuty', 'Enable VPC flow logs', 'Rotate access keys', 'Configure AWS Backup'],
      severity: 'medium' as const,
    },
    {
      priority: 4,
      label: 'Ongoing',
      title: 'Maintenance',
      items: ['Monthly compliance scans', 'Key rotation schedule', 'Quarterly backup restore tests', 'Security training'],
      severity: 'pass' as const,
    },
  ]

  return (
    <div className="bg-white text-gray-900 rounded-xl overflow-hidden shadow-2xl">
      {/* Report header */}
      <div className="bg-[#0B1F3A] px-8 py-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <svg width="28" height="28" viewBox="0 0 40 40" fill="none">
                <path d="M20 3L5 9.5V20C5 28.284 11.716 35.5 20 37C28.284 35.5 35 28.284 35 20V9.5L20 3Z" fill="#0B1F3A" stroke="#00C2D4" strokeWidth="1.5"/>
                <text x="20" y="26" fontFamily="sans-serif" fontSize="16" fontWeight="700" fill="#00C2D4" textAnchor="middle">K</text>
              </svg>
              <span className="text-white font-bold text-lg font-syne">Konforme</span>
            </div>
            <h1 className="text-2xl font-bold text-white font-syne mt-2">NIS2 Compliance Report</h1>
            <p className="text-[#7a9cc4] text-sm mt-1">EU Directive 2022/2555 · Article 21 Assessment</p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-red-400 font-syne">{score}%</div>
            <div className="text-red-400 text-sm font-semibold">Non-Compliant</div>
            <div className="text-[#7a9cc4] text-xs mt-1">{date}</div>
          </div>
        </div>
      </div>

      <div className="p-8 space-y-8">
        {/* Executive Summary */}
        <section>
          <h2 className="text-lg font-bold font-syne text-gray-800 border-b border-gray-200 pb-2 mb-4">
            Executive Summary
          </h2>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-3">
              <AlertTriangle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-red-700 text-sm">Critical Compliance Gap Identified</p>
                <p className="text-sm text-gray-600 mt-1">
                  Your AWS environment ({mockScanResult.accountName}) scored <strong>{score}%</strong> against
                  NIS2 Article 21 security requirements. With {mockScanResult.criticalCount} critical and{' '}
                  {mockScanResult.highCount} high severity findings, immediate remediation is required to achieve
                  compliance before the NIS2 deadline.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-3">
            {[
              { label: 'Total Checks', value: mockScanResult.totalChecks, color: 'text-gray-700' },
              { label: 'Passed', value: mockScanResult.passed, color: 'text-emerald-600' },
              { label: 'Failed', value: mockScanResult.failed, color: 'text-red-600' },
              { label: 'Critical', value: mockScanResult.criticalCount, color: 'text-red-700' },
            ].map(stat => (
              <div key={stat.label} className="text-center p-3 bg-gray-50 rounded-lg">
                <div className={`text-2xl font-bold font-syne ${stat.color}`}>{stat.value}</div>
                <div className="text-xs text-gray-500 mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Score by domain */}
        <section>
          <h2 className="text-lg font-bold font-syne text-gray-800 border-b border-gray-200 pb-2 mb-4">
            Compliance by NIS2 Domain
          </h2>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={mockScanResult.domainScores} margin={{ top: 0, right: 0, left: -30, bottom: 0 }}>
              <XAxis dataKey="domain" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar dataKey="score" radius={[3, 3, 0, 0]} maxBarSize={50}>
                {mockScanResult.domainScores.map((entry, i) => (
                  <Cell key={i} fill={entry.score >= 75 ? '#10b981' : entry.score >= 50 ? '#f59e0b' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </section>

        {/* Critical findings */}
        <section>
          <h2 className="text-lg font-bold font-syne text-gray-800 border-b border-gray-200 pb-2 mb-4">
            Priority Findings
          </h2>
          <div className="space-y-2">
            {priorityFindings.map((f, i) => (
              <div key={f.id} className="flex items-center gap-3 p-3 rounded-lg border border-gray-200">
                <span className="w-6 h-6 flex-shrink-0 bg-gray-100 rounded-full flex items-center justify-center text-xs font-bold text-gray-600">
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{f.checkName}</p>
                  <p className="text-xs text-gray-500 truncate">{f.resource}</p>
                </div>
                <span className="text-xs font-mono text-blue-600 hidden sm:block">{f.article}</span>
                <div className="flex-shrink-0">
                  <SeverityBadge severity={f.severity} />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Remediation roadmap */}
        <section>
          <h2 className="text-lg font-bold font-syne text-gray-800 border-b border-gray-200 pb-2 mb-4">
            Remediation Roadmap
          </h2>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
            <div className="space-y-4">
              {roadmap.map((phase) => (
                <div key={phase.priority} className="relative flex gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#0B1F3A] flex items-center justify-center text-white text-xs font-bold z-10">
                    {phase.priority}
                  </div>
                  <div className="flex-1 pb-2">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-gray-500">{phase.label}</span>
                      <span className="font-semibold text-gray-800 text-sm">{phase.title}</span>
                    </div>
                    <ul className="space-y-1">
                      {phase.items.map((item, i) => (
                        <li key={i} className="flex items-center gap-2 text-xs text-gray-600">
                          <ChevronRight size={11} className="text-gray-400 flex-shrink-0" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Footer */}
        <div className="border-t border-gray-200 pt-4 flex items-center justify-between text-xs text-gray-400">
          <span>Generated by Konforme · {date}</span>
          <span>Confidential — for internal use only</span>
          <span>NIS2 Directive 2022/2555</span>
        </div>
      </div>
    </div>
  )
}

export default function Reports() {
  const [generating, setGenerating] = useState(false)
  const [showPreview, setShowPreview] = useState(true)

  const handleGenerate = () => {
    setGenerating(true)
    setTimeout(() => {
      setGenerating(false)
      window.print()
    }, 1500)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold font-syne text-white flex items-center gap-2">
            Compliance Report
            <InfoTooltip content="Generate and download a PDF compliance report summarizing your NIS2 posture, findings, and remediation roadmap" />
          </h1>
          <p className="text-sm text-navy-300 mt-1">
            NIS2 Article 21 assessment · {mockScanResult.accountName}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="md"
            onClick={() => setShowPreview(!showPreview)}
          >
            <Eye size={15} />
            {showPreview ? 'Hide' : 'Show'} Preview
          </Button>
          <Button
            variant="secondary"
            size="md"
          >
            <Printer size={15} />
            Print
          </Button>
          <Button
            size="md"
            loading={generating}
            onClick={handleGenerate}
          >
            {!generating && <Download size={15} />}
            {generating ? 'Generating PDF...' : 'Download PDF'}
          </Button>
        </div>
      </div>

      {/* Report metadata */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { icon: <Building size={15} className="text-cyan-400" />, label: 'Account', value: mockScanResult.accountName },
          { icon: <Globe size={15} className="text-cyan-400" />, label: 'Region', value: mockScanResult.region },
          { icon: <Calendar size={15} className="text-cyan-400" />, label: 'Scan Date', value: format(new Date(mockScanResult.completedAt), 'MMM d, yyyy') },
          { icon: <Shield size={15} className="text-cyan-400" />, label: 'Framework', value: 'NIS2 Art. 21' },
        ].map(item => (
          <div key={item.label} className="glass-card rounded-xl p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-navy-800/60">{item.icon}</div>
            <div>
              <p className="text-xs text-navy-400">{item.label}</p>
              <p className="text-sm font-semibold text-white">{item.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick stats for report */}
      <Card>
        <div className="flex items-center gap-3 mb-5">
          <BarChart2 size={16} className="text-cyan-400" />
          <h2 className="text-base font-bold font-syne text-white">Report Summary</h2>
          <InfoTooltip content="Compliance scores broken down by NIS2 Article 21 domain — each domain maps to a specific set of security requirements" size={12} />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {mockScanResult.domainScores.map(d => (
            <div key={d.domain} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-white">{d.domain}</span>
                <span className={`text-sm font-bold ${d.score >= 75 ? 'text-emerald-400' : d.score >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {d.score}%
                </span>
              </div>
              <ProgressBar value={d.score} />
              <div className="flex justify-between text-xs">
                <span className="text-navy-500 font-mono">{d.article}</span>
                <span className="text-navy-400">{d.passed}/{d.total} pass</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Findings breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <h3 className="text-sm font-bold font-syne text-white mb-4 flex items-center gap-2">
            <AlertTriangle size={14} className="text-red-400" />
            Findings to Remediate
            <InfoTooltip content="Failed checks from the latest scan that require action to achieve compliance" size={12} />
          </h3>
          <div className="space-y-2">
            {mockFindings.filter(f => f.status === 'fail').map(f => (
              <div key={f.id} className="flex items-center gap-3 py-1.5 border-b border-navy-800/60 last:border-0">
                <SeverityBadge severity={f.severity} />
                <span className="text-xs text-navy-200 flex-1 truncate">{f.checkName}</span>
                <span className="text-xs font-mono text-navy-500">{f.article}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h3 className="text-sm font-bold font-syne text-white mb-4 flex items-center gap-2">
            <CheckCircle size={14} className="text-emerald-400" />
            Passing Controls
            <InfoTooltip content="Checks that your AWS environment currently passes — these controls are compliant" size={12} />
          </h3>
          <div className="space-y-2">
            {mockFindings.filter(f => f.status === 'pass').map(f => (
              <div key={f.id} className="flex items-center gap-3 py-1.5 border-b border-navy-800/60 last:border-0">
                <CheckCircle size={13} className="text-emerald-400 flex-shrink-0" />
                <span className="text-xs text-navy-200 flex-1 truncate">{f.checkName}</span>
                <span className="text-xs font-mono text-navy-500">{f.article}</span>
              </div>
            ))}
          </div>

          <div className="mt-4 p-3 rounded-lg bg-emerald-500/8 border border-emerald-500/15">
            <div className="flex items-center gap-2">
              <TrendingUp size={14} className="text-emerald-400" />
              <p className="text-xs text-emerald-300 font-medium">
                {mockScanResult.passed} of {mockScanResult.totalChecks} controls are passing.
                Focus on critical remediations to achieve compliance.
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Report preview */}
      {showPreview && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <FileText size={15} className="text-cyan-400" />
            <h2 className="text-base font-bold font-syne text-white">Report Preview</h2>
            <span className="text-xs text-navy-400 px-2 py-0.5 rounded-full bg-navy-800 border border-navy-700">PDF format</span>
          </div>
          <div className="rounded-xl overflow-hidden shadow-2xl shadow-navy-950/50 ring-1 ring-navy-700">
            <ReportPreview />
          </div>
        </div>
      )}
    </div>
  )
}
