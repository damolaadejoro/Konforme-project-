import { Control, EmployeeCampaign, QuizQuestion } from '../types/controls'

export const controls: Control[] = [
  // RISK MANAGEMENT (Art. 21(2)(a))
  {
    id: 'ctrl-001',
    title: 'Information Security Policy document',
    description: 'A formal information security policy approved by management and communicated to all staff. Must cover scope, responsibilities, acceptable use, data classification, and incident response.',
    article: 'Art. 21(2)(a)',
    articleArea: 'Risk Management',
    category: 'Organizational',
    status: 'Implemented',
    owner: 'Sarah Chen (CISO)',
    dueDate: '2024-12-31',
    evidence: [
      {
        id: 'ev-001',
        filename: 'Information_Security_Policy_v2.1.pdf',
        uploadedAt: '2024-01-15T10:30:00Z',
        uploadedBy: 'Sarah Chen',
        fileSize: '2.4 MB'
      },
      {
        id: 'ev-002',
        filename: 'Board_Approval_Minutes_2024-01.pdf',
        uploadedAt: '2024-01-20T14:15:00Z',
        uploadedBy: 'Sarah Chen',
        fileSize: '856 KB'
      }
    ],
    notes: 'Policy reviewed and approved by board in January 2024. Next review scheduled for Q1 2025.',
    isAutoPopulated: false,
    isPeopleControl: true,
    lastUpdated: '2024-01-20T14:15:00Z',
    severity: 'critical'
  },
  {
    id: 'ctrl-002',
    title: 'Annual risk assessment process',
    description: 'Regular risk assessments to identify threats, vulnerabilities, and impacts to critical services. Must use a recognized framework (ISO 27005, NIST).',
    article: 'Art. 21(2)(a)',
    articleArea: 'Risk Management',
    category: 'Organizational',
    status: 'Partial',
    owner: 'Michael Rodriguez',
    dueDate: '2024-06-30',
    evidence: [
      {
        id: 'ev-003',
        filename: 'Risk_Assessment_Framework_2024.pdf',
        uploadedAt: '2024-02-10T09:00:00Z',
        uploadedBy: 'Michael Rodriguez',
        fileSize: '1.8 MB'
      }
    ],
    notes: 'Framework documented. Annual assessment in progress, 60% complete.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-02-10T09:00:00Z',
    severity: 'critical'
  },
  {
    id: 'ctrl-003',
    title: 'Risk register maintained and reviewed',
    description: 'Active risk register tracking all identified cybersecurity risks with likelihood, impact, mitigation plans, and owners.',
    article: 'Art. 21(2)(a)',
    articleArea: 'Risk Management',
    category: 'Organizational',
    status: 'Implemented',
    owner: 'Michael Rodriguez',
    dueDate: null,
    evidence: [
      {
        id: 'ev-004',
        filename: 'Q1_2024_Risk_Register.xlsx',
        uploadedAt: '2024-03-28T16:45:00Z',
        uploadedBy: 'Michael Rodriguez',
        fileSize: '245 KB'
      }
    ],
    notes: 'Risk register reviewed quarterly. 14 active risks tracked, 3 critical.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-28T16:45:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-004',
    title: 'Security roles and responsibilities defined',
    description: 'Clear accountability with documented RACI matrix for security functions. Roles like CISO, security team, system owners must be formally defined.',
    article: 'Art. 21(2)(a)',
    articleArea: 'Risk Management',
    category: 'Organizational',
    status: 'Implemented',
    owner: 'Sarah Chen (CISO)',
    dueDate: null,
    evidence: [
      {
        id: 'ev-005',
        filename: 'Security_RACI_Matrix_2024.pdf',
        uploadedAt: '2024-01-15T11:00:00Z',
        uploadedBy: 'Sarah Chen',
        fileSize: '180 KB'
      }
    ],
    notes: 'RACI matrix covers all security domains. Included in security policy.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-01-15T11:00:00Z',
    severity: 'high'
  },

  // INCIDENT HANDLING (Art. 21(2)(b))
  {
    id: 'ctrl-005',
    title: 'Incident response plan documented',
    description: 'Formal incident response process covering detection, containment, eradication, recovery, and lessons learned. Must include escalation paths and communication templates.',
    article: 'Art. 21(2)(b)',
    articleArea: 'Incident Handling',
    category: 'Organizational',
    status: 'Implemented',
    owner: 'James Park',
    dueDate: null,
    evidence: [
      {
        id: 'ev-006',
        filename: 'Incident_Response_Plan_v3.2.pdf',
        uploadedAt: '2024-02-05T13:20:00Z',
        uploadedBy: 'James Park',
        fileSize: '3.1 MB'
      },
      {
        id: 'ev-007',
        filename: 'IR_Playbook_Ransomware.pdf',
        uploadedAt: '2024-02-05T13:25:00Z',
        uploadedBy: 'James Park',
        fileSize: '1.2 MB'
      }
    ],
    notes: 'Plan covers 6 major incident types with detailed playbooks.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-02-05T13:25:00Z',
    severity: 'critical'
  },
  {
    id: 'ctrl-006',
    title: 'Incident classification and escalation process',
    description: 'Defined severity levels (Critical, High, Medium, Low) with clear escalation criteria, response SLAs, and notification requirements.',
    article: 'Art. 21(2)(b)',
    articleArea: 'Incident Handling',
    category: 'Organizational',
    status: 'Implemented',
    owner: 'James Park',
    dueDate: null,
    evidence: [
      {
        id: 'ev-008',
        filename: 'Incident_Severity_Matrix.pdf',
        uploadedAt: '2024-02-05T14:00:00Z',
        uploadedBy: 'James Park',
        fileSize: '420 KB'
      }
    ],
    notes: 'SLAs: Critical 1h, High 4h, Medium 24h. Escalation paths defined.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-02-05T14:00:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-007',
    title: 'CSIRT registration completed',
    description: 'Organization registered with national Computer Security Incident Response Team (CSIRT) for mandatory incident reporting.',
    article: 'Art. 21(2)(b)',
    articleArea: 'Incident Handling',
    category: 'Organizational',
    status: 'Implemented',
    owner: 'Sarah Chen (CISO)',
    dueDate: null,
    evidence: [
      {
        id: 'ev-009',
        filename: 'CSIRT_Registration_Confirmation.pdf',
        uploadedAt: '2023-12-10T10:00:00Z',
        uploadedBy: 'Sarah Chen',
        fileSize: '95 KB'
      }
    ],
    notes: 'Registered with national CSIRT. Contact details documented in IR plan.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2023-12-10T10:00:00Z',
    severity: 'critical'
  },
  {
    id: 'ctrl-008',
    title: 'Incident response tabletop exercise conducted (last 12 months)',
    description: 'Regular testing of incident response plan through tabletop exercises or simulations.',
    article: 'Art. 21(2)(b)',
    articleArea: 'Incident Handling',
    category: 'Organizational',
    status: 'Planned',
    owner: 'James Park',
    dueDate: '2024-05-15',
    evidence: [],
    notes: 'Exercise scheduled for May 2024. Scenario: ransomware attack on production systems.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-20T09:30:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-009',
    title: '24-hour notification process to authorities defined',
    description: 'Clear process for early warning notification to authorities within 24 hours of detecting a significant incident.',
    article: 'Art. 23',
    articleArea: 'Incident Handling',
    category: 'Organizational',
    status: 'Implemented',
    owner: 'James Park',
    dueDate: null,
    evidence: [
      {
        id: 'ev-010',
        filename: 'Incident_Notification_Procedure.pdf',
        uploadedAt: '2024-02-05T15:00:00Z',
        uploadedBy: 'James Park',
        fileSize: '560 KB'
      }
    ],
    notes: '24h, 72h, and final report templates ready. Notification contacts verified.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-02-05T15:00:00Z',
    severity: 'critical'
  },

  // BUSINESS CONTINUITY (Art. 21(2)(c))
  {
    id: 'ctrl-010',
    title: 'Business continuity plan documented',
    description: 'BCP ensuring critical services can continue during disruptions. Must cover critical functions, dependencies, alternate arrangements, and communication plans.',
    article: 'Art. 21(2)(c)',
    articleArea: 'Business Continuity',
    category: 'Organizational',
    status: 'Partial',
    owner: 'Lisa Martinez',
    dueDate: '2024-07-01',
    evidence: [
      {
        id: 'ev-011',
        filename: 'BCP_Draft_v1.3.pdf',
        uploadedAt: '2024-03-10T11:30:00Z',
        uploadedBy: 'Lisa Martinez',
        fileSize: '2.8 MB'
      }
    ],
    notes: 'BCP drafted and under review. Awaiting executive approval.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-10T11:30:00Z',
    severity: 'critical'
  },
  {
    id: 'ctrl-011',
    title: 'Disaster recovery plan with RTO/RPO targets',
    description: 'DR plan with defined Recovery Time Objective (RTO) and Recovery Point Objective (RPO) for each critical system.',
    article: 'Art. 21(2)(c)',
    articleArea: 'Business Continuity',
    category: 'Technical',
    status: 'Implemented',
    owner: 'David Kim',
    dueDate: null,
    evidence: [
      {
        id: 'ev-012',
        filename: 'DR_Plan_2024.pdf',
        uploadedAt: '2024-02-20T14:00:00Z',
        uploadedBy: 'David Kim',
        fileSize: '3.5 MB'
      },
      {
        id: 'ev-013',
        filename: 'RTO_RPO_Matrix.xlsx',
        uploadedAt: '2024-02-20T14:15:00Z',
        uploadedBy: 'David Kim',
        fileSize: '125 KB'
      }
    ],
    notes: 'Core systems: RTO 4h, RPO 1h. Secondary systems: RTO 24h, RPO 8h.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-02-20T14:15:00Z',
    severity: 'critical'
  },
  {
    id: 'ctrl-012',
    title: 'DR plan tested (last 12 months)',
    description: 'Regular testing of disaster recovery plan through simulations or full failover tests.',
    article: 'Art. 21(2)(c)',
    articleArea: 'Business Continuity',
    category: 'Technical',
    status: 'Not Started',
    owner: 'David Kim',
    dueDate: '2024-06-30',
    evidence: [],
    notes: 'Last test was 15 months ago. Urgent: schedule DR test by end of Q2.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-25T10:00:00Z',
    severity: 'critical'
  },
  {
    id: 'ctrl-013',
    title: 'Critical system backups tested regularly',
    description: 'Regular restore tests to verify backup integrity and restoration procedures. Quarterly testing required.',
    article: 'Art. 21(2)(c)',
    articleArea: 'Business Continuity',
    category: 'Technical',
    status: 'Implemented',
    owner: 'David Kim',
    dueDate: null,
    evidence: [
      {
        id: 'ev-014',
        filename: 'Q1_2024_Backup_Test_Results.pdf',
        uploadedAt: '2024-03-30T16:00:00Z',
        uploadedBy: 'David Kim',
        fileSize: '890 KB'
      }
    ],
    notes: 'Quarterly tests passed. Last test: March 2024. All critical systems verified.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-30T16:00:00Z',
    severity: 'high'
  },

  // SUPPLY CHAIN (Art. 21(2)(d))
  {
    id: 'ctrl-014',
    title: 'Supplier cybersecurity assessment process',
    description: 'Process to assess cybersecurity practices of critical suppliers, including security questionnaires and certification requirements.',
    article: 'Art. 21(2)(d)',
    articleArea: 'Supply Chain Security',
    category: 'Organizational',
    status: 'Partial',
    owner: 'Amanda Foster',
    dueDate: '2024-08-01',
    evidence: [
      {
        id: 'ev-015',
        filename: 'Supplier_Security_Assessment_Template.xlsx',
        uploadedAt: '2024-03-01T09:00:00Z',
        uploadedBy: 'Amanda Foster',
        fileSize: '340 KB'
      }
    ],
    notes: 'Template created. 5 of 12 critical suppliers assessed so far.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-01T09:00:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-015',
    title: 'Security requirements in supplier contracts',
    description: 'Contractual security obligations including breach notification, right to audit, data protection, and security certifications.',
    article: 'Art. 21(2)(d)',
    articleArea: 'Supply Chain Security',
    category: 'Organizational',
    status: 'Planned',
    owner: 'Amanda Foster',
    dueDate: '2024-09-01',
    evidence: [],
    notes: 'Legal team drafting security clauses. Will apply to all new contracts and renewals.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-15T14:30:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-016',
    title: 'Third-party access management process',
    description: 'Formal approval, MFA enforcement, and monitoring for third-party system access. Quarterly access reviews required.',
    article: 'Art. 21(2)(d)',
    articleArea: 'Supply Chain Security',
    category: 'Technical',
    status: 'Implemented',
    owner: 'David Kim',
    dueDate: null,
    evidence: [
      {
        id: 'ev-016',
        filename: 'Third_Party_Access_Policy.pdf',
        uploadedAt: '2024-01-25T10:00:00Z',
        uploadedBy: 'David Kim',
        fileSize: '680 KB'
      },
      {
        id: 'ev-017',
        filename: 'Q1_2024_Access_Review.xlsx',
        uploadedAt: '2024-03-31T15:00:00Z',
        uploadedBy: 'David Kim',
        fileSize: '145 KB'
      }
    ],
    notes: 'MFA enforced for all third-party access. Last review: March 2024.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-31T15:00:00Z',
    severity: 'high'
  },

  // TECHNICAL CONTROLS (Art. 21(2)(e) + (h))
  {
    id: 'ctrl-017',
    title: 'MFA enabled on all critical systems',
    description: 'Multi-factor authentication enforced on all critical systems, admin accounts, and remote access.',
    article: 'Art. 21(2)(e)',
    articleArea: 'Access Control',
    category: 'Technical',
    status: 'Partial',
    owner: 'Auto-populated from AWS scan',
    dueDate: '2024-05-01',
    evidence: [],
    notes: 'AWS scan detected: MFA not enabled on root account. 3 critical IAM users missing MFA.',
    isAutoPopulated: true,
    isPeopleControl: false,
    lastUpdated: '2024-04-01T08:00:00Z',
    severity: 'critical'
  },
  {
    id: 'ctrl-018',
    title: 'Data encryption at rest and in transit',
    description: 'Encryption of sensitive data using approved algorithms (AES-256, TLS 1.3) for data at rest and in transit.',
    article: 'Art. 21(2)(h)',
    articleArea: 'Cryptography',
    category: 'Technical',
    status: 'Partial',
    owner: 'Auto-populated from AWS scan',
    dueDate: '2024-04-15',
    evidence: [],
    notes: 'AWS scan detected: 2 S3 buckets without encryption. RDS instances encrypted.',
    isAutoPopulated: true,
    isPeopleControl: false,
    lastUpdated: '2024-04-01T08:00:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-019',
    title: 'Network security monitoring in place',
    description: 'Active monitoring of network traffic, intrusion detection, and security event logging.',
    article: 'Art. 21(2)(e)',
    articleArea: 'Monitoring',
    category: 'Technical',
    status: 'Implemented',
    owner: 'Auto-populated from AWS scan',
    dueDate: null,
    evidence: [],
    notes: 'AWS scan verified: CloudTrail enabled, VPC Flow Logs active, GuardDuty monitoring.',
    isAutoPopulated: true,
    isPeopleControl: false,
    lastUpdated: '2024-04-01T08:00:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-020',
    title: 'Vulnerability management process',
    description: 'Regular vulnerability scanning, patch management, and remediation tracking for all systems.',
    article: 'Art. 21(2)(e)',
    articleArea: 'Security Operations',
    category: 'Technical',
    status: 'Implemented',
    owner: 'James Park',
    dueDate: null,
    evidence: [
      {
        id: 'ev-018',
        filename: 'Vulnerability_Management_Policy.pdf',
        uploadedAt: '2024-02-15T11:00:00Z',
        uploadedBy: 'James Park',
        fileSize: '1.1 MB'
      },
      {
        id: 'ev-019',
        filename: 'March_2024_Vuln_Scan_Report.pdf',
        uploadedAt: '2024-03-31T17:00:00Z',
        uploadedBy: 'James Park',
        fileSize: '2.3 MB'
      }
    ],
    notes: 'Monthly scans. SLA: Critical 24h, High 7d, Medium 30d. 98% compliance.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-31T17:00:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-021',
    title: 'Cryptography and key management policy',
    description: 'Policy governing encryption algorithms, key lifecycle, and secure key storage using KMS or HSM.',
    article: 'Art. 21(2)(h)',
    articleArea: 'Cryptography',
    category: 'Technical',
    status: 'Implemented',
    owner: 'David Kim',
    dueDate: null,
    evidence: [
      {
        id: 'ev-020',
        filename: 'Cryptography_Policy_v2.0.pdf',
        uploadedAt: '2024-01-30T10:00:00Z',
        uploadedBy: 'David Kim',
        fileSize: '980 KB'
      }
    ],
    notes: 'Policy approved. AWS KMS used for key management. Automatic rotation enabled.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-01-30T10:00:00Z',
    severity: 'medium'
  },
  {
    id: 'ctrl-022',
    title: 'Patch management process',
    description: 'Systematic process for applying security patches to operating systems, applications, and firmware.',
    article: 'Art. 21(2)(e)',
    articleArea: 'Security Operations',
    category: 'Technical',
    status: 'Implemented',
    owner: 'David Kim',
    dueDate: null,
    evidence: [
      {
        id: 'ev-021',
        filename: 'Patch_Management_Procedure.pdf',
        uploadedAt: '2024-02-01T09:00:00Z',
        uploadedBy: 'David Kim',
        fileSize: '1.5 MB'
      },
      {
        id: 'ev-022',
        filename: 'March_2024_Patch_Compliance_Report.xlsx',
        uploadedAt: '2024-03-31T18:00:00Z',
        uploadedBy: 'David Kim',
        fileSize: '220 KB'
      }
    ],
    notes: 'Automated patching for non-critical. Critical patches tested within 7 days.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-31T18:00:00Z',
    severity: 'high'
  },

  // PEOPLE & AWARENESS (Art. 21(2)(g) + (i))
  {
    id: 'ctrl-023',
    title: 'Security awareness training completed by all staff',
    description: 'Annual mandatory security awareness training covering phishing, password security, data handling, and incident reporting.',
    article: 'Art. 21(2)(g)',
    articleArea: 'Training & Awareness',
    category: 'People',
    status: 'Partial',
    owner: 'Sarah Chen (CISO)',
    dueDate: '2024-06-30',
    evidence: [],
    notes: '142 of 180 employees completed (79%). Campaign active. Deadline: June 30.',
    isAutoPopulated: false,
    isPeopleControl: true,
    lastUpdated: '2024-04-01T09:00:00Z',
    severity: 'critical'
  },
  {
    id: 'ctrl-024',
    title: 'Information security policy acknowledged by all staff',
    description: 'All employees must read and formally acknowledge the information security policy annually.',
    article: 'Art. 21(2)(g)',
    articleArea: 'Training & Awareness',
    category: 'People',
    status: 'Partial',
    owner: 'Sarah Chen (CISO)',
    dueDate: '2024-05-31',
    evidence: [],
    notes: '155 of 180 employees acknowledged (86%). Reminders sent to remaining 25.',
    isAutoPopulated: false,
    isPeopleControl: true,
    lastUpdated: '2024-04-01T09:15:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-025',
    title: 'Secure onboarding process for new employees',
    description: 'Security onboarding checklist including background checks, NDA signing, security training, and access provisioning.',
    article: 'Art. 21(2)(i)',
    articleArea: 'HR Security',
    category: 'People',
    status: 'Implemented',
    owner: 'HR + IT Security',
    dueDate: null,
    evidence: [
      {
        id: 'ev-023',
        filename: 'Security_Onboarding_Checklist.pdf',
        uploadedAt: '2024-01-10T10:00:00Z',
        uploadedBy: 'Sarah Chen',
        fileSize: '540 KB'
      }
    ],
    notes: 'Standardized process in place. Security training mandatory within first week.',
    isAutoPopulated: false,
    isPeopleControl: true,
    lastUpdated: '2024-01-10T10:00:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-026',
    title: 'Same-day access revocation on employee departure',
    description: 'Process ensuring all system access is disabled within 1 hour of employee departure. Equipment collection and exit interview.',
    article: 'Art. 21(2)(i)',
    articleArea: 'HR Security',
    category: 'People',
    status: 'Implemented',
    owner: 'HR + IT Security',
    dueDate: null,
    evidence: [
      {
        id: 'ev-024',
        filename: 'Offboarding_Procedure.pdf',
        uploadedAt: '2024-01-10T11:00:00Z',
        uploadedBy: 'Sarah Chen',
        fileSize: '620 KB'
      }
    ],
    notes: 'Automated workflow. HR notification triggers immediate account deactivation.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-01-10T11:00:00Z',
    severity: 'critical'
  },
  {
    id: 'ctrl-027',
    title: 'Privileged access background checks conducted',
    description: 'Background verification for roles with admin rights or access to sensitive data (system admins, database admins, finance, HR).',
    article: 'Art. 21(2)(i)',
    articleArea: 'HR Security',
    category: 'People',
    status: 'Implemented',
    owner: 'HR',
    dueDate: null,
    evidence: [
      {
        id: 'ev-025',
        filename: 'Background_Check_Policy.pdf',
        uploadedAt: '2024-01-05T09:00:00Z',
        uploadedBy: 'HR Department',
        fileSize: '380 KB'
      }
    ],
    notes: 'Background checks required for 22 privileged roles. 100% compliance.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-01-05T09:00:00Z',
    severity: 'high'
  },
  {
    id: 'ctrl-028',
    title: 'Annual access review completed',
    description: 'Quarterly access certification where managers review and certify their team members\' access rights.',
    article: 'Art. 21(2)(i)',
    articleArea: 'HR Security',
    category: 'People',
    status: 'Implemented',
    owner: 'David Kim',
    dueDate: null,
    evidence: [
      {
        id: 'ev-026',
        filename: 'Q1_2024_Access_Certification.xlsx',
        uploadedAt: '2024-03-31T16:00:00Z',
        uploadedBy: 'David Kim',
        fileSize: '285 KB'
      }
    ],
    notes: 'Q1 2024 review completed. 8 orphaned accounts removed, 15 access rights adjusted.',
    isAutoPopulated: false,
    isPeopleControl: false,
    lastUpdated: '2024-03-31T16:00:00Z',
    severity: 'high'
  }
]

export const mockCampaigns: EmployeeCampaign[] = [
  {
    id: 'camp-001',
    controlId: 'ctrl-023',
    controlName: 'Security awareness training completed by all staff',
    taskType: 'quiz',
    deadline: '2024-06-30',
    createdAt: '2024-03-01T09:00:00Z',
    tasks: [
      {
        id: 'task-001',
        controlId: 'ctrl-023',
        campaignId: 'camp-001',
        employeeName: 'Alice Johnson',
        employeeEmail: 'alice.johnson@company.com',
        department: 'Engineering',
        taskType: 'quiz',
        status: 'completed',
        sentDate: '2024-03-01T09:00:00Z',
        completedDate: '2024-03-02T14:30:00Z',
        deadline: '2024-06-30',
        score: 5
      },
      {
        id: 'task-002',
        controlId: 'ctrl-023',
        campaignId: 'camp-001',
        employeeName: 'Bob Martinez',
        employeeEmail: 'bob.martinez@company.com',
        department: 'Sales',
        taskType: 'quiz',
        status: 'completed',
        sentDate: '2024-03-01T09:00:00Z',
        completedDate: '2024-03-05T10:15:00Z',
        deadline: '2024-06-30',
        score: 4
      },
      {
        id: 'task-003',
        controlId: 'ctrl-023',
        campaignId: 'camp-001',
        employeeName: 'Carol White',
        employeeEmail: 'carol.white@company.com',
        department: 'Marketing',
        taskType: 'quiz',
        status: 'pending',
        sentDate: '2024-03-01T09:00:00Z',
        completedDate: null,
        deadline: '2024-06-30'
      },
      {
        id: 'task-004',
        controlId: 'ctrl-023',
        campaignId: 'camp-001',
        employeeName: 'David Lee',
        employeeEmail: 'david.lee@company.com',
        department: 'Engineering',
        taskType: 'quiz',
        status: 'completed',
        sentDate: '2024-03-01T09:00:00Z',
        completedDate: '2024-03-03T16:45:00Z',
        deadline: '2024-06-30',
        score: 5
      },
      {
        id: 'task-005',
        controlId: 'ctrl-023',
        campaignId: 'camp-001',
        employeeName: 'Emma Davis',
        employeeEmail: 'emma.davis@company.com',
        department: 'Finance',
        taskType: 'quiz',
        status: 'pending',
        sentDate: '2024-03-01T09:00:00Z',
        completedDate: null,
        deadline: '2024-06-30'
      }
    ]
  },
  {
    id: 'camp-002',
    controlId: 'ctrl-024',
    controlName: 'Information security policy acknowledged by all staff',
    taskType: 'acknowledge',
    deadline: '2024-05-31',
    createdAt: '2024-02-15T10:00:00Z',
    policyContent: 'All employees must comply with the Information Security Policy which covers data protection, acceptable use, password requirements, incident reporting, and access control procedures.',
    tasks: [
      {
        id: 'task-006',
        controlId: 'ctrl-024',
        campaignId: 'camp-002',
        employeeName: 'Frank Wilson',
        employeeEmail: 'frank.wilson@company.com',
        department: 'Operations',
        taskType: 'acknowledge',
        status: 'completed',
        sentDate: '2024-02-15T10:00:00Z',
        completedDate: '2024-02-16T09:20:00Z',
        deadline: '2024-05-31'
      },
      {
        id: 'task-007',
        controlId: 'ctrl-024',
        campaignId: 'camp-002',
        employeeName: 'Grace Taylor',
        employeeEmail: 'grace.taylor@company.com',
        department: 'HR',
        taskType: 'acknowledge',
        status: 'completed',
        sentDate: '2024-02-15T10:00:00Z',
        completedDate: '2024-02-15T14:30:00Z',
        deadline: '2024-05-31'
      },
      {
        id: 'task-008',
        controlId: 'ctrl-024',
        campaignId: 'camp-002',
        employeeName: 'Henry Brown',
        employeeEmail: 'henry.brown@company.com',
        department: 'Engineering',
        taskType: 'acknowledge',
        status: 'overdue',
        sentDate: '2024-02-15T10:00:00Z',
        completedDate: null,
        deadline: '2024-05-31'
      },
      {
        id: 'task-009',
        controlId: 'ctrl-024',
        campaignId: 'camp-002',
        employeeName: 'Iris Chen',
        employeeEmail: 'iris.chen@company.com',
        department: 'Marketing',
        taskType: 'acknowledge',
        status: 'completed',
        sentDate: '2024-02-15T10:00:00Z',
        completedDate: '2024-02-17T11:00:00Z',
        deadline: '2024-05-31'
      }
    ]
  }
]

export const quizQuestions: QuizQuestion[] = [
  {
    id: 'q1',
    question: 'What should you do if you receive a suspicious email?',
    options: [
      'Forward it to colleagues to warn them',
      'Delete it and report to IT security',
      'Open the attachment to check what it is',
      'Reply asking who sent it'
    ],
    correctAnswer: 1,
    explanation: 'Always delete suspicious emails and report them to your IT security team immediately.'
  },
  {
    id: 'q2',
    question: 'How often should you update your work passwords?',
    options: [
      'Never, they\'re fine as they are',
      'Every 3 months or when prompted by security policy',
      'Only when you forget them',
      'Once a year'
    ],
    correctAnswer: 1,
    explanation: 'Regular password updates (typically every 3 months) help maintain security.'
  },
  {
    id: 'q3',
    question: 'What is phishing?',
    options: [
      'A type of network attack using malware',
      'An attempt to trick you into revealing credentials or sensitive information',
      'A software vulnerability in email systems',
      'A type of firewall technology'
    ],
    correctAnswer: 1,
    explanation: 'Phishing is a social engineering attack designed to steal your credentials or sensitive data.'
  },
  {
    id: 'q4',
    question: 'What should you do before leaving your workstation?',
    options: [
      'Leave it on so colleagues can use it',
      'Lock your screen (Windows+L or Ctrl+Cmd+Q)',
      'Shut it down completely',
      'Nothing, it\'s in a secure office'
    ],
    correctAnswer: 1,
    explanation: 'Always lock your screen when stepping away to prevent unauthorized access.'
  },
  {
    id: 'q5',
    question: 'Who should you contact if you suspect a security incident?',
    options: [
      'Handle it yourself, don\'t bother anyone',
      'Your manager only',
      'IT security team immediately',
      'Post about it on company chat to warn others'
    ],
    correctAnswer: 2,
    explanation: 'Always report security incidents to the IT security team immediately so they can respond appropriately.'
  }
]
