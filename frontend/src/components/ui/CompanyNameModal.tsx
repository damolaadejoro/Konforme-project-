import React, { useState } from 'react'
import { X, Building2 } from 'lucide-react'

interface CompanyNameModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (companyName: string) => void
  isGenerating?: boolean
}

export default function CompanyNameModal({ isOpen, onClose, onConfirm, isGenerating = false }: CompanyNameModalProps) {
  const [companyName, setCompanyName] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (companyName.trim()) {
      onConfirm(companyName.trim())
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-navy-950/80 backdrop-blur-sm"
        onClick={!isGenerating ? onClose : undefined}
      />

      {/* Modal */}
      <div className="relative bg-navy-900 border border-navy-700 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-scale-in">
        {/* Close button */}
        {!isGenerating && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 text-navy-400 hover:text-white hover:bg-navy-800 rounded-lg transition-all"
          >
            <X size={18} />
          </button>
        )}

        {/* Icon */}
        <div className="flex items-center justify-center w-14 h-14 bg-cyan-500/10 border border-cyan-500/20 rounded-xl mb-4">
          <Building2 size={24} className="text-cyan-400" />
        </div>

        {/* Content */}
        <h2 className="text-xl font-bold font-syne text-white mb-2">
          Generate NIS2 Report
        </h2>
        <p className="text-sm text-navy-300 mb-6">
          Enter your company name to generate a professional compliance report
        </p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="companyName" className="block text-sm font-medium text-navy-200 mb-2">
              Company Name
            </label>
            <input
              id="companyName"
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g., Acme Corporation"
              disabled={isGenerating}
              className="w-full px-4 py-3 bg-navy-800 border border-navy-700 rounded-lg text-white placeholder-navy-400 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              autoFocus
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isGenerating}
              className="flex-1 px-4 py-3 bg-navy-800 text-navy-200 hover:bg-navy-700 hover:text-white border border-navy-700 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!companyName.trim() || isGenerating}
              className="flex-1 px-4 py-3 bg-cyan-500 text-white hover:bg-cyan-600 rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20"
            >
              {isGenerating ? 'Generating...' : 'Generate Report'}
            </button>
          </div>
        </form>

        {/* Loading indicator */}
        {isGenerating && (
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-cyan-400">
            <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            <span>Creating your PDF report...</span>
          </div>
        )}
      </div>
    </div>
  )
}
