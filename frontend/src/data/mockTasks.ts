export interface MockTask {
  id: string
  type: 'acknowledge' | 'quiz'
  employeeName: string
  employeeEmail: string
  company: string
  taskName: string
  assignedBy: string
  dueDate: string
  policyContent?: {
    title: string
    summary: string[]
  }
}

export const mockTasks: Record<string, MockTask> = {
  'task-001': {
    id: 'task-001',
    type: 'acknowledge',
    employeeName: 'Alice Johnson',
    employeeEmail: 'alice.johnson@acmecorp.com',
    company: 'Acme Corp',
    taskName: 'Acknowledge Information Security Policy',
    assignedBy: 'IT Security Team',
    dueDate: '2024-05-15',
    policyContent: {
      title: 'Information Security Policy',
      summary: [
        'You are responsible for protecting company data and systems',
        'Passwords must be strong, unique, and never shared',
        'Report any suspicious activity or security incidents to IT immediately',
        'Only use approved software and applications on company devices',
        'Confidential data must not be shared outside the organization without authorization'
      ]
    }
  },
  'task-002': {
    id: 'task-002',
    type: 'quiz',
    employeeName: 'Bob Martinez',
    employeeEmail: 'bob.martinez@acmecorp.com',
    company: 'Acme Corp',
    taskName: 'Security Awareness Training',
    assignedBy: 'IT Security Team',
    dueDate: '2024-06-30'
  },
  'task-003': {
    id: 'task-003',
    type: 'acknowledge',
    employeeName: 'Sarah Chen',
    employeeEmail: 'sarah.chen@acmecorp.com',
    company: 'Acme Corp',
    taskName: 'Acknowledge Information Security Policy',
    assignedBy: 'IT Security Team',
    dueDate: '2024-05-15',
    policyContent: {
      title: 'Information Security Policy',
      summary: [
        'You are responsible for protecting company data and systems',
        'Passwords must be strong, unique, and never shared',
        'Report any suspicious activity or security incidents to IT immediately',
        'Only use approved software and applications on company devices',
        'Confidential data must not be shared outside the organization without authorization'
      ]
    }
  },
  'task-004': {
    id: 'task-004',
    type: 'quiz',
    employeeName: 'David Okafor',
    employeeEmail: 'david.okafor@acmecorp.com',
    company: 'Acme Corp',
    taskName: 'Security Awareness Training',
    assignedBy: 'IT Security Team',
    dueDate: '2024-06-30'
  }
}

export interface QuizQuestionData {
  id: string
  question: string
  options: string[]
  correctAnswer: number
  explanation: string
}

export const quizQuestionsData: QuizQuestionData[] = [
  {
    id: 'q1',
    question: 'What should you do if you receive a suspicious email?',
    options: [
      'Forward it to colleagues',
      'Delete it immediately without doing anything',
      'Report it to the IT security team',
      'Open the attachment to verify if it\'s safe'
    ],
    correctAnswer: 2,
    explanation: 'Reporting suspicious emails helps IT investigate and protect the whole company.'
  },
  {
    id: 'q2',
    question: 'What is the safest way to handle your work password?',
    options: [
      'Write it on a sticky note near your desk',
      'Use a unique strong password and never share it',
      'Use the same password as your personal accounts',
      'Share it with your manager for safekeeping'
    ],
    correctAnswer: 1,
    explanation: 'Unique strong passwords prevent unauthorized access if one account is compromised.'
  },
  {
    id: 'q3',
    question: 'What should you do when leaving your workstation, even briefly?',
    options: [
      'Leave everything open — you\'ll be back soon',
      'Ask a colleague to watch it',
      'Lock your screen',
      'Shut the computer down completely'
    ],
    correctAnswer: 2,
    explanation: 'Locking your screen prevents unauthorized access in seconds.'
  },
  {
    id: 'q4',
    question: 'What is phishing?',
    options: [
      'A type of software vulnerability',
      'An attempt to trick you into revealing credentials or clicking malicious links',
      'A network performance issue',
      'A type of antivirus software'
    ],
    correctAnswer: 1,
    explanation: 'Phishing is the most common way attackers gain access to company systems.'
  },
  {
    id: 'q5',
    question: 'Who should you contact first if you suspect a security incident?',
    options: [
      'No one — try to fix it yourself',
      'Your personal IT contact',
      'The IT security team or your manager',
      'Post about it on social media to warn others'
    ],
    correctAnswer: 2,
    explanation: 'Fast reporting to the right people minimizes damage from security incidents.'
  }
]
