import { useState, useEffect, useCallback } from 'react'
import type { RemediationTask } from '../types/assessment'
import {
  getRemediationTasks,
  createRemediationTask,
  updateRemediationTask,
  getStoredAuth,
  isConnected,
} from '../services/api'

const STORAGE_KEY = 'konforme_remediation_tasks'

function generateId(): string {
  return `local-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

function loadLocalTasks(): RemediationTask[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

function saveLocalTasks(tasks: RemediationTask[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks))
}

export function useRemediation() {
  const [tasks, setTasks] = useState<RemediationTask[]>([])
  const [loading, setLoading] = useState(true)
  const connected = isConnected()

  const fetchTasks = useCallback(async () => {
    if (connected) {
      const { accountId } = getStoredAuth()
      if (accountId) {
        try {
          const data = await getRemediationTasks(accountId)
          setTasks(data)
          setLoading(false)
          return
        } catch (err) {
          console.error('Failed to fetch remediation tasks from backend:', err)
        }
      }
    }

    // Fallback to localStorage
    setTasks(loadLocalTasks())
    setLoading(false)
  }, [connected])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const addTask = useCallback(async (task: {
    question_id: string
    title: string
    description?: string
    priority?: string
    assigned_to?: string | null
    due_date?: string | null
  }) => {
    // Try backend first
    if (connected) {
      const { accountId } = getStoredAuth()
      if (accountId) {
        try {
          const created = await createRemediationTask(accountId, task)
          setTasks(prev => [created, ...prev])
          return created
        } catch (err) {
          console.error('Backend create failed, falling back to local:', err)
        }
      }
    }

    // Fallback: create locally
    const now = new Date().toISOString()
    const localTask: RemediationTask = {
      id: generateId(),
      questionId: task.question_id,
      title: task.title,
      description: task.description || '',
      status: 'open',
      priority: task.priority || 'medium',
      assignedTo: task.assigned_to || null,
      dueDate: task.due_date || null,
      createdAt: now,
      updatedAt: now,
      completedAt: null,
    }

    setTasks(prev => {
      const updated = [localTask, ...prev]
      saveLocalTasks(updated)
      return updated
    })
    return localTask
  }, [connected])

  const updateTask = useCallback(async (taskId: string, updates: {
    title?: string
    description?: string
    status?: string
    priority?: string
    assigned_to?: string | null
    due_date?: string | null
  }) => {
    // Try backend first
    if (connected) {
      const { accountId } = getStoredAuth()
      if (accountId) {
        try {
          const updated = await updateRemediationTask(accountId, taskId, updates)
          setTasks(prev => prev.map(t => t.id === taskId ? updated : t))
          return updated
        } catch (err) {
          console.error('Backend update failed, falling back to local:', err)
        }
      }
    }

    // Fallback: update locally
    setTasks(prev => {
      const updated = prev.map(t => {
        if (t.id !== taskId) return t
        return {
          ...t,
          ...(updates.title !== undefined && { title: updates.title }),
          ...(updates.description !== undefined && { description: updates.description }),
          ...(updates.status !== undefined && { status: updates.status as RemediationTask['status'] }),
          ...(updates.priority !== undefined && { priority: updates.priority }),
          ...(updates.assigned_to !== undefined && { assignedTo: updates.assigned_to }),
          ...(updates.due_date !== undefined && { dueDate: updates.due_date }),
          updatedAt: new Date().toISOString(),
          ...(updates.status === 'completed' && { completedAt: new Date().toISOString() }),
        }
      })
      saveLocalTasks(updated)
      return updated
    })
    return null
  }, [connected])

  return {
    tasks,
    loading,
    fetchTasks,
    addTask,
    updateTask,
  }
}
