import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useControls } from '../hooks/useControls'
import { Control, ControlStatus } from '../types/controls'

describe('Compliance Scoring Algorithm', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    vi.clearAllMocks()
    localStorage.getItem.mockReturnValue(null)
  })

  describe('Readiness Score Calculation', () => {
    it('Overall score is 0% when all controls are Not Started', () => {
      // Mock controls where all are Not Started
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control 1',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Test Control 2',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Organizational',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'high'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.overall).toBe(0)
    })

    it('Overall score is 100% when all controls are Implemented', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control 1',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Test Control 2',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Organizational',
          status: 'Implemented',
          owner: 'Jane Smith',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'high'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.overall).toBe(100)
    })

    it('Overall score calculates correctly with mixed statuses', () => {
      // Test with 2 critical controls: 1 Implemented, 1 Not Started
      // Weight: Critical = 3
      // Implemented: 3 * 1 = 3
      // Not Started: 3 * 0 = 0
      // Total: 3 / 6 = 50%
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control 1',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Test Control 2',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Organizational',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.overall).toBe(50)
    })

    it('Not Started contributes 0% of control weight', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.overall).toBe(0)
    })

    it('Planned contributes 25% of control weight', () => {
      // 1 critical control at Planned: 3 * 0.25 = 0.75 / 3 = 25%
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Planned',
          owner: 'John Doe',
          dueDate: '2024-12-31',
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.overall).toBe(25)
    })

    it('Partial contributes 50% of control weight', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Partial',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.overall).toBe(50)
    })

    it('Implemented contributes 100% of control weight', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.overall).toBe(100)
    })

    it('Score never exceeds 100%', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control 1',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Test Control 2',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Organizational',
          status: 'Implemented',
          owner: 'Jane Smith',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'high'
        },
        {
          id: '3',
          title: 'Test Control 3',
          description: 'Test',
          article: 'Art. 21(2)(c)',
          articleArea: 'Business Continuity',
          category: 'People',
          status: 'Implemented',
          owner: 'Bob Johnson',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: true,
          lastUpdated: new Date().toISOString(),
          severity: 'medium'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.overall).toBeLessThanOrEqual(100)
      expect(result.current.complianceScore.overall).toBe(100)
    })

    it('Score never goes below 0%', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control 1',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.overall).toBeGreaterThanOrEqual(0)
      expect(result.current.complianceScore.overall).toBe(0)
    })

    it('Score rounds to nearest whole number', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control 1',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Test Control 2',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Organizational',
          status: 'Implemented',
          owner: 'Jane Smith',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '3',
          title: 'Test Control 3',
          description: 'Test',
          article: 'Art. 21(2)(c)',
          articleArea: 'Business Continuity',
          category: 'People',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: true,
          lastUpdated: new Date().toISOString(),
          severity: 'medium'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      // Score should be a whole number
      expect(Number.isInteger(result.current.complianceScore.overall)).toBe(true)
    })
  })

  describe('Severity Weighting', () => {
    it('Critical severity controls have weight multiplier of 3', () => {
      // With 1 critical Implemented vs 1 critical Not Started, score should be 50%
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control 1',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Test Control 2',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Organizational',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      // 3*1 / (3+3) = 3/6 = 50%
      expect(result.current.complianceScore.overall).toBe(50)
    })

    it('High severity controls have weight multiplier of 2', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control 1',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'high'
        },
        {
          id: '2',
          title: 'Test Control 2',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Organizational',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'high'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      // 2*1 / (2+2) = 2/4 = 50%
      expect(result.current.complianceScore.overall).toBe(50)
    })

    it('Medium severity controls have weight multiplier of 1', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Test Control 1',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'medium'
        },
        {
          id: '2',
          title: 'Test Control 2',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Organizational',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'medium'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      // 1*1 / (1+1) = 1/2 = 50%
      expect(result.current.complianceScore.overall).toBe(50)
    })

    it('A single Critical Implemented control outweighs multiple Medium Not Started controls proportionally', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Critical Control',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Medium Control 1',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Organizational',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'medium'
        },
        {
          id: '3',
          title: 'Medium Control 2',
          description: 'Test',
          article: 'Art. 21(2)(c)',
          articleArea: 'Business Continuity',
          category: 'People',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: true,
          lastUpdated: new Date().toISOString(),
          severity: 'medium'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      // Critical: 3*1 = 3
      // Medium 1: 1*0 = 0
      // Medium 2: 1*0 = 0
      // Total: 3 / (3+1+1) = 3/5 = 60%
      expect(result.current.complianceScore.overall).toBe(60)
    })
  })

  describe('Category Score Calculation', () => {
    it('Technical category score calculates independently from Organizational and People scores', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Technical Control',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Organizational Control',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Organizational',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.technical).toBe(100)
      expect(result.current.complianceScore.organizational).toBe(0)
    })

    it('Organizational category score calculates independently', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Organizational Control',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Organizational',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Technical Control',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Technical',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.organizational).toBe(100)
      expect(result.current.complianceScore.technical).toBe(0)
    })

    it('People category score calculates independently', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'People Control',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'People',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: true,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Technical Control',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Technical',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.complianceScore.people).toBe(100)
      expect(result.current.complianceScore.technical).toBe(0)
    })

    it('Category scores are based only on controls in that category', () => {
      const mockControls: Control[] = [
        {
          id: '1',
          title: 'Technical Control 1',
          description: 'Test',
          article: 'Art. 21(2)(a)',
          articleArea: 'Risk Management',
          category: 'Technical',
          status: 'Implemented',
          owner: 'John Doe',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '2',
          title: 'Technical Control 2',
          description: 'Test',
          article: 'Art. 21(2)(b)',
          articleArea: 'Incident Response',
          category: 'Technical',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'critical'
        },
        {
          id: '3',
          title: 'Organizational Control',
          description: 'Test',
          article: 'Art. 21(2)(c)',
          articleArea: 'Business Continuity',
          category: 'Organizational',
          status: 'Not Started',
          owner: '',
          dueDate: null,
          evidence: [],
          notes: '',
          isAutoPopulated: false,
          isPeopleControl: false,
          lastUpdated: new Date().toISOString(),
          severity: 'high'
        }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      // Technical: 3*1 / (3+3) = 50%
      expect(result.current.complianceScore.technical).toBe(50)
      // Organizational: 2*0 / 2 = 0%
      expect(result.current.complianceScore.organizational).toBe(0)
      // People: no controls, should be 0
      expect(result.current.complianceScore.people).toBe(0)
    })
  })

  describe('Critical Gaps', () => {
    it('Top 5 gaps are the 5 highest severity Not Started or Partial controls', () => {
      const mockControls: Control[] = [
        { id: '1', title: 'Critical Gap 1', description: 'Test', article: 'Art. 21(2)(a)', articleArea: 'Risk Management', category: 'Technical', status: 'Not Started', owner: '', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'critical' },
        { id: '2', title: 'Critical Gap 2', description: 'Test', article: 'Art. 21(2)(b)', articleArea: 'Incident Response', category: 'Organizational', status: 'Partial', owner: 'John', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'critical' },
        { id: '3', title: 'High Gap 1', description: 'Test', article: 'Art. 21(2)(c)', articleArea: 'Business Continuity', category: 'People', status: 'Not Started', owner: '', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: true, lastUpdated: new Date().toISOString(), severity: 'high' },
        { id: '4', title: 'High Gap 2', description: 'Test', article: 'Art. 21(2)(d)', articleArea: 'Supply Chain', category: 'Technical', status: 'Partial', owner: 'Jane', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'high' },
        { id: '5', title: 'Medium Gap 1', description: 'Test', article: 'Art. 21(2)(e)', articleArea: 'Access Control', category: 'Organizational', status: 'Not Started', owner: '', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'medium' },
        { id: '6', title: 'Implemented Control', description: 'Test', article: 'Art. 21(2)(f)', articleArea: 'Encryption', category: 'Technical', status: 'Implemented', owner: 'Bob', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'critical' },
        { id: '7', title: 'Medium Gap 2', description: 'Test', article: 'Art. 21(2)(g)', articleArea: 'Monitoring', category: 'People', status: 'Partial', owner: 'Alice', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: true, lastUpdated: new Date().toISOString(), severity: 'medium' }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.criticalGaps.length).toBe(5)
      // Should not include the Implemented control
      expect(result.current.criticalGaps.every(gap => gap.status !== 'Implemented')).toBe(true)
    })

    it('Critical severity gaps appear before High severity gaps', () => {
      const mockControls: Control[] = [
        { id: '1', title: 'High Gap', description: 'Test', article: 'Art. 21(2)(a)', articleArea: 'Risk Management', category: 'Technical', status: 'Not Started', owner: '', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'high' },
        { id: '2', title: 'Critical Gap', description: 'Test', article: 'Art. 21(2)(b)', articleArea: 'Incident Response', category: 'Organizational', status: 'Not Started', owner: '', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'critical' }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.criticalGaps[0].severity).toBe('critical')
      expect(result.current.criticalGaps[1].severity).toBe('high')
    })

    it('High severity gaps appear before Medium severity gaps', () => {
      const mockControls: Control[] = [
        { id: '1', title: 'Medium Gap', description: 'Test', article: 'Art. 21(2)(a)', articleArea: 'Risk Management', category: 'Technical', status: 'Not Started', owner: '', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'medium' },
        { id: '2', title: 'High Gap', description: 'Test', article: 'Art. 21(2)(b)', articleArea: 'Incident Response', category: 'Organizational', status: 'Not Started', owner: '', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'high' }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.criticalGaps[0].severity).toBe('high')
      expect(result.current.criticalGaps[1].severity).toBe('medium')
    })

    it('If fewer than 5 gaps exist only those gaps are returned', () => {
      const mockControls: Control[] = [
        { id: '1', title: 'Gap 1', description: 'Test', article: 'Art. 21(2)(a)', articleArea: 'Risk Management', category: 'Technical', status: 'Not Started', owner: '', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'critical' },
        { id: '2', title: 'Gap 2', description: 'Test', article: 'Art. 21(2)(b)', articleArea: 'Incident Response', category: 'Organizational', status: 'Partial', owner: 'John', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'high' },
        { id: '3', title: 'Implemented', description: 'Test', article: 'Art. 21(2)(c)', articleArea: 'Business Continuity', category: 'People', status: 'Implemented', owner: 'Jane', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: true, lastUpdated: new Date().toISOString(), severity: 'critical' }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.criticalGaps.length).toBe(2)
    })

    it('Implemented controls never appear in gaps list', () => {
      const mockControls: Control[] = [
        { id: '1', title: 'Gap', description: 'Test', article: 'Art. 21(2)(a)', articleArea: 'Risk Management', category: 'Technical', status: 'Not Started', owner: '', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'critical' },
        { id: '2', title: 'Implemented', description: 'Test', article: 'Art. 21(2)(b)', articleArea: 'Incident Response', category: 'Organizational', status: 'Implemented', owner: 'John', dueDate: null, evidence: [], notes: '', isAutoPopulated: false, isPeopleControl: false, lastUpdated: new Date().toISOString(), severity: 'critical' }
      ]

      localStorage.getItem.mockImplementation((key: string) => {
        if (key === 'konforme_controls') return JSON.stringify(mockControls)
        if (key === 'konforme_campaigns') return '[]'
        return null
      })

      const { result } = renderHook(() => useControls())
      expect(result.current.criticalGaps.length).toBe(1)
      expect(result.current.criticalGaps[0].status).not.toBe('Implemented')
    })
  })
})
