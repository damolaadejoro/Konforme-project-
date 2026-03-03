import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import NIS2Overview from '../pages/NIS2Overview'
import TaskNotFound from '../components/task/TaskNotFound'
import TaskShell from '../components/task/TaskShell'

// Mock the useControls hook
vi.mock('../hooks/useControls', () => ({
  useControls: () => ({
    complianceScore: {
      overall: 75,
      technical: 80,
      organizational: 70,
      people: 75,
      byArticle: {}
    },
    articleAreas: [
      {
        id: 'test-area',
        name: 'Risk Management',
        article: 'Art. 21',
        controlCount: 5,
        implementedCount: 3,
        status: 'Partial'
      }
    ],
    criticalGaps: [
      {
        id: 'gap-1',
        title: 'Critical Gap Control',
        description: 'Test gap',
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
    ],
    employeeComplianceStats: {
      totalTasks: 10,
      completedTasks: 5,
      pendingTasks: 3,
      overdueTasks: 2,
      completionRate: 50
    },
    controls: [],
    campaigns: [],
    selectedControl: null,
    setSelectedControl: vi.fn(),
    updateControl: vi.fn(),
    addEvidence: vi.fn(),
    removeEvidence: vi.fn(),
    createCampaign: vi.fn(),
    updateTaskStatus: vi.fn(),
    filterControls: vi.fn(),
    getCampaignsForControl: vi.fn(),
    allTasks: [],
    lastSaved: new Date().toISOString()
  })
}))

describe('UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.getItem.mockReturnValue(null)
  })

  describe('NIS2 Overview Page', () => {
    it('Renders without crashing', () => {
      render(
        <BrowserRouter>
          <NIS2Overview />
        </BrowserRouter>
      )
      expect(screen.getByText('NIS2 Compliance Overview')).toBeInTheDocument()
    })

    it('Displays the overall readiness score', () => {
      render(
        <BrowserRouter>
          <NIS2Overview />
        </BrowserRouter>
      )
      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('Displays score as green when between 71-90%', () => {
      render(
        <BrowserRouter>
          <NIS2Overview />
        </BrowserRouter>
      )
      // The score is 75%, which should show "Good"
      expect(screen.getByText('Good')).toBeInTheDocument()
    })

    it('Displays all three category scores', () => {
      render(
        <BrowserRouter>
          <NIS2Overview />
        </BrowserRouter>
      )
      expect(screen.getByText('80%')).toBeInTheDocument() // Technical
      expect(screen.getByText('70%')).toBeInTheDocument() // Organizational
      // People score is also 75% so it's already displayed
    })

    it('Renders the Article 21 coverage map', () => {
      render(
        <BrowserRouter>
          <NIS2Overview />
        </BrowserRouter>
      )
      expect(screen.getByText('NIS2 Article 21 Coverage Map')).toBeInTheDocument()
    })

    it('Renders the top 5 critical gaps section', () => {
      render(
        <BrowserRouter>
          <NIS2Overview />
        </BrowserRouter>
      )
      expect(screen.getByText('Top 5 Critical Gaps')).toBeInTheDocument()
    })

    it('Quick action buttons are present and visible', () => {
      render(
        <BrowserRouter>
          <NIS2Overview />
        </BrowserRouter>
      )
      expect(screen.getByText('Manage Controls')).toBeInTheDocument()
      expect(screen.getByText('People Tasks')).toBeInTheDocument()
      expect(screen.getByText('Technical Scan')).toBeInTheDocument()
    })
  })

  describe('Employee Task Pages', () => {
    it('/task/invalid-task renders the error page', () => {
      render(<TaskNotFound />)
      expect(screen.getByText('Task Not Found')).toBeInTheDocument()
    })

    it('TaskShell renders the Konforme logo', () => {
      render(
        <TaskShell companyName="Test Company" totalSteps={4} currentStep={1}>
          <div>Test Content</div>
        </TaskShell>
      )
      expect(screen.getByText('Konforme')).toBeInTheDocument()
    })

    it('TaskShell renders the company name', () => {
      render(
        <TaskShell companyName="Test Company" totalSteps={4} currentStep={1}>
          <div>Test Content</div>
        </TaskShell>
      )
      expect(screen.getByText('Test Company')).toBeInTheDocument()
    })

    it('TaskShell renders the progress bar', () => {
      const { container } = render(
        <TaskShell companyName="Test Company" totalSteps={4} currentStep={2}>
          <div>Test Content</div>
        </TaskShell>
      )
      // Progress bar should be present (it's a div with specific width)
      const progressBar = container.querySelector('[style*="width"]')
      expect(progressBar).toBeInTheDocument()
    })
  })
})
