import { test as setup, expect } from '@playwright/test'

setup('authenticate', async ({ page }) => {
  // Mock the auth/me endpoint so AuthProvider doesn't clear our localStorage
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

  // Mock accounts endpoint called after auth/me
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

  // Mock any other API calls that fire on app init
  await page.route('**/api/v1/**', route => {
    // Catch-all for remaining API endpoints
    if (!route.request().url().includes('/auth/me') && !route.request().url().includes('/accounts')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: '{}',
      })
    }
    return route.fallback()
  })

  // Navigate to the app and wait for it to settle
  await page.goto('/login')
  await expect(page.locator('h1')).toContainText('Sign in to Konforme')

  // Inject auth localStorage values
  await page.evaluate(() => {
    localStorage.setItem('konforme_account_id', 'test-account-id')
    localStorage.setItem('konforme_account_name', 'Test Corp')
    localStorage.setItem('konforme_email', 'test@konforme.io')
    localStorage.setItem('konforme_aws_accounts', '[]')
  })

  // Verify localStorage was set
  const accountId = await page.evaluate(() => localStorage.getItem('konforme_account_id'))
  expect(accountId).toBe('test-account-id')

  // Save storage state for reuse across tests
  await page.context().storageState({ path: 'e2e/.auth/state.json' })
})
