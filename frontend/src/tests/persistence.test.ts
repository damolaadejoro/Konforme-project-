import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useControls } from '../hooks/useControls'
import { Control } from '../types/controls'

describe('LocalStorage Persistence', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.getItem.mockReturnValue(null)
    localStorage.setItem.mockClear()
  })

  describe('Initial Load', () => {
    it('On first visit mock data loads when localStorage is empty', () => {
      localStorage.getItem.mockReturnValue(null)

      const { result } = renderHook(() => useControls())

      // Should load initial controls
      expect(result.current.controls.length).toBeGreaterThan(0)
    })

    it('On return visit data loads from localStorage not mock data', () => {
      const savedControls: Control[] = [
        {
          id: 'saved-1',
          title: 'Saved Control',
          description: 'This was saved',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'Saved Owner',
          dueDate: '2024-12-31',
          evidence: [],
          notes: 'Saved notes',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(savedControls)
        if (key === 'konforme_campaigns') return '[]'
        if (key === 'konforme_last_saved') return new Date().toISOString()
        return null
      })

      const { result } = renderHook(() => useControls())

      expect(result.current.controls.length).toBe(1)
      expect(result.current.controls[0].id).toBe('saved-1')
      expect(result.current.controls[0].title).toBe('Saved Control')
      expect(result.current.controls[0].owner).toBe('Saved Owner')
    })

    it('Corrupted JSON in localStorage falls back to mock data gracefully', () => {
      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return 'invalid JSON {'
        return null
      })

      const { result } = renderHook(() => useControls())

      // Should load initial controls despite corrupted data
      expect(result.current.controls.length).toBeGreaterThan(0)
    })

    it('Missing localStorage key falls back to mock data gracefully', () => {
      localStorage.getItem.mockReturnValue(null)

      const { result } = renderHook(() => useControls())

      expect(result.current.controls.length).toBeGreaterThan(0)
    })

    it('Partial localStorage data falls back to mock data gracefully', () => {
      // Only controls saved, no campaigns
      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())

      // Should handle empty array gracefully and load initial data
      expect(Array.isArray(result.current.controls)).toBe(true)
      expect(Array.isArray(result.current.campaigns)).toBe(true)
    })
  })

  describe('Saving Data', () => {
    it('Changing a control status saves to localStorage immediately', async () => {
      localStorage.getItem.mockReturnValue(null)

      const { result } = renderHook(() => useControls())

      const controlId = result.current.controls[0].id

      act(() => {
        result.current.updateControl(controlId, { status: 'Implemented' })
      })

      // Wait for state update
      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith(
          'konforme_controls',
          expect.any(String)
        )
      })
    })

    it('Changing control owner saves to localStorage immediately', async () => {
      localStorage.getItem.mockReturnValue(null)

      const { result } = renderHook(() => useControls())

      const controlId = result.current.controls[0].id

      act(() => {
        result.current.updateControl(controlId, { owner: 'New Owner' })
      })

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith(
          'konforme_controls',
          expect.any(String)
        )
      })
    })

    it('Changing control due date saves to localStorage immediately', async () => {
      localStorage.getItem.mockReturnValue(null)

      const { result } = renderHook(() => useControls())

      const controlId = result.current.controls[0].id

      act(() => {
        result.current.updateControl(controlId, { dueDate: '2024-12-31' })
      })

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith(
          'konforme_controls',
          expect.any(String)
        )
      })
    })

    it('Changing control notes saves to localStorage immediately', async () => {
      localStorage.getItem.mockReturnValue(null)

      const { result } = renderHook(() => useControls())

      const controlId = result.current.controls[0].id

      act(() => {
        result.current.updateControl(controlId, { notes: 'Updated notes' })
      })

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith(
          'konforme_controls',
          expect.any(String)
        )
      })
    })

    it('Adding evidence to a control saves to localStorage immediately', async () => {
      localStorage.getItem.mockReturnValue(null)

      const { result } = renderHook(() => useControls())

      const controlId = result.current.controls[0].id

      act(() => {
        result.current.addEvidence(controlId, {
          filename: 'test.pdf',
          uploadedAt: new Date().toISOString(),
          uploadedBy: 'Test User'
        })
      })

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith(
          'konforme_controls',
          expect.any(String)
        )
      })
    })

    it('Removing evidence from a control saves to localStorage immediately', async () => {
      localStorage.getItem.mockReturnValue(null)

      const { result } = renderHook(() => useControls())

      const controlId = result.current.controls[0].id

      // First add evidence
      act(() => {
        result.current.addEvidence(controlId, {
          filename: 'test.pdf',
          uploadedAt: new Date().toISOString(),
          uploadedBy: 'Test User'
        })
      })

      await waitFor(() => {
        expect(result.current.controls[0].evidence.length).toBeGreaterThan(0)
      })

      const evidenceId = result.current.controls[0].evidence[0].id

      // Then remove it
      act(() => {
        result.current.removeEvidence(controlId, evidenceId)
      })

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalled()
      })
    })

    it('Creating a new campaign saves to localStorage immediately', async () => {
      localStorage.getItem.mockReturnValue(null)

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
          '2024-12-31',
          'Test policy content'
        )
      })

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith(
          'konforme_campaigns',
          expect.any(String)
        )
      })
    })

    it('Updating employee task status saves to localStorage immediately', async () => {
      localStorage.getItem.mockReturnValue(null)

      const { result } = renderHook(() => useControls())

      const controlId = result.current.controls[0].id

      // First create a campaign
      act(() => {
        result.current.createCampaign(
          controlId,
          'acknowledge',
          [{ name: 'John Doe', email: 'john@example.com', department: 'IT' }],
          '2024-12-31'
        )
      })

      await waitFor(() => {
        expect(result.current.campaigns.length).toBeGreaterThan(0)
      })

      const taskId = result.current.campaigns[0].tasks[0].id

      // Then update task status
      act(() => {
        result.current.updateTaskStatus(taskId, 'completed')
      })

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalled()
      })
    })
  })

  describe('Data Integrity', () => {
    it('All 28 controls are present after loading from localStorage', () => {
      // First load to get initial controls
      localStorage.getItem.mockReturnValue(null)
      const { result: initialResult } = renderHook(() => useControls())

      // Save the controls
      const controls = initialResult.current.controls

      // Now create a new hook instance with saved data
      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(controls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())

      expect(result.current.controls.length).toBe(controls.length)
    })

    it('Control NIS2 article references are preserved correctly', () => {
      localStorage.getItem.mockReturnValue(null)
      const { result: initialResult } = renderHook(() => useControls())

      const originalArticles = initialResult.current.controls.map(c => c.article)
      const controls = initialResult.current.controls

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(controls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())

      const loadedArticles = result.current.controls.map(c => c.article)
      expect(loadedArticles).toEqual(originalArticles)
    })

    it('Control categories are preserved correctly', () => {
      localStorage.getItem.mockReturnValue(null)
      const { result: initialResult } = renderHook(() => useControls())

      const originalCategories = initialResult.current.controls.map(c => c.category)
      const controls = initialResult.current.controls

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(controls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())

      const loadedCategories = result.current.controls.map(c => c.category)
      expect(loadedCategories).toEqual(originalCategories)
    })

    it('Control severity weights are preserved correctly', () => {
      localStorage.getItem.mockReturnValue(null)
      const { result: initialResult } = renderHook(() => useControls())

      const originalSeverities = initialResult.current.controls.map(c => c.severity)
      const controls = initialResult.current.controls

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(controls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())

      const loadedSeverities = result.current.controls.map(c => c.severity)
      expect(loadedSeverities).toEqual(originalSeverities)
    })

    it('Campaign employee lists are preserved correctly', () => {
      localStorage.getItem.mockReturnValue(null)
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

      // Get the saved campaigns
      const savedCampaigns = result.current.campaigns

      // Reload with saved data
      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(result.current.controls)
        if (key === 'konforme_campaigns') return JSON.stringify(savedCampaigns)
        return null
      })

      const { result: reloadedResult } = renderHook(() => useControls())

      expect(reloadedResult.current.campaigns[0].tasks.length).toBe(2)
      expect(reloadedResult.current.campaigns[0].tasks[0].employeeName).toBe('John Doe')
      expect(reloadedResult.current.campaigns[0].tasks[1].employeeName).toBe('Jane Smith')
    })

    it('Employee completion statuses are preserved correctly', async () => {
      localStorage.getItem.mockReturnValue(null)
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

      await waitFor(() => {
        expect(result.current.campaigns.length).toBeGreaterThan(0)
      })

      const taskId = result.current.campaigns[0].tasks[0].id

      act(() => {
        result.current.updateTaskStatus(taskId, 'completed', 85)
      })

      // Get saved data
      const savedCampaigns = result.current.campaigns

      // Reload
      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(result.current.controls)
        if (key === 'konforme_campaigns') return JSON.stringify(savedCampaigns)
        return null
      })

      const { result: reloadedResult } = renderHook(() => useControls())

      expect(reloadedResult.current.campaigns[0].tasks[0].status).toBe('completed')
      expect(reloadedResult.current.campaigns[0].tasks[0].score).toBe(85)
    })
  })
})
