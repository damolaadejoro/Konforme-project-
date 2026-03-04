export type ControlCategory = 'Technical' | 'Organizational' | 'People'
export type ControlStatus = 'Not Started' | 'Planned' | 'Partial' | 'Implemented'
export type ControlSeverity = 'critical' | 'high' | 'medium'
export type TaskType = 'acknowledge' | 'quiz'
export type TaskStatus = 'pending' | 'completed' | 'overdue'

export interface Control {
  id: string
  title: string
  description: string
  article: string // e.g., "Art. 21(2)(a)"
  articleArea: string // e.g., "Risk Management"
  category: ControlCategory
  status: ControlStatus
  owner: string
  dueDate: string | null
  evidence: Evidence[]
  notes: string
  isAutoPopulated: boolean // for AWS scanner controls
  isPeopleControl: boolean
  lastUpdated: string
  severity: ControlSeverity
}

export interface Evidence {
  id: string
  filename: string
  uploadedAt: string
  uploadedBy: string
  fileSize?: string
}

export interface EmployeeTask {
  id: string
  controlId: string
  campaignId: string
  employeeName: string
  employeeEmail: string
  department: string
  taskType: TaskType
  status: TaskStatus
  sentDate: string
  completedDate: string | null
  deadline: string
  score?: number // for quiz tasks
}

export interface EmployeeCampaign {
  id: string
  controlId: string
  controlName: string
  taskType: TaskType
  deadline: string
  createdAt: string
  tasks: EmployeeTask[]
  policyContent?: string // for acknowledge tasks
}

export interface QuizQuestion {
  id: string
  question: string
  options: string[]
  correctAnswer: number // index of correct option
  explanation?: string
}

export interface QuizResult {
  score: number
  total: number
  passed: boolean
  completedAt: string
}

export interface ArticleArea {
  id: string
  name: string
  article: string
  controlCount: number
  implementedCount: number
  status: ControlStatus
}

export interface ComplianceScore {
  overall: number
  technical: number
  organizational: number
  people: number
  byArticle: Record<string, number>
}
