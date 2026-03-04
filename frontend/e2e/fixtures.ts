import { test as base, expect, Page } from '@playwright/test'

/**
 * Set up API route mocks so the app works without a backend.
 * Must be called BEFORE any page.goto() in each test.
 */
export async function mockApi(page: Page) {
  // Mock GET /auth/me — return the test user
  await page.route('**/api/v1/auth/me', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        account_id: 'test-account-id',
        account_name: 'Test Corp',
        email: 'test@konforme.io',
      }),
    })
  )

  // Mock GET /accounts
  await page.route('**/api/v1/accounts', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'test-account-id',
        name: 'Test Corp',
        is_active: true,
        connected_at: new Date().toISOString(),
        aws_accounts: [],
      }),
    })
  )

  // Mock POST /auth/login
  await page.route('**/api/v1/auth/login', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'fake-token',
        token_type: 'bearer',
        account_id: 'test-account-id',
        account_name: 'Test Corp',
        email: 'test@konforme.io',
      }),
    })
  )

  // Mock POST /auth/register
  await page.route('**/api/v1/auth/register', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'fake-token',
        token_type: 'bearer',
        account_id: 'test-account-id',
        account_name: 'Test Corp',
        email: 'test@konforme.io',
      }),
    })
  )

  // Mock POST /auth/reset-password
  await page.route('**/api/v1/auth/reset-password', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  )

  // Mock POST /auth/refresh
  await page.route('**/api/v1/auth/refresh', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        account_id: 'test-account-id',
        account_name: 'Test Corp',
        email: 'test@konforme.io',
      }),
    })
  )

  // Mock POST /auth/logout
  await page.route('**/api/v1/auth/logout', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  )

  // Mock assessment endpoints
  await page.route('**/api/v1/assessment/**', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ assessment: null, questions: [] }),
    })
  )

  // Mock remediation endpoints
  await page.route('**/api/v1/remediation/**', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: '[]',
    })
  )

  // Mock score endpoint
  await page.route('**/api/v1/score/**', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        overallScore: null,
        technicalScore: null,
        humanFactorScore: null,
        lastTechnicalScan: null,
        lastHumanAssessment: null,
        technicalWeight: 0.5,
        humanWeight: 0.5,
        grade: null,
        articleBreakdown: [],
      }),
    })
  )

  // Mock report endpoint
  await page.route('**/api/v1/report/**', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        accountId: 'test-account-id',
        accountName: 'Test Corp',
        generatedAt: new Date().toISOString(),
        overallScore: null,
        grade: null,
        criticalActions: [],
        warnings: [],
        humanGaps: [],
        passingCount: 0,
        totalChecks: 0,
      }),
    })
  )

  // Mock scan endpoints
  await page.route('**/api/v1/scan/**', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: '{}',
    })
  )
}

export const test = base
export { expect }
