import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useControls } from '../hooks/useControls'

describe('Employee Campaigns', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.getItem.mockReturnValue(null)
  })

  describe('Campaign Creation', () => {
    it('A new campaign can be created with valid data', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [{ name: 'John Doe', email: 'john@example.com', department: 'IT' }],
          '2024-12-31',
          'Test policy content'
        )
      })

      expect(result.current.campaigns.length).toBeGreaterThan(0)
    })

    it('Campaign requires a name, type, and deadline', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'quiz',
          [{ name: 'Jane Smith', email: 'jane@example.com', department: 'HR' }],
          '2024-12-31'
        )
      })

      const campaign = result.current.campaigns[0]
      expect(campaign.controlName).toBeTruthy()
      expect(campaign.taskType).toBeTruthy()
      expect(campaign.deadline).toBeTruthy()
    })

    it('Campaign is added to the campaigns list after creation', () => {
      const { result } = renderHook(() => useControls())
      const initialCampaignCount = result.current.campaigns.length
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [{ name: 'John Doe', email: 'john@example.com', department: 'IT' }],
          '2024-12-31'
        )
      })

      expect(result.current.campaigns.length).toBe(initialCampaignCount + 1)
    })

    it('Campaign is associated with the correct control', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [{ name: 'John Doe', email: 'john@example.com', department: 'IT' }],
          '2024-12-31'
        )
      })

      const campaign = result.current.campaigns[0]
      expect(campaign.controlId).toBe(controlId)
    })

    it('Employees are added to the campaign correctly', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id
      const employees = [
        { name: 'John Doe', email: 'john@example.com', department: 'IT' },
        { name: 'Jane Smith', email: 'jane@example.com', department: 'HR' }
      ]

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          employees,
          '2024-12-31'
        )
      })

      const campaign = result.current.campaigns[0]
      expect(campaign.tasks.length).toBe(2)
      expect(campaign.tasks[0].employeeName).toBe('John Doe')
      expect(campaign.tasks[1].employeeName).toBe('Jane Smith')
    })

    it('Each employee gets a unique task ID', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id
      const employees = [
        { name: 'John Doe', email: 'john@example.com', department: 'IT' },
        { name: 'Jane Smith', email: 'jane@example.com', department: 'HR' },
        { name: 'Bob Johnson', email: 'bob@example.com', department: 'Finance' }
      ]

      act(() => {
        result.current.createCampaign(
          controlId,
          'quiz',
          employees,
          '2024-12-31'
        )
      })

      const campaign = result.current.campaigns[0]
      const taskIds = campaign.tasks.map(t => t.id)
      const uniqueIds = new Set(taskIds)
      expect(uniqueIds.size).toBe(3)
    })
  })

  describe('Campaign Tracking', () => {
    it('Completion percentage is 0% when no employees have completed', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [
            { name: 'John Doe', email: 'john@example.com', department: 'IT' },
            { name: 'Jane Smith', email: 'jane@example.com', department: 'HR' }
          ],
          '2024-12-31'
        )
      })

      const stats = result.current.employeeComplianceStats
      const completedTasks = result.current.allTasks.filter(t => t.status === 'completed').length
      expect(completedTasks).toBe(0)
    })

    it('Completion percentage is 100% when all employees completed', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [
            { name: 'John Doe', email: 'john@example.com', department: 'IT' },
            { name: 'Jane Smith', email: 'jane@example.com', department: 'HR' }
          ],
          '2024-12-31'
        )
      })

      const campaign = result.current.campaigns[0]

      act(() => {
        campaign.tasks.forEach(task => {
          result.current.updateTaskStatus(task.id, 'completed')
        })
      })

      const stats = result.current.employeeComplianceStats
      expect(stats.completionRate).toBe(100)
    })

    it('Completion percentage calculates correctly for partial completion', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'quiz',
          [
            { name: 'John Doe', email: 'john@example.com', department: 'IT' },
            { name: 'Jane Smith', email: 'jane@example.com', department: 'HR' }
          ],
          '2024-12-31'
        )
      })

      const campaign = result.current.campaigns[0]

      act(() => {
        result.current.updateTaskStatus(campaign.tasks[0].id, 'completed')
      })

      const stats = result.current.employeeComplianceStats
      expect(stats.completionRate).toBe(50)
    })

    it('A campaign with 3 of 5 completed shows 60%', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [
            { name: 'Employee 1', email: 'emp1@example.com', department: 'IT' },
            { name: 'Employee 2', email: 'emp2@example.com', department: 'HR' },
            { name: 'Employee 3', email: 'emp3@example.com', department: 'Finance' },
            { name: 'Employee 4', email: 'emp4@example.com', department: 'Sales' },
            { name: 'Employee 5', email: 'emp5@example.com', department: 'Marketing' }
          ],
          '2024-12-31'
        )
      })

      const campaign = result.current.campaigns[0]

      act(() => {
        result.current.updateTaskStatus(campaign.tasks[0].id, 'completed')
        result.current.updateTaskStatus(campaign.tasks[1].id, 'completed')
        result.current.updateTaskStatus(campaign.tasks[2].id, 'completed')
      })

      const stats = result.current.employeeComplianceStats
      expect(stats.completionRate).toBe(60)
    })

    it('Completed status is set when employee submits their task', async () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [{ name: 'John Doe', email: 'john@example.com', department: 'IT' }],
          '2024-12-31'
        )
      })

      const taskId = result.current.campaigns[0].tasks[0].id

      act(() => {
        result.current.updateTaskStatus(taskId, 'completed')
      })

      await waitFor(() => {
        const task = result.current.campaigns[0].tasks[0]
        expect(task.status).toBe('completed')
      })
    })
  })

  describe('Employee Tasks', () => {
    it('Employee task status starts as Pending', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [{ name: 'John Doe', email: 'john@example.com', department: 'IT' }],
          '2024-12-31'
        )
      })

      const task = result.current.campaigns[0].tasks[0]
      expect(task.status).toBe('pending')
    })

    it('Employee task status changes to Completed on submission', async () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [{ name: 'John Doe', email: 'john@example.com', department: 'IT' }],
          '2024-12-31'
        )
      })

      const taskId = result.current.campaigns[0].tasks[0].id

      act(() => {
        result.current.updateTaskStatus(taskId, 'completed')
      })

      await waitFor(() => {
        const task = result.current.campaigns[0].tasks[0]
        expect(task.status).toBe('completed')
      })
    })

    it('Quiz score is recorded correctly on completion', async () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'quiz',
          [{ name: 'John Doe', email: 'john@example.com', department: 'IT' }],
          '2024-12-31'
        )
      })

      const taskId = result.current.campaigns[0].tasks[0].id

      act(() => {
        result.current.updateTaskStatus(taskId, 'completed', 85)
      })

      await waitFor(() => {
        const task = result.current.campaigns[0].tasks[0]
        expect(task.score).toBe(85)
      })
    })

    it('Policy acknowledgment records employee name and date', async () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [{ name: 'John Doe', email: 'john@example.com', department: 'IT' }],
          '2024-12-31'
        )
      })

      const task = result.current.campaigns[0].tasks[0]
      expect(task.employeeName).toBe('John Doe')
      expect(task.sentDate).toBeTruthy()

      const taskId = task.id

      act(() => {
        result.current.updateTaskStatus(taskId, 'completed')
      })

      await waitFor(() => {
        const completedTask = result.current.campaigns[0].tasks[0]
        expect(completedTask.completedDate).toBeTruthy()
      })
    })

    it('Completing all tasks in a campaign marks campaign as completed', async () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.createCampaign(
          controlId,
          'quiz',
          [
            { name: 'John Doe', email: 'john@example.com', department: 'IT' },
            { name: 'Jane Smith', email: 'jane@example.com', department: 'HR' }
          ],
          '2024-12-31'
        )
      })

      const campaign = result.current.campaigns[0]

      act(() => {
        campaign.tasks.forEach(task => {
          result.current.updateTaskStatus(task.id, 'completed', 100)
        })
      })

      await waitFor(() => {
        const allCompleted = result.current.campaigns[0].tasks.every(t => t.status === 'completed')
        expect(allCompleted).toBe(true)
      })
    })
  })
})
