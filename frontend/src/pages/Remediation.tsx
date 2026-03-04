import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ListTodo,
  Plus,
  Filter,
  CheckCircle,
  Clock,
  AlertTriangle,
  ChevronRight,
  ArrowLeft,
  X,
} from 'lucide-react'
import { Card, Button, InfoTooltip, Tooltip } from '../components/ui'
import { useRemediation } from '../hooks/useRemediation'
import { QUESTION_MAP, ASSESSMENT_QUESTIONS, ARTICLES } from '../data/assessmentQuestions'
import { isConnected } from '../services/api'

type StatusFilter = 'all' | 'open' | 'in_progress' | 'completed' | 'dismissed'

const STATUS_TOOLTIPS: Record<string, string> = {
  open: 'Tasks created but not yet started',
  in_progress: 'Tasks actively being worked on',
  completed: 'Tasks that have been resolved',
  dismissed: 'Tasks acknowledged but deprioritized',
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bgColor: string; icon: React.ReactNode }> = {
  open: { label: 'Open', color: 'text-red-400', bgColor: 'bg-red-500/10 border-red-500/20', icon: <AlertTriangle size={14} /> },
  in_progress: { label: 'In Progress', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10 border-yellow-500/20', icon: <Clock size={14} /> },
  completed: { label: 'Completed', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10 border-emerald-500/20', icon: <CheckCircle size={14} /> },
  dismissed: { label: 'Dismissed', color: 'text-navy-400', bgColor: 'bg-navy-700/50 border-navy-600', icon: <X size={14} /> },
}

export default function Remediation() {
  const navigate = useNavigate()
  const { tasks, loading, addTask, updateTask } = useRemediation()
  const [filter, setFilter] = useState<StatusFilter>('all')
  const [showCreate, setShowCreate] = useState(false)
  const [newTask, setNewTask] = useState({ question_id: '', title: '', description: '', priority: 'medium' })

  const filteredTasks = filter === 'all' ? tasks : tasks.filter(t => t.status === filter)
  const connected = isConnected()

  const statusCounts = {
    all: tasks.length,
    open: tasks.filter(t => t.status === 'open').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    dismissed: tasks.filter(t => t.status === 'dismissed').length,
  }

  const handleCreateTask = async () => {
    if (!newTask.question_id || !newTask.title) return
    await addTask(newTask)
    setNewTask({ question_id: '', title: '', description: '', priority: 'medium' })
    setShowCreate(false)
  }

  if (!connected) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-[26px] font-bold font-syne text-white">Remediation Tasks</h1>
          <p className="text-[14px] text-[#CBD8E8] mt-1">Track and manage compliance gap remediation</p>
        </div>
        <Card>
          <div className="text-center py-16">
            <ListTodo size={48} className="text-navy-500 mx-auto mb-4" />
            <h3 className="text-lg font-bold font-syne text-white mb-2">Connect to Get Started</h3>
            <p className="text-[14px] text-[#CBD8E8] max-w-md mx-auto mb-6">
              Connect your account in Settings to create and track remediation tasks.
            </p>
            <Button onClick={() => navigate('/settings')}>Go to Settings <ChevronRight size={14} /></Button>
          </div>
        </Card>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[26px] font-bold font-syne text-white flex items-center gap-2">
            Remediation Tasks
            <InfoTooltip content="Track and manage tasks to close gaps identified in your assessment" />
          </h1>
          <p className="text-[14px] text-[#CBD8E8] mt-1">
            Track and manage compliance gap remediation
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => navigate('/assessment')}>
            <ArrowLeft size={14} /> Assessment
          </Button>
          <Button onClick={() => setShowCreate(true)}>
            <Plus size={14} /> Create Task
          </Button>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        {(['all', 'open', 'in_progress', 'completed', 'dismissed'] as StatusFilter[]).map(s => {
          const btn = (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`p-3 rounded-lg border text-left transition-all ${
                filter === s
                  ? 'bg-cyan-500/10 border-cyan-500/30'
                  : 'bg-navy-900/40 border-navy-800 hover:border-navy-600'
              }`}
            >
              <div className="text-xs text-[#94b4d1] uppercase mb-1">
                {s === 'all' ? 'All' : s === 'in_progress' ? 'In Progress' : s.charAt(0).toUpperCase() + s.slice(1)}
              </div>
              <div className={`text-xl font-bold font-syne ${filter === s ? 'text-cyan-400' : 'text-white'}`}>
                {statusCounts[s]}
              </div>
            </button>
          )
          return STATUS_TOOLTIPS[s] ? (
            <Tooltip key={s} content={STATUS_TOOLTIPS[s]}>
              {btn}
            </Tooltip>
          ) : (
            <React.Fragment key={s}>{btn}</React.Fragment>
          )
        })}
      </div>

      {/* Create task form */}
      {showCreate && (
        <Card>
          <h3 className="text-[16px] font-bold font-syne text-white mb-4">Create Remediation Task</h3>
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-navy-200 uppercase tracking-wider block mb-1.5">
                Related Question
              </label>
              <select
                value={newTask.question_id}
                onChange={(e) => {
                  const qid = e.target.value
                  const q = QUESTION_MAP[qid]
                  setNewTask(prev => ({
                    ...prev,
                    question_id: qid,
                    title: q ? `Remediate: ${q.question}` : prev.title,
                  }))
                }}
                className="w-full bg-navy-900 border border-navy-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="">Select a question...</option>
                {ARTICLES.map(art => (
                  <optgroup key={art.id} label={`${art.article} — ${art.title}`}>
                    {ASSESSMENT_QUESTIONS.filter(q => q.article === art.article).map(q => (
                      <option key={q.id} value={q.id}>
                        [{q.severity}] {q.question}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-navy-200 uppercase tracking-wider block mb-1.5">
                Title
              </label>
              <input
                value={newTask.title}
                onChange={(e) => setNewTask(prev => ({ ...prev, title: e.target.value }))}
                className="w-full bg-navy-900 border border-navy-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                placeholder="Task title..."
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-navy-200 uppercase tracking-wider block mb-1.5">
                Description
              </label>
              <textarea
                value={newTask.description}
                onChange={(e) => setNewTask(prev => ({ ...prev, description: e.target.value }))}
                className="w-full bg-navy-900 border border-navy-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 resize-none"
                rows={3}
                placeholder="Describe what needs to be done..."
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-navy-200 uppercase tracking-wider block mb-1.5">
                Priority
              </label>
              <select
                value={newTask.priority}
                onChange={(e) => setNewTask(prev => ({ ...prev, priority: e.target.value }))}
                className="w-full bg-navy-900 border border-navy-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button onClick={handleCreateTask} disabled={!newTask.question_id || !newTask.title}>
                Create Task
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Task list */}
      {filteredTasks.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <ListTodo size={48} className="text-navy-500 mx-auto mb-4" />
            <h3 className="text-lg font-bold font-syne text-white mb-2">
              {tasks.length === 0 ? 'No Tasks Yet' : 'No Matching Tasks'}
            </h3>
            <p className="text-[14px] text-[#CBD8E8] max-w-md mx-auto">
              {tasks.length === 0
                ? 'Create remediation tasks from your assessment gaps to track progress.'
                : 'Try changing the filter to see other tasks.'}
            </p>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="space-y-3">
            {filteredTasks.map(task => {
              const config = STATUS_CONFIG[task.status]
              const q = QUESTION_MAP[task.questionId]
              const priorityColors: Record<string, string> = {
                critical: 'text-red-400',
                high: 'text-orange-400',
                medium: 'text-yellow-400',
                low: 'text-blue-400',
              }

              return (
                <div
                  key={task.id}
                  className={`p-4 rounded-lg border transition-all ${config.bgColor}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className={`flex items-center gap-1 text-xs font-semibold ${config.color}`}>
                          {config.icon} {config.label}
                        </span>
                        <span className={`text-xs font-semibold ${priorityColors[task.priority] || 'text-navy-400'}`}>
                          {task.priority}
                        </span>
                        {q && <span className="text-xs text-navy-400 font-mono">{q.article}</span>}
                      </div>
                      <h4 className="text-[15px] font-semibold text-white mb-1">{task.title}</h4>
                      {task.description && (
                        <p className="text-[13px] text-[#94b4d1] line-clamp-2">{task.description}</p>
                      )}
                      <div className="flex items-center gap-3 mt-2 text-[12px] text-[#94b4d1]">
                        <span>Created: {new Date(task.createdAt).toLocaleDateString('en-GB')}</span>
                        {task.assignedTo && <span>Assigned: {task.assignedTo}</span>}
                        {task.dueDate && <span>Due: {new Date(task.dueDate).toLocaleDateString('en-GB')}</span>}
                      </div>
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      {task.status === 'open' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => updateTask(task.id, { status: 'in_progress' })}
                        >
                          Start
                        </Button>
                      )}
                      {task.status === 'in_progress' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => updateTask(task.id, { status: 'completed' })}
                        >
                          Complete
                        </Button>
                      )}
                      {(task.status === 'open' || task.status === 'in_progress') && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-navy-400"
                          onClick={() => updateTask(task.id, { status: 'dismissed' })}
                        >
                          Dismiss
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      )}
    </div>
  )
}
