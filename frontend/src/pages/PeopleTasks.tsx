import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users,
  CheckCircle,
  Clock,
  AlertTriangle,
  Mail,
  ChevronDown,
  ChevronRight,
  Calendar,
  TrendingUp,
  TrendingDown,
  Award,
  X
} from 'lucide-react'
import { useControls } from '../hooks/useControls'
import { Card, Button, StatCard, ProgressBar, InfoTooltip } from '../components/ui'
import { EmployeeCampaign, TaskStatus } from '../types/controls'
import { format } from 'date-fns'

const taskStatusColors: Record<TaskStatus, string> = {
  pending: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  completed: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  overdue: 'text-red-400 bg-red-500/10 border-red-500/20'
}

function CampaignCard({ campaign }: { campaign: EmployeeCampaign }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const navigate = useNavigate()

  const totalTasks = campaign.tasks.length
  const completedTasks = campaign.tasks.filter(t => t.status === 'completed').length
  const pendingTasks = campaign.tasks.filter(t => t.status === 'pending').length
  const overdueTasks = campaign.tasks.filter(t => t.status === 'overdue').length
  const completionRate = Math.round((completedTasks / totalTasks) * 100)

  const deadlineDate = new Date(campaign.deadline)
  const isDeadlinePassed = deadlineDate < new Date()
  const isAtRisk = isDeadlinePassed && completionRate < 80

  const averageScore = campaign.taskType === 'quiz'
    ? campaign.tasks
        .filter(t => t.score !== undefined)
        .reduce((sum, t) => sum + (t.score || 0), 0) / completedTasks || 0
    : null

  return (
    <Card className="hover:border-navy-700 transition-all">
      <div>
        {/* Campaign Header */}
        <div
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center justify-between cursor-pointer"
        >
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs px-2 py-0.5 rounded bg-navy-800 text-[#CBD8E8]">
                {campaign.taskType === 'quiz' ? 'Training Quiz' : 'Policy Acknowledgment'}
              </span>
              {isAtRisk && (
                <span className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 flex items-center gap-1">
                  <AlertTriangle size={11} />
                  At Risk
                </span>
              )}
              {completionRate === 100 && (
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                  <CheckCircle size={11} />
                  Complete
                </span>
              )}
            </div>

            <h3 className="text-[15px] font-semibold text-white mb-1">{campaign.controlName}</h3>

            <div className="flex items-center gap-4 text-[13px] text-[#94b4d1]">
              <span className="flex items-center gap-1">
                <Users size={12} />
                {totalTasks} employees
              </span>
              <span className="flex items-center gap-1">
                <Calendar size={12} />
                Due: {format(deadlineDate, 'MMM d, yyyy')}
              </span>
              <span className="flex items-center gap-1">
                <Clock size={12} />
                Created: {format(new Date(campaign.createdAt), 'MMM d')}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-3xl font-bold font-syne" style={{
                color: completionRate >= 80 ? '#10b981' : completionRate >= 50 ? '#f59e0b' : '#ef4444'
              }}>
                {completionRate}%
              </div>
              <div className="text-xs text-[#94b4d1]">completion</div>
            </div>

            {isExpanded ? (
              <ChevronDown size={20} className="text-cyan-400" />
            ) : (
              <ChevronRight size={20} className="text-[#4a6580]" />
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs mb-2">
            <div className="flex items-center gap-3">
              <span className="text-emerald-400">{completedTasks} completed</span>
              <span className="text-yellow-400">{pendingTasks} pending</span>
              {overdueTasks > 0 && (
                <span className="text-red-400">{overdueTasks} overdue</span>
              )}
            </div>
            {averageScore !== null && (
              <span className="flex items-center gap-1 text-[#CBD8E8]">
                <Award size={12} />
                Avg score: {averageScore.toFixed(1)}/5
              </span>
            )}
          </div>
          <ProgressBar
            value={completionRate}
            color={completionRate >= 80 ? 'bg-emerald-500' : 'bg-yellow-500'}
            height="h-2"
          />
        </div>

        {/* Expanded Employee List */}
        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-navy-700 space-y-2">
            {campaign.tasks.map(task => (
              <div
                key={task.id}
                className="flex items-center gap-4 p-3 rounded-lg bg-navy-900/40 border border-navy-800"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-[14px] font-medium text-white">{task.employeeName}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-lg border ${taskStatusColors[task.status]}`}>
                      {task.status === 'completed' ? 'Completed' : task.status === 'overdue' ? 'Overdue' : 'Pending'}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-[13px] text-[#94b4d1]">
                    <span>{task.employeeEmail}</span>
                    <span>•</span>
                    <span>{task.department}</span>
                  </div>
                </div>

                <div className="text-right text-[13px]">
                  {task.status === 'completed' ? (
                    <div>
                      <div className="text-emerald-400 font-semibold mb-0.5">
                        {format(new Date(task.completedDate!), 'MMM d, yyyy')}
                      </div>
                      {task.score !== undefined && (
                        <div className="text-[#94b4d1]">Score: {task.score}/5</div>
                      )}
                    </div>
                  ) : (
                    <div className={task.status === 'overdue' ? 'text-red-400' : 'text-yellow-400'}>
                      {task.status === 'overdue' ? 'Overdue' : 'Not completed'}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Campaign Actions */}
            <div className="flex items-center gap-2 pt-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={pendingTasks === 0 && overdueTasks === 0}
              >
                <Mail size={14} />
                Send Reminder ({pendingTasks + overdueTasks})
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/controls')}
              >
                View Control <ChevronRight size={14} />
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

export default function PeopleTasks() {
  const navigate = useNavigate()
  const { campaigns, employeeComplianceStats } = useControls()

  const activeCampaigns = campaigns.filter(c => {
    const completionRate = (c.tasks.filter(t => t.status === 'completed').length / c.tasks.length) * 100
    return completionRate < 100
  })

  const completedCampaigns = campaigns.filter(c => {
    const completionRate = (c.tasks.filter(t => t.status === 'completed').length / c.tasks.length) * 100
    return completionRate === 100
  })

  const atRiskCampaigns = campaigns.filter(c => {
    const completionRate = (c.tasks.filter(t => t.status === 'completed').length / c.tasks.length) * 100
    const isDeadlinePassed = new Date(c.deadline) < new Date()
    return isDeadlinePassed && completionRate < 80
  })

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[26px] font-bold font-syne text-white flex items-center gap-2">
            People Tasks
            <InfoTooltip content="Assign and track employee training campaigns and policy acknowledgments to meet NIS2 people-related requirements" />
          </h1>
          <p className="text-[14px] text-[#CBD8E8] mt-1">
            Track employee training and policy acknowledgment campaigns
          </p>
        </div>
        <Button onClick={() => navigate('/controls')}>
          <Users size={16} />
          Create Campaign
        </Button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Overall Completion"
          value={`${employeeComplianceStats.completionRate}%`}
          icon={employeeComplianceStats.completionRate >= 80 ? (
            <TrendingUp size={18} className="text-emerald-400" />
          ) : (
            <TrendingDown size={18} className="text-yellow-400" />
          )}
          accent={employeeComplianceStats.completionRate >= 80 ? 'text-emerald-400' : 'text-yellow-400'}
          trend={`${employeeComplianceStats.completedTasks}/${employeeComplianceStats.totalTasks} tasks`}
        />
        <StatCard
          label="Active Campaigns"
          value={activeCampaigns.length}
          icon={<Users size={18} className="text-cyan-400" />}
          accent="text-cyan-400"
        />
        <StatCard
          label="At Risk"
          value={atRiskCampaigns.length}
          icon={<AlertTriangle size={18} className="text-red-500" />}
          accent="text-red-500"
          trend="Past deadline, <80%"
        />
        <StatCard
          label="Completed"
          value={completedCampaigns.length}
          icon={<CheckCircle size={18} className="text-emerald-400" />}
          accent="text-emerald-400"
        />
      </div>

      {/* Alert for at-risk campaigns */}
      {atRiskCampaigns.length > 0 && (
        <Card className="bg-red-500/5 border-red-500/20">
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="text-red-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-[15px] font-semibold text-red-400 mb-1">
                {atRiskCampaigns.length} Campaign{atRiskCampaigns.length !== 1 ? 's' : ''} At Risk
              </h3>
              <p className="text-[14px] text-red-300 leading-relaxed mb-3">
                {atRiskCampaigns.length === 1
                  ? 'This campaign has passed its deadline with less than 80% completion. Consider sending reminders or extending the deadline.'
                  : `These campaigns have passed their deadlines with less than 80% completion. Consider sending reminders or extending deadlines.`}
              </p>
              <div className="flex flex-wrap gap-2">
                {atRiskCampaigns.map(c => {
                  const completionRate = Math.round(
                    (c.tasks.filter(t => t.status === 'completed').length / c.tasks.length) * 100
                  )
                  return (
                    <span key={c.id} className="text-xs px-2 py-1 rounded bg-navy-900/60 border border-red-500/20 text-red-300">
                      {c.controlName.slice(0, 40)}... ({completionRate}%)
                    </span>
                  )
                })}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* No campaigns message */}
      {campaigns.length === 0 && (
        <Card className="text-center py-12">
          <Users size={48} className="text-navy-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold font-syne text-white mb-2">
            No Employee Campaigns Yet
          </h3>
          <p className="text-[14px] text-[#CBD8E8] max-w-md mx-auto mb-6">
            Create your first campaign by going to the Controls Library, selecting a People control, and assigning tasks to employees.
          </p>
          <Button onClick={() => navigate('/controls')}>
            <Users size={16} />
            Go to Controls Library
          </Button>
        </Card>
      )}

      {/* Active Campaigns */}
      {activeCampaigns.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[18px] font-bold font-syne text-white">
              Active Campaigns ({activeCampaigns.length})
            </h2>
          </div>

          <div className="space-y-3">
            {activeCampaigns.map(campaign => (
              <CampaignCard key={campaign.id} campaign={campaign} />
            ))}
          </div>
        </div>
      )}

      {/* Completed Campaigns */}
      {completedCampaigns.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[18px] font-bold font-syne text-white flex items-center gap-2">
              <CheckCircle size={18} className="text-emerald-400" />
              Completed Campaigns ({completedCampaigns.length})
            </h2>
          </div>

          <div className="space-y-3">
            {completedCampaigns.map(campaign => (
              <CampaignCard key={campaign.id} campaign={campaign} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
