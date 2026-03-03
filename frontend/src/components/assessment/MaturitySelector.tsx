import React from 'react'
import type { MaturityLevel } from '../../types/assessment'
import { MATURITY_LABELS, MATURITY_COLORS } from '../../types/assessment'
import { Tooltip } from '../ui'

interface MaturitySelectorProps {
  value: MaturityLevel
  onChange: (level: MaturityLevel) => void
  disabled?: boolean
}

const LEVELS: Array<{ level: number; label: string; tooltip: string }> = [
  { level: 0, label: 'Not Addressed', tooltip: 'Not addressed — no measures in place' },
  { level: 1, label: 'Aware', tooltip: 'Initial — ad-hoc, informal measures exist' },
  { level: 2, label: 'Ad-hoc', tooltip: 'Managed — documented processes are in place' },
  { level: 3, label: 'Documented', tooltip: 'Defined — standardized and consistently applied' },
  { level: 4, label: 'Practiced', tooltip: 'Practiced — regularly reviewed and continuously improved' },
]

export default function MaturitySelector({ value, onChange, disabled }: MaturitySelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {LEVELS.map(({ level, label, tooltip }) => {
        const isSelected = value === level
        const color = MATURITY_COLORS[level]

        return (
          <Tooltip key={level} content={tooltip}>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onChange(level as MaturityLevel)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-200 ${
                isSelected
                  ? 'ring-1 ring-offset-1 ring-offset-navy-900'
                  : 'opacity-60 hover:opacity-100'
              } disabled:cursor-not-allowed disabled:opacity-30`}
              style={{
                backgroundColor: isSelected ? `${color}20` : 'transparent',
                borderColor: isSelected ? `${color}80` : '#2a3f5f',
                color: isSelected ? color : '#94b4d1',
                ...(isSelected ? { ringColor: color } : {}),
              }}
            >
              <span className="mr-1">{level}</span>
              {label}
            </button>
          </Tooltip>
        )
      })}

      {/* N/A option */}
      <Tooltip content="This requirement does not apply to your organization">
        <button
          type="button"
          disabled={disabled}
          onClick={() => onChange(null)}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-200 ${
            value === null
              ? 'bg-navy-700/50 border-navy-500 text-white ring-1 ring-navy-500 ring-offset-1 ring-offset-navy-900'
              : 'border-navy-700 text-navy-400 opacity-60 hover:opacity-100'
          } disabled:cursor-not-allowed disabled:opacity-30`}
        >
          N/A
        </button>
      </Tooltip>
    </div>
  )
}
