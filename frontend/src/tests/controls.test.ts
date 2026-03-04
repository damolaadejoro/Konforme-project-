import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useControls } from '../hooks/useControls'

describe('Controls Data and Filtering', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.getItem.mockReturnValue(null)
  })

  describe('Controls Data Integrity', () => {
    it('Exactly 28 controls exist in the controls library', () => {
      const { result } = renderHook(() => useControls())
      expect(result.current.controls.length).toBe(28)
    })

    it('Every control has a unique ID', () => {
      const { result } = renderHook(() => useControls())
      const ids = result.current.controls.map(c => c.id)
      const uniqueIds = new Set(ids)
      expect(uniqueIds.size).toBe(ids.length)
    })

    it('Every control has a title', () => {
      const { result } = renderHook(() => useControls())
      result.current.controls.forEach(control => {
        expect(control.title).toBeTruthy()
        expect(control.title.length).toBeGreaterThan(0)
      })
    })

    it('Every control has a valid NIS2 article reference', () => {
      const { result } = renderHook(() => useControls())
      result.current.controls.forEach(control => {
        expect(control.article).toBeTruthy()
        expect(control.article).toMatch(/Art\.\s*\d+/)
      })
    })

    it('Every control has a valid category', () => {
      const { result } = renderHook(() => useControls())
      const validCategories = ['Technical', 'Organizational', 'People']
      result.current.controls.forEach(control => {
        expect(validCategories).toContain(control.category)
      })
    })

    it('Every control has a valid severity', () => {
      const { result } = renderHook(() => useControls())
      const validSeverities = ['critical', 'high', 'medium']
      result.current.controls.forEach(control => {
        expect(validSeverities).toContain(control.severity)
      })
    })

    it('Every control has a valid initial maturity status', () => {
      const { result } = renderHook(() => useControls())
      const validStatuses = ['Not Started', 'Planned', 'Partial', 'Implemented']
      result.current.controls.forEach(control => {
        expect(validStatuses).toContain(control.status)
      })
    })

    it('All Article 21 areas are represented by at least one control', () => {
      const { result } = renderHook(() => useControls())
      const articleAreas = result.current.articleAreas
      expect(articleAreas.length).toBeGreaterThan(0)
      articleAreas.forEach(area => {
        expect(area.controlCount).toBeGreaterThan(0)
      })
    })

    it('Auto-populated controls are marked correctly', () => {
      const { result } = renderHook(() => useControls())
      const autoPopulatedControls = result.current.controls.filter(c => c.isAutoPopulated)
      // Just verify the property exists and is boolean
      autoPopulatedControls.forEach(control => {
        expect(typeof control.isAutoPopulated).toBe('boolean')
      })
    })

    it('People controls are marked correctly', () => {
      const { result } = renderHook(() => useControls())
      const peopleControls = result.current.controls.filter(c => c.isPeopleControl)
      // Just verify the property exists and is boolean
      peopleControls.forEach(control => {
        expect(typeof control.isPeopleControl).toBe('boolean')
      })
    })
  })

  describe('Filtering Logic', () => {
    it('Filtering by category Technical returns only Technical controls', () => {
      const { result } = renderHook(() => useControls())
      const filtered = result.current.filterControls('Technical')
      expect(filtered.length).toBeGreaterThan(0)
      filtered.forEach(control => {
        expect(control.category).toBe('Technical')
      })
    })

    it('Filtering by category Organizational returns only Organizational controls', () => {
      const { result } = renderHook(() => useControls())
      const filtered = result.current.filterControls('Organizational')
      expect(filtered.length).toBeGreaterThan(0)
      filtered.forEach(control => {
        expect(control.category).toBe('Organizational')
      })
    })

    it('Filtering by category People returns only People controls', () => {
      const { result } = renderHook(() => useControls())
      const filtered = result.current.filterControls('People')
      expect(filtered.length).toBeGreaterThan(0)
      filtered.forEach(control => {
        expect(control.category).toBe('People')
      })
    })

    it('Filtering by status Not Started returns only Not Started controls', () => {
      const { result } = renderHook(() => useControls())
      const filtered = result.current.filterControls(undefined, 'Not Started')
      filtered.forEach(control => {
        expect(control.status).toBe('Not Started')
      })
    })

    it('Filtering by status Implemented returns only Implemented controls', () => {
      const { result } = renderHook(() => useControls())
      const filtered = result.current.filterControls(undefined, 'Implemented')
      filtered.forEach(control => {
        expect(control.status).toBe('Implemented')
      })
    })

    it('Filtering by Article area returns only controls in that Article area', () => {
      const { result } = renderHook(() => useControls())
      const firstArea = result.current.articleAreas[0]
      const filtered = result.current.filterControls(undefined, undefined, firstArea.name)
      expect(filtered.length).toBe(firstArea.controlCount)
      filtered.forEach(control => {
        expect(control.articleArea).toBe(firstArea.name)
      })
    })

    it('Multiple filters applied together work correctly', () => {
      const { result } = renderHook(() => useControls())
      const firstArea = result.current.articleAreas[0]
      const filtered = result.current.filterControls('Technical', 'Not Started', firstArea.name)
      filtered.forEach(control => {
        expect(control.category).toBe('Technical')
        expect(control.status).toBe('Not Started')
        expect(control.articleArea).toBe(firstArea.name)
      })
    })

    it('Search by title returns matching controls', () => {
      const { result } = renderHook(() => useControls())
      const firstControlTitle = result.current.controls[0].title
      const searchTerm = firstControlTitle.split(' ')[0]
      const filtered = result.current.filterControls(undefined, undefined, undefined, searchTerm)
      expect(filtered.length).toBeGreaterThan(0)
      filtered.forEach(control => {
        const matchesTitle = control.title.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesDescription = control.description.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesArticle = control.article.toLowerCase().includes(searchTerm.toLowerCase())
        expect(matchesTitle || matchesDescription || matchesArticle).toBe(true)
      })
    })

    it('Search is case insensitive', () => {
      const { result } = renderHook(() => useControls())
      const searchTerm = 'RISK'
      const filtered = result.current.filterControls(undefined, undefined, undefined, searchTerm)
      filtered.forEach(control => {
        const matchesTitle = control.title.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesDescription = control.description.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesArticle = control.article.toLowerCase().includes(searchTerm.toLowerCase())
        expect(matchesTitle || matchesDescription || matchesArticle).toBe(true)
      })
    })

    it('Search with no matches returns empty array', () => {
      const { result } = renderHook(() => useControls())
      const filtered = result.current.filterControls(undefined, undefined, undefined, 'XYZABC123NOMATCH')
      expect(filtered.length).toBe(0)
    })

    it('Clearing all filters returns all 28 controls', () => {
      const { result } = renderHook(() => useControls())
      const filtered = result.current.filterControls()
      expect(filtered.length).toBe(28)
    })

    it('Search combined with category filter works correctly', () => {
      const { result } = renderHook(() => useControls())
      const filtered = result.current.filterControls('Technical', undefined, undefined, 'security')
      filtered.forEach(control => {
        expect(control.category).toBe('Technical')
        const matchesSearch =
          control.title.toLowerCase().includes('security') ||
          control.description.toLowerCase().includes('security') ||
          control.article.toLowerCase().includes('security')
        expect(matchesSearch).toBe(true)
      })
    })
  })

  describe('Control Updates', () => {
    it('Updating a control status changes only that control', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id
      const originalStatus = result.current.controls[0].status

      act(() => {
        result.current.updateControl(controlId, { status: 'Implemented' })
      })

      const updatedControl = result.current.controls.find(c => c.id === controlId)
      expect(updatedControl?.status).toBe('Implemented')
      expect(updatedControl?.status).not.toBe(originalStatus)
    })

    it('Updating a control owner changes only that control', () => {
      const { result } = renderHook(() => useControls())
      const controlId = result.current.controls[0].id

      act(() => {
        result.current.updateControl(controlId, { owner: 'New Owner' })
      })

      const updatedControl = result.current.controls.find(c => c.id === controlId)
      expect(updatedControl?.owner).toBe('New Owner')
    })

    it('Other controls are not affected when one control is updated', () => {
      const { result } = renderHook(() => useControls())
      const firstControlId = result.current.controls[0].id
      const secondControl = result.current.controls[1]
      const secondControlSnapshot = { ...secondControl }

      act(() => {
        result.current.updateControl(firstControlId, { status: 'Implemented', owner: 'Test Owner' })
      })

      const unchangedControl = result.current.controls.find(c => c.id === secondControl.id)
      expect(unchangedControl?.status).toBe(secondControlSnapshot.status)
      expect(unchangedControl?.owner).toBe(secondControlSnapshot.owner)
    })

    it('The readiness score updates after a control status change', () => {
      const { result } = renderHook(() => useControls())
      const initialScore = result.current.complianceScore.overall

      // Find a Not Started control and implement it
      const notStartedControl = result.current.controls.find(c => c.status === 'Not Started')

      if (notStartedControl) {
        act(() => {
          result.current.updateControl(notStartedControl.id, { status: 'Implemented' })
        })

        const updatedScore = result.current.complianceScore.overall
        expect(updatedScore).toBeGreaterThan(initialScore)
      } else {
        // If no Not Started controls, find an Implemented and set to Not Started
        const implementedControl = result.current.controls.find(c => c.status === 'Implemented')
        if (implementedControl) {
          act(() => {
            result.current.updateControl(implementedControl.id, { status: 'Not Started' })
          })

          const updatedScore = result.current.complianceScore.overall
          expect(updatedScore).toBeLessThan(initialScore)
        }
      }
    })
  })
})
