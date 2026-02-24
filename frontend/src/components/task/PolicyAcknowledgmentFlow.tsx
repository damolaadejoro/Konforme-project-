import React, { useState, useEffect } from 'react'
import { FileText, ChevronRight, Calendar, User, CheckCircle } from 'lucide-react'
import { MockTask } from '../../data/mockTasks'
import { format } from 'date-fns'

interface PolicyAcknowledgmentFlowProps {
  task: MockTask
  onComplete: (employeeName: string) => void
  onStepChange?: (step: number) => void
}

export default function PolicyAcknowledgmentFlow({ task, onComplete, onStepChange }: PolicyAcknowledgmentFlowProps) {
  const [step, setStep] = useState(1)
  const [hasReadPolicy, setHasReadPolicy] = useState(false)
  const [confirmedName, setConfirmedName] = useState(task.employeeName)

  const totalSteps = 4

  // Notify parent of step changes for progress bar
  useEffect(() => {
    onStepChange?.(step)
  }, [step, onStepChange])

  // Step 1: Welcome
  if (step === 1) {
    return (
      <div className="space-y-5 sm:space-y-6 animate-fade-in">
        <div className="text-center">
          <p className="text-xs sm:text-sm text-gray-500 mb-1">Step {step} of {totalSteps}</p>
          <h1 className="text-[22px] sm:text-2xl md:text-3xl font-bold text-navy-900 mb-2 leading-tight">
            Hi {task.employeeName.split(' ')[0]} 👋
          </h1>
          <p className="text-[15px] sm:text-base text-gray-600">
            {task.company} has assigned you a compliance task
          </p>
        </div>

        {/* Task Card */}
        <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-lg sm:rounded-2xl p-5 sm:p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start gap-4">
            <div className="p-3 bg-cyan-100 rounded-xl flex-shrink-0">
              <FileText size={24} className="text-cyan-600 sm:w-7 sm:h-7" />
            </div>
            <div className="flex-1 w-full sm:w-auto">
              <h2 className="text-base sm:text-lg font-semibold text-navy-900 mb-2 leading-snug">
                {task.taskName}
              </h2>
              <div className="space-y-2 text-sm sm:text-[15px]">
                <div className="flex items-center gap-2 text-gray-600">
                  <User size={14} className="flex-shrink-0" />
                  <span className="leading-relaxed">Assigned by: <span className="font-medium text-gray-800">{task.assignedBy}</span></span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <Calendar size={14} className="flex-shrink-0" />
                  <span className="leading-relaxed">Due: <span className="font-medium text-gray-800">{format(new Date(task.dueDate), 'MMMM d, yyyy')}</span></span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 text-sm sm:text-[15px] text-gray-600">
              <div className="w-2 h-2 rounded-full bg-cyan-500 flex-shrink-0" />
              <span className="leading-relaxed">Estimated time: <span className="font-medium text-gray-800">Takes about 1 minute</span></span>
            </div>
          </div>
        </div>

        {/* Start Button */}
        <button
          onClick={() => setStep(2)}
          className="w-full bg-cyan-500 hover:bg-cyan-600 active:bg-cyan-700 text-white font-semibold py-[14px] sm:py-4 px-6 rounded-lg sm:rounded-xl transition-colors flex items-center justify-center gap-2 shadow-sm hover:shadow-md text-base sm:text-[17px] min-h-[52px]"
        >
          Start Task
          <ChevronRight size={18} />
        </button>
      </div>
    )
  }

  // Step 2: Policy Review
  if (step === 2) {
    return (
      <div className="space-y-5 sm:space-y-6 animate-fade-in">
        <div className="text-center">
          <p className="text-xs sm:text-sm text-gray-500 mb-1">Step {step} of {totalSteps}</p>
          <h1 className="text-[22px] sm:text-2xl md:text-3xl font-bold text-navy-900 mb-2 leading-tight">
            {task.policyContent?.title}
          </h1>
          <p className="text-[15px] sm:text-base text-gray-600">
            Please read the key points below
          </p>
        </div>

        {/* Policy Summary Card */}
        <div className="bg-gradient-to-br from-blue-50 to-white border border-blue-200 rounded-lg sm:rounded-2xl p-5 sm:p-6 shadow-sm">
          <ul className="space-y-4">
            {task.policyContent?.summary.map((point, index) => (
              <li key={index} className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-100 flex items-center justify-center mt-0.5">
                  <span className="text-xs font-semibold text-cyan-600">{index + 1}</span>
                </div>
                <span className="text-[15px] sm:text-base text-gray-700 leading-relaxed">{point}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Checkbox */}
        <div className="bg-white border-2 border-gray-200 rounded-lg sm:rounded-xl p-4 sm:p-5">
          <label className="flex items-start gap-3 cursor-pointer min-h-[44px]">
            <input
              type="checkbox"
              checked={hasReadPolicy}
              onChange={(e) => setHasReadPolicy(e.target.checked)}
              className="mt-0.5 w-5 h-5 sm:w-6 sm:h-6 rounded border-gray-300 text-cyan-500 focus:ring-cyan-500 cursor-pointer flex-shrink-0"
            />
            <span className="text-[15px] sm:text-base text-gray-700 select-none leading-relaxed">
              I have read and understood the above policy
            </span>
          </label>
        </div>

        {/* Continue Button */}
        <button
          onClick={() => setStep(3)}
          disabled={!hasReadPolicy}
          className={`w-full font-semibold py-[14px] sm:py-4 px-6 rounded-lg sm:rounded-xl transition-all flex items-center justify-center gap-2 text-base sm:text-[17px] min-h-[52px] ${
            hasReadPolicy
              ? 'bg-cyan-500 hover:bg-cyan-600 active:bg-cyan-700 text-white shadow-sm hover:shadow-md'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
        >
          Continue
          <ChevronRight size={18} />
        </button>
      </div>
    )
  }

  // Step 3: Confirmation
  if (step === 3) {
    return (
      <div className="space-y-5 sm:space-y-6 animate-fade-in">
        <div className="text-center">
          <p className="text-xs sm:text-sm text-gray-500 mb-1">Step {step} of {totalSteps}</p>
          <h1 className="text-[22px] sm:text-2xl md:text-3xl font-bold text-navy-900 mb-2 leading-tight">
            Confirm Your Acknowledgment
          </h1>
          <p className="text-[15px] sm:text-base text-gray-600">
            Review and confirm the details below
          </p>
        </div>

        {/* Confirmation Form */}
        <div className="bg-white border border-gray-200 rounded-lg sm:rounded-2xl p-5 sm:p-6 space-y-5 shadow-sm">
          <div>
            <label className="block text-sm sm:text-[15px] font-medium text-gray-700 mb-2">
              Your Name
            </label>
            <input
              type="text"
              value={confirmedName}
              onChange={(e) => setConfirmedName(e.target.value)}
              className="w-full px-4 py-3 sm:py-3.5 bg-gray-50 border border-gray-200 rounded-lg sm:rounded-xl text-[15px] sm:text-base text-gray-900 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100 min-h-[48px]"
            />
          </div>

          <div>
            <label className="block text-sm sm:text-[15px] font-medium text-gray-700 mb-2">
              Date
            </label>
            <input
              type="text"
              value={format(new Date(), 'MMMM d, yyyy')}
              readOnly
              className="w-full px-4 py-3 sm:py-3.5 bg-gray-100 border border-gray-200 rounded-lg sm:rounded-xl text-[15px] sm:text-base text-gray-600 cursor-not-allowed min-h-[48px]"
            />
          </div>
        </div>

        {/* Statement */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg sm:rounded-xl p-4 sm:p-5">
          <p className="text-sm sm:text-[15px] text-gray-700 leading-relaxed">
            By clicking <span className="font-semibold">Confirm</span>, I acknowledge that I have read and understood the{' '}
            <span className="font-semibold">{task.policyContent?.title}</span> and agree to comply with its requirements.
          </p>
        </div>

        {/* Buttons */}
        <div className="space-y-3">
          <button
            onClick={() => {
              onComplete(confirmedName)
              setStep(4)
            }}
            disabled={!confirmedName.trim()}
            className={`w-full font-semibold py-[14px] sm:py-4 px-6 rounded-lg sm:rounded-xl transition-all text-base sm:text-[17px] min-h-[52px] ${
              confirmedName.trim()
                ? 'bg-cyan-500 hover:bg-cyan-600 active:bg-cyan-700 text-white shadow-sm hover:shadow-md'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            Confirm & Submit
          </button>
          <button
            onClick={() => setStep(2)}
            className="w-full text-gray-600 hover:text-gray-800 active:text-gray-900 font-medium py-3 transition-colors text-[15px] sm:text-base min-h-[48px]"
          >
            ← Back
          </button>
        </div>
      </div>
    )
  }

  // Step 4: Complete
  return (
    <div className="space-y-5 sm:space-y-6 animate-fade-in text-center">
      <div>
        <p className="text-xs sm:text-sm text-gray-500 mb-4">Step {step} of {totalSteps}</p>
        <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 bg-green-100 rounded-full mb-5 sm:mb-6 animate-scale-in">
          <CheckCircle size={40} className="text-green-600 sm:w-12 sm:h-12" />
        </div>
        <h1 className="text-[26px] sm:text-3xl md:text-4xl font-bold text-navy-900 mb-3 leading-tight">
          All Done!
        </h1>
        <p className="text-base sm:text-lg text-gray-600 mb-6 sm:mb-8 leading-relaxed px-2">
          Your acknowledgment has been recorded. Thank you for keeping {task.company} secure.
        </p>
      </div>

      {/* Completion Card */}
      <div className="bg-gradient-to-br from-green-50 to-white border border-green-200 rounded-lg sm:rounded-2xl p-5 sm:p-6 text-left shadow-sm">
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm sm:text-[15px] font-medium text-gray-600">Task</span>
            <span className="text-sm sm:text-[15px] font-semibold text-gray-900 text-right">{task.taskName}</span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm sm:text-[15px] font-medium text-gray-600">Completed by</span>
            <span className="text-sm sm:text-[15px] font-semibold text-gray-900 text-right">{confirmedName}</span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm sm:text-[15px] font-medium text-gray-600">Date</span>
            <span className="text-sm sm:text-[15px] font-semibold text-gray-900">{format(new Date(), 'MMM d, yyyy')}</span>
          </div>
          <div className="flex items-center justify-between gap-3 pt-3 border-t border-green-200">
            <span className="text-sm sm:text-[15px] font-medium text-gray-600">Status</span>
            <div className="flex items-center gap-2">
              <CheckCircle size={16} className="text-green-600" />
              <span className="text-sm sm:text-[15px] font-semibold text-green-600">Completed</span>
            </div>
          </div>
        </div>
      </div>

      {/* Note */}
      <div className="pt-4">
        <p className="text-sm sm:text-[15px] text-gray-500">
          You can now close this tab
        </p>
      </div>
    </div>
  )
}
