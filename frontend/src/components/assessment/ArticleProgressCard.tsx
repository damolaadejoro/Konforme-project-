import React from 'react'
import type { ArticleScore } from '../../types/assessment'
import { ProgressBar } from '../ui'

interface ArticleProgressCardProps {
  articleScore: ArticleScore
  isActive: boolean
  onClick: () => void
}

export default function ArticleProgressCard({ articleScore, isActive, onClick }: ArticleProgressCardProps) {
  const { article, title, score, answered, total } = articleScore
  const color = score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : score > 0 ? '#ef4444' : '#4a6580'
  const progress = total > 0 ? Math.round((answered / total) * 100) : 0

  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg border transition-all duration-200 ${
        isActive
          ? 'bg-cyan-500/10 border-cyan-500/30'
          : 'bg-navy-900/40 border-navy-800 hover:border-navy-600'
      }`}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-mono text-[#94b4d1]">{article}</span>
        {answered > 0 && (
          <span className="text-xs font-bold" style={{ color }}>
            {score}%
          </span>
        )}
      </div>
      <h4 className={`text-[13px] font-semibold leading-snug mb-2 ${
        isActive ? 'text-cyan-400' : 'text-white'
      }`}>
        {title}
      </h4>
      <div className="space-y-1">
        <ProgressBar
          value={progress}
          color={isActive ? 'bg-cyan-500' : undefined}
          height="h-1"
        />
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-[#94b4d1]">
            {answered}/{total} answered
          </span>
          {answered === total && answered > 0 && (
            <span className="text-[11px] text-emerald-400 font-semibold">Complete</span>
          )}
        </div>
      </div>
    </button>
  )
}
