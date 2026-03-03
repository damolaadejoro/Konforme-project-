import { useState, useEffect, useMemo } from 'react'
import {
  Control,
  ControlCategory,
  ControlStatus,
  EmployeeCampaign,
  EmployeeTask,
  ComplianceScore,
  ArticleArea,
  TaskType,
  TaskStatus
} from '../types/controls'
import { controls as templateControls, mockCampaigns } from '../data/controlsData'
import { mockScanResult } from '../data/mockData'

// Fresh controls for new users: all statuses reset to "Not Started", no pre-filled data
const freshControls: Control[] = templateControls.map(c => ({
  ...c,
  status: 'Not Started' as ControlStatus,
  owner: '',
  evidence: [],
  notes: '',
  lastUpdated: new Date().toISOString(),
}))

const STORAGE_KEY = 'konforme_controls'
const CAMPAIGNS_STORAGE_KEY = 'konforme_campaigns'
const LAST_SAVED_KEY = 'konforme_last_saved'

// Status weights for scoring
const STATUS_WEIGHTS = {
  'Not Started': 0,
  'Planned': 0.25,
  'Partial': 0.5,
  'Implemented': 1
}

// Severity weights
const SEVERITY_WEIGHTS = {
  critical: 3,
  high: 2,
  medium: 1
}

export function useControls() {
  const [controls, setControls] = useState<Control[]>([])
  const [campaigns, setCampaigns] = useState<EmployeeCampaign[]>([])
  const [selectedControl, setSelectedControl] = useState<Control | null>(null)
  const [lastSaved, setLastSaved] = useState<string | null>(null)

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    const storedCampaigns = localStorage.getItem(CAMPAIGNS_STORAGE_KEY)
    const storedLastSaved = localStorage.getItem(LAST_SAVED_KEY)

    if (stored) {
      try {
        setControls(JSON.parse(stored))
      } catch (e) {
        console.error('Failed to load controls', e)
        setControls(freshControls)
      }
    } else {
      setControls(freshControls)
    }

    if (storedCampaigns) {
      try {
        setCampaigns(JSON.parse(storedCampaigns))
      } catch (e) {
        console.error('Failed to load campaigns', e)
        setCampaigns([])
      }
    } else {
      setCampaigns([])
    }

    if (storedLastSaved) {
      setLastSaved(storedLastSaved)
    }
  }, [])

  // Save to localStorage whenever controls or campaigns change
  useEffect(() => {
    if (controls.length > 0) {
      const timestamp = new Date().toISOString()
      localStorage.setItem(STORAGE_KEY, JSON.stringify(controls))
      localStorage.setItem(LAST_SAVED_KEY, timestamp)
      setLastSaved(timestamp)
    }
  }, [controls])

  useEffect(() => {
    if (campaigns.length > 0) {
      const timestamp = new Date().toISOString()
      localStorage.setItem(CAMPAIGNS_STORAGE_KEY, JSON.stringify(campaigns))
      localStorage.setItem(LAST_SAVED_KEY, timestamp)
      setLastSaved(timestamp)
    }
  }, [campaigns])

  // Update control
  const updateControl = (controlId: string, updates: Partial<Control>) => {
    setControls(prev =>
      prev.map(control =>
        control.id === controlId
          ? { ...control, ...updates, lastUpdated: new Date().toISOString() }
          : control
      )
    )
  }

  // Add evidence to control
  const addEvidence = (controlId: string, evidence: Omit<Control['evidence'][0], 'id'>) => {
    const newEvidence = {
      ...evidence,
      id: `ev-${Date.now()}`
    }

    setControls(prev =>
      prev.map(control =>
        control.id === controlId
          ? {
              ...control,
              evidence: [...control.evidence, newEvidence],
              lastUpdated: new Date().toISOString()
            }
          : control
      )
    )
  }

  // Remove evidence
  const removeEvidence = (controlId: string, evidenceId: string) => {
    setControls(prev =>
      prev.map(control =>
        control.id === controlId
          ? {
              ...control,
              evidence: control.evidence.filter(e => e.id !== evidenceId),
              lastUpdated: new Date().toISOString()
            }
          : control
      )
    )
  }

  // Create employee campaign
  const createCampaign = (
    controlId: string,
    taskType: TaskType,
    employees: Array<{ name: string; email: string; department: string }>,
    deadline: string,
    policyContent?: string
  ) => {
    const control = controls.find(c => c.id === controlId)
    if (!control) return

    const tasks: EmployeeTask[] = employees.map(emp => ({
      id: `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      controlId,
      campaignId: '', // Will be set below
      employeeName: emp.name,
      employeeEmail: emp.email,
      department: emp.department,
      taskType,
      status: 'pending',
      sentDate: new Date().toISOString(),
      completedDate: null,
      deadline
    }))

    const campaign: EmployeeCampaign = {
      id: `camp-${Date.now()}`,
      controlId,
      controlName: control.title,
      taskType,
      deadline,
      createdAt: new Date().toISOString(),
      tasks: tasks.map(t => ({ ...t, campaignId: `camp-${Date.now()}` })),
      policyContent
    }

    setCampaigns(prev => [...prev, campaign])

    // Update control status if not already implemented
    if (control.status === 'Not Started') {
      updateControl(controlId, { status: 'Planned' })
    }
  }

  // Update task status
  const updateTaskStatus = (taskId: string, status: TaskStatus, score?: number) => {
    setCampaigns(prev =>
      prev.map(campaign => ({
        ...campaign,
        tasks: campaign.tasks.map(task =>
          task.id === taskId
            ? {
                ...task,
                status,
                completedDate: status === 'completed' ? new Date().toISOString() : task.completedDate,
                score
              }
            : task
        )
      }))
    )
  }

  // Calculate compliance score
  const complianceScore: ComplianceScore = useMemo(() => {
    let totalWeightedScore = 0
    let totalPossibleWeight = 0

    const categoryScores = {
      Technical: { score: 0, possible: 0 },
      Organizational: { score: 0, possible: 0 },
      People: { score: 0, possible: 0 }
    }

    const byArticle: Record<string, { score: number; possible: number }> = {}

    controls.forEach(control => {
      const statusWeight = STATUS_WEIGHTS[control.status]
      const severityWeight = SEVERITY_WEIGHTS[control.severity]
      const weightedScore = statusWeight * severityWeight
      const possibleWeight = severityWeight

      totalWeightedScore += weightedScore
      totalPossibleWeight += possibleWeight

      // Category scores
      categoryScores[control.category].score += weightedScore
      categoryScores[control.category].possible += possibleWeight

      // Article scores
      const article = control.article
      if (!byArticle[article]) {
        byArticle[article] = { score: 0, possible: 0 }
      }
      byArticle[article].score += weightedScore
      byArticle[article].possible += possibleWeight
    })

    const overall = totalPossibleWeight > 0
      ? Math.round((totalWeightedScore / totalPossibleWeight) * 100)
      : 0

    const technical = categoryScores.Technical.possible > 0
      ? Math.round((categoryScores.Technical.score / categoryScores.Technical.possible) * 100)
      : 0

    const organizational = categoryScores.Organizational.possible > 0
      ? Math.round((categoryScores.Organizational.score / categoryScores.Organizational.possible) * 100)
      : 0

    const people = categoryScores.People.possible > 0
      ? Math.round((categoryScores.People.score / categoryScores.People.possible) * 100)
      : 0

    const articleScores: Record<string, number> = {}
    Object.keys(byArticle).forEach(article => {
      const { score, possible } = byArticle[article]
      articleScores[article] = possible > 0 ? Math.round((score / possible) * 100) : 0
    })

    return {
      overall,
      technical,
      organizational,
      people,
      byArticle: articleScores
    }
  }, [controls])

  // Get article areas with status
  const articleAreas: ArticleArea[] = useMemo(() => {
    const areas: Record<string, ArticleArea> = {}

    controls.forEach(control => {
      const areaName = control.articleArea
      if (!areas[areaName]) {
        areas[areaName] = {
          id: areaName.toLowerCase().replace(/\s+/g, '-'),
          name: areaName,
          article: control.article.split('(')[0].trim(), // Extract just "Art. 21"
          controlCount: 0,
          implementedCount: 0,
          status: 'Not Started' as ControlStatus
        }
      }

      areas[areaName].controlCount++
      if (control.status === 'Implemented') {
        areas[areaName].implementedCount++
      }
    })

    // Determine status for each area
    Object.values(areas).forEach(area => {
      const implementedRatio = area.implementedCount / area.controlCount
      if (implementedRatio === 1) {
        area.status = 'Implemented'
      } else if (implementedRatio >= 0.5) {
        area.status = 'Partial'
      } else if (implementedRatio > 0) {
        area.status = 'Planned'
      } else {
        area.status = 'Not Started'
      }
    })

    return Object.values(areas)
  }, [controls])

  // Get critical gaps
  const criticalGaps = useMemo(() => {
    return controls
      .filter(c =>
        (c.status === 'Not Started' || c.status === 'Partial') &&
        (c.severity === 'critical' || c.severity === 'high')
      )
      .sort((a, b) => {
        // Sort by severity first
        const severityOrder = { critical: 0, high: 1, medium: 2 }
        const severityDiff = severityOrder[a.severity] - severityOrder[b.severity]
        if (severityDiff !== 0) return severityDiff

        // Then by status (Not Started before Partial)
        const statusOrder = { 'Not Started': 0, 'Planned': 1, 'Partial': 2, 'Implemented': 3 }
        return statusOrder[a.status] - statusOrder[b.status]
      })
      .slice(0, 5)
  }, [controls])

  // Filter controls
  const filterControls = (
    category?: ControlCategory,
    status?: ControlStatus,
    articleArea?: string,
    searchQuery?: string
  ) => {
    return controls.filter(control => {
      if (category && control.category !== category) return false
      if (status && control.status !== status) return false
      if (articleArea && control.articleArea !== articleArea) return false
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        return (
          control.title.toLowerCase().includes(query) ||
          control.description.toLowerCase().includes(query) ||
          control.article.toLowerCase().includes(query)
        )
      }
      return true
    })
  }

  // Get campaign for control
  const getCampaignsForControl = (controlId: string) => {
    return campaigns.filter(c => c.controlId === controlId)
  }

  // Get all tasks across all campaigns
  const allTasks = useMemo(() => {
    return campaigns.flatMap(c => c.tasks)
  }, [campaigns])

  // Employee compliance stats
  const employeeComplianceStats = useMemo(() => {
    const totalTasks = allTasks.length
    const completedTasks = allTasks.filter(t => t.status === 'completed').length
    const pendingTasks = allTasks.filter(t => t.status === 'pending').length
    const overdueTasks = allTasks.filter(t => t.status === 'overdue').length
    const completionRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

    return {
      totalTasks,
      completedTasks,
      pendingTasks,
      overdueTasks,
      completionRate
    }
  }, [allTasks])

  return {
    controls,
    campaigns,
    selectedControl,
    setSelectedControl,
    updateControl,
    addEvidence,
    removeEvidence,
    createCampaign,
    updateTaskStatus,
    complianceScore,
    articleAreas,
    criticalGaps,
    filterControls,
    getCampaignsForControl,
    allTasks,
    employeeComplianceStats,
    lastSaved
  }
}
