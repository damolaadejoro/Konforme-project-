# Konforme Product Guide

## What Is Konforme?

Konforme is an NIS2 compliance management platform that helps organisations assess, track, and implement the controls required by EU Directive 2022/2555 (NIS2 — Network and Information Security Directive). It measures readiness across three dimensions — Technical, Organisational, and People — and provides a single real-time compliance score that executives, CISOs, and compliance officers can act on immediately.

---

## Who Is It For?

| Role | What They Get |
|---|---|
| **CISO / Security Manager** | Real-time visibility into compliance posture, automated AWS security scanning, remediation roadmaps |
| **Compliance Officer** | Control library mapped to NIS2 Article 21, evidence management, audit-ready PDF reports |
| **Executive / Board Member** | High-level readiness score, critical-gap summaries, risk indicators |
| **Employee** | Assigned compliance tasks — policy acknowledgments and training quizzes — delivered through a standalone mobile-friendly page |

---

## Core Features

### 1. NIS2 Overview Dashboard

The main landing page at `/` shows the organisation's overall NIS2 readiness score, broken down by category (Technical, Organisational, People) and by each Article 21 compliance area. It highlights critical gaps, displays employee compliance statistics, and shows the last-saved timestamp. A one-click button generates a full PDF audit report.

### 2. Controls Library

Located at `/controls`, this page provides a browsable catalogue of 50+ NIS2 Article 21 controls across three categories:

- **Technical** — AWS and infrastructure controls (encryption, access management, monitoring, network security)
- **Organisational** — Policies, governance, risk management, incident response, supply chain security
- **People** — Security awareness training, competency assessments, policy acknowledgments

Each control can be opened in a detail drawer where you can:

- Set status: Not Started, Planned, Partial, or Implemented
- Assign an owner
- Set a due date
- Add notes and attach evidence
- Create employee tasks (quiz or policy acknowledgment)

Controls can be filtered by status, category, and severity, and searched by keyword.

### 3. Technical Scan

The `/scan` page provides an AWS compliance scanner interface. Enter AWS credentials (access key, secret key, region), and the system runs 15 automated NIS2-aligned checks:

- MFA on root account
- CloudTrail multi-region logging
- S3 bucket public access blocks
- EBS volume encryption
- IAM policy hygiene
- VPC security group rules
- RDS encryption at rest
- KMS key management
- GuardDuty threat detection
- VPC flow logs
- And more

Results are displayed in a terminal-style UI with real-time progress, pass/fail outcomes, severity levels, and step-by-step remediation guidance for each finding.

### 4. People Tasks

At `/people-tasks`, administrators can view and manage employee compliance campaigns. Each campaign card shows:

- Task type (Quiz or Policy Acknowledgment)
- Completion rate with a progress bar
- Pending, completed, and overdue counts
- Average quiz scores
- Risk indicators for lagging campaigns

Campaigns are created from the Controls Library when assigning tasks to employees.

### 5. Employee Task Page

Employees receive a direct link to `/task/:taskId` — a standalone, mobile-optimised page with no admin navigation. Two task types are supported:

**Policy Acknowledgment** (4 steps): Introduction, read the policy document, confirm understanding, sign with name entry.

**Training Quiz** (7 steps): Introduction, multiple-choice questions with validation, scoring, results display, and a completion certificate.

Progress is tracked in real time and reported back to the campaign dashboard.

### 6. Reports

The `/reports` page provides a pre-built compliance report that can be downloaded as PDF. It includes:

- Executive summary
- Compliance breakdown charts (bar and pie)
- Critical findings list
- Remediation roadmap with four priority tiers
- Evidence of implemented controls

### 7. Settings

At `/settings`, configure:

- Organisation name and contact email
- Notification preferences
- Target compliance frameworks (NIS2, ISO 27001, SOC 2)
- Scan schedule (daily, weekly, monthly, or manual)

---

## Scoring System

Konforme calculates a weighted compliance score using two factors:

| Factor | Weight |
|---|---|
| **Status** | Not Started = 0, Planned = 0.25, Partial = 0.5, Implemented = 1.0 |
| **Severity** | Critical = 3x, High = 2x, Medium = 1x |

The overall score is a weighted average across all controls. Category scores (Technical, Organisational, People) and per-article scores are computed independently. The score updates in real time as control statuses change.

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend framework** | React 18 with TypeScript |
| **Build tool** | Vite |
| **Routing** | React Router DOM 6 |
| **UI components** | Radix UI primitives, Lucide icons |
| **Styling** | Tailwind CSS with a custom navy/cyan theme, glass-morphism effects |
| **Charts** | Recharts |
| **PDF generation** | jsPDF with jspdf-autotable |
| **Animations** | Framer Motion |
| **Testing** | Vitest, React Testing Library, JSDOM |
| **Data storage** | Browser LocalStorage (demo mode) |
| **Deployment** | Netlify with security headers |

---

## Project Structure

```
konforme-app/
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Router and route definitions
│   │   ├── main.tsx                # Application entry point
│   │   ├── index.css               # Global styles and Tailwind directives
│   │   ├── pages/                  # Page-level components
│   │   │   ├── NIS2Overview.tsx    # Main compliance dashboard
│   │   │   ├── ControlsLibrary.tsx # Control catalogue and detail drawer
│   │   │   ├── Scan.tsx            # AWS compliance scanner
│   │   │   ├── PeopleTasks.tsx     # Employee campaign management
│   │   │   ├── EmployeeTaskPage.tsx# Standalone employee task page
│   │   │   ├── Reports.tsx         # PDF report generation
│   │   │   └── Settings.tsx        # Configuration
│   │   ├── components/
│   │   │   ├── layout/             # Layout, Sidebar, TopNav, Logo
│   │   │   ├── task/               # TaskShell, QuizFlow, PolicyAcknowledgmentFlow
│   │   │   └── ui/                 # Shared UI components
│   │   ├── hooks/                  # Custom hooks (useControls, useScan, etc.)
│   │   ├── types/                  # TypeScript type definitions
│   │   ├── data/                   # Mock data and control definitions
│   │   ├── utils/                  # Utilities (PDF generation)
│   │   └── tests/                  # Test suites
│   ├── public/                     # Static assets
│   ├── dist/                       # Production build output
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
├── backend/                        # Placeholder backend structure
│   └── app/
│       ├── api/
│       ├── rules/
│       └── scanners/
└── netlify.toml                    # Deployment configuration
```

---

## Running the Application

### Prerequisites

- Node.js (v18 or later recommended)
- npm

### Development

```bash
cd frontend
npm install
npm run dev
```

The development server starts at `http://localhost:5173`.

### Production Build

```bash
cd frontend
npm run build
npm run preview
```

### Testing

```bash
cd frontend
npm test                # Run tests in watch mode
npm run test:ui         # Run tests with browser UI
npm run test:coverage   # Run tests with coverage report
```

---

## Data Storage

In the current version, all data is stored in the browser's LocalStorage under these keys:

| Key | Contents |
|---|---|
| `konforme_controls` | Control statuses, owners, due dates, notes, evidence |
| `konforme_campaigns` | Employee task campaigns and individual task records |
| `konforme_last_saved` | Timestamp of the last save operation |

Data persists across page reloads and browser sessions but is local to the device and browser.

---

## Security

### Implemented

- React 18 automatic output encoding (XSS protection)
- Content Security Policy header
- HTTP Strict Transport Security (1 year, including subdomains)
- X-Frame-Options DENY (clickjacking prevention)
- X-Content-Type-Options nosniff
- Permissions Policy blocking geolocation, microphone, camera, and payment APIs
- No hardcoded credentials in source code
- Mock data only — no real personally identifiable information
- Zero known vulnerabilities in production dependencies

### Planned for Production

- OAuth 2.0 / SAML authentication
- Role-Based Access Control
- API rate limiting
- Server-side data encryption at rest
- CSRF protection
- Audit logging
- Security monitoring and alerting

---

## Deployment

Konforme is deployed on Netlify. The `netlify.toml` at the project root configures:

- **Base directory**: `frontend`
- **Build command**: `npm run build`
- **Publish directory**: `frontend/dist`
- **SPA routing**: All paths redirect to `index.html` with a 200 status
- **Security headers**: Applied to all routes

---

## Roadmap Considerations

- **Backend implementation**: The `backend/` directory contains a skeleton structure for API endpoints, compliance rules, and cloud scanners ready for server-side development.
- **Real AWS integration**: The scanner framework is designed to accept real AWS credentials and run live compliance checks once the backend is connected.
- **Multi-framework support**: The settings page already allows selecting ISO 27001 and SOC 2 alongside NIS2, indicating planned expansion of the control library.
- **Authentication and multi-tenancy**: Required before any production deployment to support multiple organisations securely.

---

## Version

**v1.0.0 (Beta)** — MVP with full frontend functionality, mock data, and Netlify deployment.
