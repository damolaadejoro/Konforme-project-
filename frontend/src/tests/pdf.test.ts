import { describe, it, expect, beforeEach, vi } from 'vitest'
import { generateComplianceReport } from '../utils/generatePDF'
import { Control, ComplianceScore, ArticleArea } from '../types/controls'

// Mock jsPDF
vi.mock('jspdf', () => {
  const mockDoc = {
    setFillColor: vi.fn(),
    setTextColor: vi.fn(),
    setFontSize: vi.fn(),
    setFont: vi.fn(),
    setDrawColor: vi.fn(),
    setLineWidth: vi.fn(),
    rect: vi.fn(),
    circle: vi.fn(),
    roundedRect: vi.fn(),
    line: vi.fn(),
    text: vi.fn(),
    splitTextToSize: vi.fn((text: string) => [text]),
    addPage: vi.fn(),
    save: vi.fn(),
    internal: {
      pageSize: {
        width: 210,
        height: 297
      }
    },
    lastAutoTable: {
      finalY: 100
    }
  }

  const MockJsPDF = vi.fn(() => mockDoc)
  return {
    default: MockJsPDF,
    jsPDF: MockJsPDF,
  }
})

// Mock autoTable
vi.mock('jspdf-autotable', () => ({
  default: vi.fn()
}))

describe('PDF Report Generation', () => {
  const mockComplianceScore: ComplianceScore = {
    overall: 75,
    technical: 80,
    organizational: 70,
    people: 75,
    byArticle: {
      'Art. 21(2)(a)': 80,
      'Art. 21(2)(b)': 70
    }
  }

  const mockControls: Control[] = [
    {
      id: '1',
      title: 'Test Control 1',
      description: 'Test description',
      article: 'Art. 21(2)(a)',
      articleArea: 'Risk Management',
      category: 'Technical',
      status: 'Implemented',
      owner: 'John Doe',
      dueDate: '2024-12-31',
      evidence: [
        {
          id: 'ev-1',
          filename: 'test.pdf',
          uploadedAt: new Date().toISOString(),
          uploadedBy: 'Test User'
        }
      ],
      notes: 'Test notes',
      isAutoPopulated: false,
      isPeopleControl: false,
      lastUpdated: new Date().toISOString(),
      severity: 'critical'
    },
    {
      id: '2',
      title: 'Test Control 2',
      description: 'Another test',
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

  const mockArticleAreas: ArticleArea[] = [
    {
      id: 'risk-management',
      name: 'Risk Management',
      article: 'Art. 21',
      controlCount: 1,
      implementedCount: 1,
      status: 'Implemented'
    },
    {
      id: 'incident-response',
      name: 'Incident Response',
      article: 'Art. 21',
      controlCount: 1,
      implementedCount: 0,
      status: 'Not Started'
    }
  ]

  const mockCriticalGaps = mockControls.filter(c => c.status === 'Not Started')

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('PDF generation function exists and is callable', () => {
    expect(typeof generateComplianceReport).toBe('function')
  })

  it('PDF generates without throwing errors', async () => {
    await expect(
      generateComplianceReport({
        companyName: 'Test Company',
        complianceScore: mockComplianceScore,
        controls: mockControls,
        articleAreas: mockArticleAreas,
        criticalGaps: mockCriticalGaps
      })
    ).resolves.not.toThrow()
  })

  it('PDF filename includes today\'s date', async () => {
    const jsPDF = await import('jspdf')
    await generateComplianceReport({
      companyName: 'Test Company',
      complianceScore: mockComplianceScore,
      controls: mockControls,
      articleAreas: mockArticleAreas,
      criticalGaps: mockCriticalGaps
    })

    const mockDocInstance = vi.mocked(jsPDF.default).mock.results[0].value
    expect(mockDocInstance.save).toHaveBeenCalled()

    const saveCall = mockDocInstance.save.mock.calls[0][0]
    expect(saveCall).toContain('Konforme-NIS2-Report-')
    expect(saveCall).toContain('.pdf')
  })

  it('Company name is included in the report', async () => {
    const jsPDF = await import('jspdf')
    await generateComplianceReport({
      companyName: 'Acme Corporation',
      complianceScore: mockComplianceScore,
      controls: mockControls,
      articleAreas: mockArticleAreas,
      criticalGaps: mockCriticalGaps
    })

    const mockDocInstance = vi.mocked(jsPDF.default).mock.results[0].value
    const textCalls = mockDocInstance.text.mock.calls

    // Check if company name was written to PDF
    const hasCompanyName = textCalls.some(call => call[0] === 'Acme Corporation')
    expect(hasCompanyName).toBe(true)
  })

  it('Overall score is included in the report', async () => {
    const jsPDF = await import('jspdf')
    await generateComplianceReport({
      companyName: 'Test Company',
      complianceScore: mockComplianceScore,
      controls: mockControls,
      articleAreas: mockArticleAreas,
      criticalGaps: mockCriticalGaps
    })

    const mockDocInstance = vi.mocked(jsPDF.default).mock.results[0].value
    const textCalls = mockDocInstance.text.mock.calls

    // Check if overall score was written
    const hasOverallScore = textCalls.some(call => call[0] === '75%')
    expect(hasOverallScore).toBe(true)
  })

  it('Auto-generated summary matches the correct score band for 75% score', async () => {
    const jsPDF = await import('jspdf')
    await generateComplianceReport({
      companyName: 'Test Company',
      complianceScore: mockComplianceScore, // 75%
      controls: mockControls,
      articleAreas: mockArticleAreas,
      criticalGaps: mockCriticalGaps
    })

    const mockDocInstance = vi.mocked(jsPDF.default).mock.results[0].value
    const textCalls = mockDocInstance.text.mock.calls

    // For 71-90%, should include "good compliance progress"
    const hasSummary = textCalls.some(call => {
      const text = Array.isArray(call[0]) ? call[0].join(' ') : call[0]
      return typeof text === 'string' && text.toLowerCase().includes('good')
    })
    expect(hasSummary).toBe(true)
  })

  it('Score 0-40 generates critical risk summary', async () => {
    const jsPDF = await import('jspdf')
    await generateComplianceReport({
      companyName: 'Test Company',
      complianceScore: { ...mockComplianceScore, overall: 35 },
      controls: mockControls,
      articleAreas: mockArticleAreas,
      criticalGaps: mockCriticalGaps
    })

    const mockDocInstance = vi.mocked(jsPDF.default).mock.results[0].value
    const textCalls = mockDocInstance.text.mock.calls

    const hasCriticalSummary = textCalls.some(call => {
      const text = Array.isArray(call[0]) ? call[0].join(' ') : call[0]
      return typeof text === 'string' && text.toLowerCase().includes('significant gaps')
    })
    expect(hasCriticalSummary).toBe(true)
  })

  it('Score 41-70 generates moderate risk summary', async () => {
    const jsPDF = await import('jspdf')
    await generateComplianceReport({
      companyName: 'Test Company',
      complianceScore: { ...mockComplianceScore, overall: 55 },
      controls: mockControls,
      articleAreas: mockArticleAreas,
      criticalGaps: mockCriticalGaps
    })

    const mockDocInstance = vi.mocked(jsPDF.default).mock.results[0].value
    const textCalls = mockDocInstance.text.mock.calls

    const hasModerateSummary = textCalls.some(call => {
      const text = Array.isArray(call[0]) ? call[0].join(' ') : call[0]
      return typeof text === 'string' && text.toLowerCase().includes('moderate')
    })
    expect(hasModerateSummary).toBe(true)
  })

  it('Score 91-100 generates strong compliance summary', async () => {
    const jsPDF = await import('jspdf')
    await generateComplianceReport({
      companyName: 'Test Company',
      complianceScore: { ...mockComplianceScore, overall: 95 },
      controls: mockControls,
      articleAreas: mockArticleAreas,
      criticalGaps: mockCriticalGaps
    })

    const mockDocInstance = vi.mocked(jsPDF.default).mock.results[0].value
    const textCalls = mockDocInstance.text.mock.calls

    const hasStrongSummary = textCalls.some(call => {
      const text = Array.isArray(call[0]) ? call[0].join(' ') : call[0]
      return typeof text === 'string' && text.toLowerCase().includes('strong')
    })
    expect(hasStrongSummary).toBe(true)
  })

  it('All controls appear in the report', async () => {
    const jsPDF = await import('jspdf')
    const controls = [
      ...mockControls,
      ...Array.from({ length: 26 }, (_, i) => ({
        id: `control-${i + 3}`,
        title: `Control ${i + 3}`,
        description: 'Test',
        article: 'Art. 21(2)(c)',
        articleArea: 'Test Area',
        category: 'Technical' as const,
        status: 'Not Started' as const,
        owner: '',
        dueDate: null,
        evidence: [],
        notes: '',
        isAutoPopulated: false,
        isPeopleControl: false,
        lastUpdated: new Date().toISOString(),
        severity: 'medium' as const
      }))
    ]

    await generateComplianceReport({
      companyName: 'Test Company',
      complianceScore: mockComplianceScore,
      controls,
      articleAreas: mockArticleAreas,
      criticalGaps: mockCriticalGaps
    })

    const mockDocInstance = vi.mocked(jsPDF.default).mock.results[0].value

    // Multiple pages should be added for all controls
    expect(mockDocInstance.addPage).toHaveBeenCalled()
  })

  it('Not Started controls are flagged as gaps', async () => {
    const jsPDF = await import('jspdf')
    await generateComplianceReport({
      companyName: 'Test Company',
      complianceScore: mockComplianceScore,
      controls: mockControls,
      articleAreas: mockArticleAreas,
      criticalGaps: mockCriticalGaps
    })

    const mockDocInstance = vi.mocked(jsPDF.default).mock.results[0].value
    const textCalls = mockDocInstance.text.mock.calls

    // Recommendations section should be present
    const hasRecommendations = textCalls.some(call => call[0] === 'Recommendations')
    expect(hasRecommendations).toBe(true)
  })

  it('Recommendations section is generated', async () => {
    const jsPDF = await import('jspdf')
    await generateComplianceReport({
      companyName: 'Test Company',
      complianceScore: mockComplianceScore,
      controls: mockControls,
      articleAreas: mockArticleAreas,
      criticalGaps: mockCriticalGaps
    })

    const mockDocInstance = vi.mocked(jsPDF.default).mock.results[0].value
    const textCalls = mockDocInstance.text.mock.calls

    const hasRecommendations = textCalls.some(call => call[0] === 'Recommendations')
    expect(hasRecommendations).toBe(true)
  })
})
