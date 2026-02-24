import React, { useState, useMemo } from 'react'
import {
  Shield,
  Search,
  Filter,
  X,
  Upload,
  ChevronRight,
  Calendar,
  User,
  FileText,
  Trash2,
  AlertCircle,
  CheckCircle,
  Users as UsersIcon,
  Mail,
  Clock
} from 'lucide-react'
import { useControls } from '../hooks/useControls'
import { Card, Button, Select, Input, SeverityBadge } from '../components/ui'
import { Control, ControlCategory, ControlStatus } from '../types/controls'
import { format } from 'date-fns'

const statusColors: Record<ControlStatus, string> = {
  'Not Started': 'text-red-400 bg-red-500/10 border-red-500/20',
  'Planned': 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  'Partial': 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  'Implemented': 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
}

const categoryIcons = {
  Technical: '⚙️',
  Organizational: '📋',
  People: '👥'
}

function ControlDrawer({
  control,
  onClose,
  onUpdate,
  onAddEvidence,
  onRemoveEvidence,
  campaigns
}: {
  control: Control
  onClose: () => void
  onUpdate: (updates: Partial<Control>) => void
  onAddEvidence: (evidence: any) => void
  onRemoveEvidence: (evidenceId: string) => void
  campaigns: any[]
}) {
  const [isEditingStatus, setIsEditingStatus] = useState(false)
  const [isEditingOwner, setIsEditingOwner] = useState(false)
  const [isEditingDueDate, setIsEditingDueDate] = useState(false)
  const [isEditingNotes, setIsEditingNotes] = useState(false)
  const [isAddingEmployee, setIsAddingEmployee] = useState(false)

  const [tempStatus, setTempStatus] = useState(control.status)
  const [tempOwner, setTempOwner] = useState(control.owner)
  const [tempDueDate, setTempDueDate] = useState(control.dueDate || '')
  const [tempNotes, setTempNotes] = useState(control.notes)

  // Employee assignment form
  const [employeeEmails, setEmployeeEmails] = useState('')
  const [taskType, setTaskType] = useState<'acknowledge' | 'quiz'>('acknowledge')
  const [deadline, setDeadline] = useState('')

  const handleSaveStatus = () => {
    onUpdate({ status: tempStatus })
    setIsEditingStatus(false)
  }

  const handleSaveOwner = () => {
    onUpdate({ owner: tempOwner })
    setIsEditingOwner(false)
  }

  const handleSaveDueDate = () => {
    onUpdate({ dueDate: tempDueDate || null })
    setIsEditingDueDate(false)
  }

  const handleSaveNotes = () => {
    onUpdate({ notes: tempNotes })
    setIsEditingNotes(false)
  }

  const handleUploadEvidence = () => {
    // Mock file upload
    const mockEvidence = {
      filename: 'Evidence_Document.pdf',
      uploadedAt: new Date().toISOString(),
      uploadedBy: 'Current User',
      fileSize: '1.2 MB'
    }
    onAddEvidence(mockEvidence)
  }

  const handleAssignEmployees = () => {
    // This would trigger the campaign creation in the parent
    console.log('Creating campaign with:', { employeeEmails, taskType, deadline })
    setIsAddingEmployee(false)
    setEmployeeEmails('')
    setDeadline('')
  }

  return (
    <div className="fixed inset-0 bg-navy-950/80 backdrop-blur-sm z-50 flex items-center justify-end">
      <div
        className="absolute inset-0"
        onClick={onClose}
      />
      <div className="relative w-full max-w-2xl h-full bg-navy-900 border-l border-navy-700 overflow-y-auto animate-slide-in-right">
        <div className="sticky top-0 z-10 bg-navy-900 border-b border-navy-700 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield size={20} className="text-cyan-400" />
            <h2 className="text-lg font-bold font-syne text-white">Control Details</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-navy-800 transition-colors"
          >
            <X size={18} className="text-navy-400" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Title and Article */}
          <div>
            <div className="flex items-start gap-3 mb-3">
              <span className="text-2xl">{categoryIcons[control.category]}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-mono text-cyan-400">{control.article}</span>
                  <span className="text-xs text-[#4a6580]">•</span>
                  <span className="text-xs text-[#94b4d1]">{control.articleArea}</span>
                  {control.isAutoPopulated && (
                    <>
                      <span className="text-xs text-navy-500">•</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        Auto
                      </span>
                    </>
                  )}
                  {control.isPeopleControl && (
                    <>
                      <span className="text-xs text-navy-500">•</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        People
                      </span>
                    </>
                  )}
                </div>
                <h3 className="text-xl font-bold font-syne text-white leading-snug">{control.title}</h3>
              </div>
            </div>
            <p className="text-[14px] text-[#CBD8E8] leading-relaxed">{control.description}</p>
          </div>

          {/* Maturity Status */}
          <div className="p-4 rounded-lg bg-navy-800/60 border border-navy-700">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-[#94b4d1] uppercase tracking-wider">
                Maturity Status
              </label>
              {!isEditingStatus && !control.isAutoPopulated && (
                <button
                  onClick={() => setIsEditingStatus(true)}
                  className="text-xs text-cyan-400 hover:text-cyan-300"
                >
                  Edit
                </button>
              )}
            </div>

            {isEditingStatus ? (
              <div className="flex items-center gap-2">
                <select
                  value={tempStatus}
                  onChange={(e) => setTempStatus(e.target.value as ControlStatus)}
                  className="flex-1 px-3 py-2 bg-navy-900 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
                >
                  <option value="Not Started">Not Started</option>
                  <option value="Planned">Planned</option>
                  <option value="Partial">Partial</option>
                  <option value="Implemented">Implemented</option>
                </select>
                <Button size="sm" onClick={handleSaveStatus}>Save</Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setTempStatus(control.status)
                    setIsEditingStatus(false)
                  }}
                >
                  Cancel
                </Button>
              </div>
            ) : (
              <span className={`inline-flex items-center px-3 py-1.5 rounded-lg border text-sm font-semibold ${statusColors[control.status]}`}>
                {control.status}
              </span>
            )}

            {control.isAutoPopulated && (
              <p className="mt-2 text-[13px] text-purple-400 flex items-center gap-1">
                <AlertCircle size={12} />
                Auto-populated from AWS scanner — status updates automatically
              </p>
            )}
          </div>

          {/* Owner */}
          <div className="p-4 rounded-lg bg-navy-800/60 border border-navy-700">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-[#94b4d1] uppercase tracking-wider flex items-center gap-2">
                <User size={14} />
                Owner
              </label>
              {!isEditingOwner && (
                <button
                  onClick={() => setIsEditingOwner(true)}
                  className="text-xs text-cyan-400 hover:text-cyan-300"
                >
                  Edit
                </button>
              )}
            </div>

            {isEditingOwner ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={tempOwner}
                  onChange={(e) => setTempOwner(e.target.value)}
                  className="flex-1 px-3 py-2 bg-navy-900 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
                  placeholder="Owner name or role"
                />
                <Button size="sm" onClick={handleSaveOwner}>Save</Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setTempOwner(control.owner)
                    setIsEditingOwner(false)
                  }}
                >
                  Cancel
                </Button>
              </div>
            ) : (
              <p className="text-[14px] text-white">{control.owner}</p>
            )}
          </div>

          {/* Due Date */}
          <div className="p-4 rounded-lg bg-navy-800/60 border border-navy-700">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-[#94b4d1] uppercase tracking-wider flex items-center gap-2">
                <Calendar size={14} />
                Due Date
              </label>
              {!isEditingDueDate && (
                <button
                  onClick={() => setIsEditingDueDate(true)}
                  className="text-xs text-cyan-400 hover:text-cyan-300"
                >
                  Edit
                </button>
              )}
            </div>

            {isEditingDueDate ? (
              <div className="flex items-center gap-2">
                <input
                  type="date"
                  value={tempDueDate}
                  onChange={(e) => setTempDueDate(e.target.value)}
                  className="flex-1 px-3 py-2 bg-navy-900 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
                />
                <Button size="sm" onClick={handleSaveDueDate}>Save</Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setTempDueDate(control.dueDate || '')
                    setIsEditingDueDate(false)
                  }}
                >
                  Cancel
                </Button>
              </div>
            ) : (
              <p className="text-[14px] text-white">
                {control.dueDate ? format(new Date(control.dueDate), 'MMMM d, yyyy') : 'No due date set'}
              </p>
            )}
          </div>

          {/* Evidence */}
          <div className="p-4 rounded-lg bg-navy-800/60 border border-navy-700">
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-semibold text-[#94b4d1] uppercase tracking-wider flex items-center gap-2">
                <FileText size={14} />
                Evidence ({control.evidence.length})
              </label>
              {!control.isAutoPopulated && (
                <Button size="sm" variant="secondary" onClick={handleUploadEvidence}>
                  <Upload size={14} />
                  Upload
                </Button>
              )}
            </div>

            {control.evidence.length === 0 ? (
              <p className="text-[13px] text-[#94b4d1] italic">No evidence uploaded yet</p>
            ) : (
              <div className="space-y-2">
                {control.evidence.map(ev => (
                  <div
                    key={ev.id}
                    className="flex items-center gap-3 p-3 rounded-lg bg-navy-900/60 border border-navy-800 hover:border-navy-700 transition-colors"
                  >
                    <FileText size={16} className="text-cyan-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[14px] font-medium text-white truncate">{ev.filename}</p>
                      <p className="text-[13px] text-[#94b4d1]">
                        {format(new Date(ev.uploadedAt), 'MMM d, yyyy')} • {ev.uploadedBy} • {ev.fileSize}
                      </p>
                    </div>
                    {!control.isAutoPopulated && (
                      <button
                        onClick={() => onRemoveEvidence(ev.id)}
                        className="p-1.5 rounded hover:bg-navy-800 text-navy-400 hover:text-red-400 transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Notes */}
          <div className="p-4 rounded-lg bg-navy-800/60 border border-navy-700">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-[#94b4d1] uppercase tracking-wider">
                Notes
              </label>
              {!isEditingNotes && (
                <button
                  onClick={() => setIsEditingNotes(true)}
                  className="text-xs text-cyan-400 hover:text-cyan-300"
                >
                  Edit
                </button>
              )}
            </div>

            {isEditingNotes ? (
              <div className="space-y-2">
                <textarea
                  value={tempNotes}
                  onChange={(e) => setTempNotes(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 bg-navy-900 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500 resize-none"
                  placeholder="Add notes about this control..."
                />
                <div className="flex items-center gap-2">
                  <Button size="sm" onClick={handleSaveNotes}>Save</Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setTempNotes(control.notes)
                      setIsEditingNotes(false)
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-[14px] text-[#CBD8E8] leading-relaxed whitespace-pre-wrap">
                {control.notes || 'No notes added'}
              </p>
            )}
          </div>

          {/* Employee Assignment (for People controls only) */}
          {control.isPeopleControl && (
            <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
              <div className="flex items-center justify-between mb-3">
                <label className="text-[15px] font-semibold text-emerald-400 flex items-center gap-2">
                  <UsersIcon size={16} />
                  Assign to Employees
                </label>
              </div>

              {campaigns.length > 0 ? (
                <div className="space-y-3">
                  {campaigns.map(campaign => {
                    const completionRate = Math.round(
                      (campaign.tasks.filter((t: any) => t.status === 'completed').length / campaign.tasks.length) * 100
                    )
                    const isOverdue = new Date(campaign.deadline) < new Date() && completionRate < 80

                    return (
                      <div key={campaign.id} className="p-3 rounded-lg bg-navy-900/60 border border-navy-800">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xs px-2 py-0.5 rounded bg-navy-800 text-[#CBD8E8]">
                              {campaign.taskType === 'quiz' ? 'Training Quiz' : 'Policy Acknowledgment'}
                            </span>
                            {isOverdue && (
                              <span className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                                At Risk
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-[#94b4d1]">
                            Due: {format(new Date(campaign.deadline), 'MMM d, yyyy')}
                          </span>
                        </div>

                        <div className="mb-2">
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-[#94b4d1]">
                              {campaign.tasks.filter((t: any) => t.status === 'completed').length} of {campaign.tasks.length} completed
                            </span>
                            <span className={completionRate >= 80 ? 'text-emerald-400' : 'text-yellow-400'}>
                              {completionRate}%
                            </span>
                          </div>
                          <div className="h-1.5 bg-navy-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all ${completionRate >= 80 ? 'bg-emerald-500' : 'bg-yellow-500'}`}
                              style={{ width: `${completionRate}%` }}
                            />
                          </div>
                        </div>

                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-cyan-400 hover:text-cyan-300 -ml-2"
                        >
                          View Details <ChevronRight size={14} />
                        </Button>
                      </div>
                    )
                  })}

                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setIsAddingEmployee(true)}
                    className="w-full"
                  >
                    <UsersIcon size={14} />
                    Create New Campaign
                  </Button>
                </div>
              ) : !isAddingEmployee ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsAddingEmployee(true)}
                  className="w-full"
                >
                  <UsersIcon size={14} />
                  Assign to Employees
                </Button>
              ) : null}

              {isAddingEmployee && (
                <div className="space-y-3 mt-3 pt-3 border-t border-emerald-500/20">
                  <div>
                    <label className="text-xs text-[#94b4d1] mb-1 block">Employee Emails (one per line)</label>
                    <textarea
                      value={employeeEmails}
                      onChange={(e) => setEmployeeEmails(e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 bg-navy-900 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500 resize-none"
                      placeholder="alice.johnson@company.com&#10;bob.martinez@company.com"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-[#94b4d1] mb-1 block">Task Type</label>
                    <select
                      value={taskType}
                      onChange={(e) => setTaskType(e.target.value as 'acknowledge' | 'quiz')}
                      className="w-full px-3 py-2 bg-navy-900 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
                    >
                      <option value="acknowledge">Acknowledge Policy</option>
                      <option value="quiz">Complete Training Quiz</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs text-[#94b4d1] mb-1 block">Deadline</label>
                    <input
                      type="date"
                      value={deadline}
                      onChange={(e) => setDeadline(e.target.value)}
                      className="w-full px-3 py-2 bg-navy-900 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <Button size="sm" onClick={handleAssignEmployees} disabled={!employeeEmails || !deadline}>
                      <Mail size={14} />
                      Send Tasks
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setIsAddingEmployee(false)
                        setEmployeeEmails('')
                        setDeadline('')
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Metadata */}
          <div className="pt-4 border-t border-navy-700 text-xs text-[#94b4d1]">
            <div className="flex items-center gap-2">
              <Clock size={12} />
              <span>Last updated: {format(new Date(control.lastUpdated), 'MMM d, yyyy \'at\' h:mm a')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ControlsLibrary() {
  const {
    controls,
    selectedControl,
    setSelectedControl,
    updateControl,
    addEvidence,
    removeEvidence,
    filterControls,
    getCampaignsForControl
  } = useControls()

  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<ControlCategory | ''>('')
  const [statusFilter, setStatusFilter] = useState<ControlStatus | ''>('')
  const [articleAreaFilter, setArticleAreaFilter] = useState('')

  const filteredControls = useMemo(() => {
    return filterControls(
      categoryFilter || undefined,
      statusFilter || undefined,
      articleAreaFilter || undefined,
      searchQuery || undefined
    )
  }, [controls, searchQuery, categoryFilter, statusFilter, articleAreaFilter])

  const articleAreas = useMemo(() => {
    return Array.from(new Set(controls.map(c => c.articleArea)))
  }, [controls])

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[26px] font-bold font-syne text-white">Controls Library</h1>
          <p className="text-[14px] text-[#CBD8E8] mt-1">
            Manage all NIS2 Article 21 controls and evidence
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[14px] text-[#94b4d1]">
            {filteredControls.length} of {controls.length} controls
          </span>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-navy-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search controls by title, description, or article..."
              className="w-full pl-10 pr-4 py-2.5 bg-navy-800 border border-navy-700 rounded-lg text-white text-sm placeholder-navy-400 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Filter row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-[#94b4d1] mb-1 block">Category</label>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value as ControlCategory | '')}
                className="w-full px-3 py-2 bg-navy-800 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
              >
                <option value="">All Categories</option>
                <option value="Technical">Technical</option>
                <option value="Organizational">Organizational</option>
                <option value="People">People</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-[#94b4d1] mb-1 block">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as ControlStatus | '')}
                className="w-full px-3 py-2 bg-navy-800 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
              >
                <option value="">All Statuses</option>
                <option value="Not Started">Not Started</option>
                <option value="Planned">Planned</option>
                <option value="Partial">Partial</option>
                <option value="Implemented">Implemented</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-[#94b4d1] mb-1 block">Article 21 Area</label>
              <select
                value={articleAreaFilter}
                onChange={(e) => setArticleAreaFilter(e.target.value)}
                className="w-full px-3 py-2 bg-navy-800 border border-navy-700 rounded-lg text-white text-sm focus:outline-none focus:border-cyan-500"
              >
                <option value="">All Areas</option>
                {articleAreas.map(area => (
                  <option key={area} value={area}>{area}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Active filters */}
          {(searchQuery || categoryFilter || statusFilter || articleAreaFilter) && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-[#94b4d1]">Active filters:</span>
              {searchQuery && (
                <span className="text-xs px-2 py-1 rounded bg-navy-800 text-white flex items-center gap-1">
                  Search: "{searchQuery}"
                  <button onClick={() => setSearchQuery('')} className="text-navy-400 hover:text-white">
                    <X size={12} />
                  </button>
                </span>
              )}
              {categoryFilter && (
                <span className="text-xs px-2 py-1 rounded bg-navy-800 text-white flex items-center gap-1">
                  {categoryFilter}
                  <button onClick={() => setCategoryFilter('')} className="text-navy-400 hover:text-white">
                    <X size={12} />
                  </button>
                </span>
              )}
              {statusFilter && (
                <span className="text-xs px-2 py-1 rounded bg-navy-800 text-white flex items-center gap-1">
                  {statusFilter}
                  <button onClick={() => setStatusFilter('')} className="text-navy-400 hover:text-white">
                    <X size={12} />
                  </button>
                </span>
              )}
              {articleAreaFilter && (
                <span className="text-xs px-2 py-1 rounded bg-navy-800 text-white flex items-center gap-1">
                  {articleAreaFilter}
                  <button onClick={() => setArticleAreaFilter('')} className="text-navy-400 hover:text-white">
                    <X size={12} />
                  </button>
                </span>
              )}
              <button
                onClick={() => {
                  setSearchQuery('')
                  setCategoryFilter('')
                  setStatusFilter('')
                  setArticleAreaFilter('')
                }}
                className="text-xs text-cyan-400 hover:text-cyan-300"
              >
                Clear all
              </button>
            </div>
          )}
        </div>
      </Card>

      {/* Controls Table */}
      <Card>
        {filteredControls.length === 0 ? (
          <div className="text-center py-12">
            <Filter size={48} className="text-navy-600 mx-auto mb-4" />
            <h3 className="text-lg font-bold font-syne text-white mb-2">
              No controls found
            </h3>
            <p className="text-[14px] text-[#94b4d1]">
              Try adjusting your filters or search query
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredControls.map((control, i) => (
              <div
                key={control.id}
                onClick={() => setSelectedControl(control)}
                className="group flex items-center gap-4 p-4 rounded-lg bg-navy-900/40 hover:bg-navy-800/60 border border-navy-800 hover:border-navy-700 cursor-pointer transition-all"
                style={{ animationDelay: `${i * 30}ms` }}
              >
                <div className="flex-shrink-0 text-2xl">
                  {categoryIcons[control.category]}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-[15px] font-semibold text-white group-hover:text-cyan-400 transition-colors truncate">
                      {control.title}
                    </h3>
                    {control.isAutoPopulated && (
                      <span className="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 flex-shrink-0">
                        Auto
                      </span>
                    )}
                    {control.isPeopleControl && (
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex-shrink-0">
                        People
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-[13px]">
                    <span className="text-[#94b4d1] font-mono">{control.article}</span>
                    <span className="text-[#4a6580]">•</span>
                    <span className="text-[#94b4d1]">{control.category}</span>
                    {control.evidence.length > 0 && (
                      <>
                        <span className="text-navy-600">•</span>
                        <span className="text-cyan-400 flex items-center gap-1">
                          <FileText size={11} />
                          {control.evidence.length} evidence
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="hidden md:flex items-center gap-4 flex-shrink-0">
                  <div className="text-right">
                    <p className="text-xs text-[#94b4d1]">Owner</p>
                    <p className="text-[13px] text-white">{control.owner}</p>
                  </div>

                  <span className={`px-3 py-1.5 rounded-lg border text-xs font-semibold ${statusColors[control.status]}`}>
                    {control.status}
                  </span>

                  <ChevronRight size={16} className="text-[#4a6580] group-hover:text-cyan-400 transition-colors" />
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Control Drawer */}
      {selectedControl && (
        <ControlDrawer
          control={selectedControl}
          onClose={() => setSelectedControl(null)}
          onUpdate={(updates) => {
            updateControl(selectedControl.id, updates)
            setSelectedControl({ ...selectedControl, ...updates })
          }}
          onAddEvidence={(evidence) => {
            addEvidence(selectedControl.id, evidence)
          }}
          onRemoveEvidence={(evidenceId) => {
            removeEvidence(selectedControl.id, evidenceId)
          }}
          campaigns={getCampaignsForControl(selectedControl.id)}
        />
      )}
    </div>
  )
}
