import { test, expect, mockApi } from './fixtures'

test.describe('Navigation & Routing', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('unauthenticated user is redirected to /login', async ({ browser }) => {
    // Use a fresh context without stored auth state
    const context = await browser.newContext()
    const page = await context.newPage()
    await page.goto('http://localhost:5180/')
    await expect(page).toHaveURL(/\/login/)
    await context.close()
  })

  test('sidebar links navigate to correct pages', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL('/')

    const sidebarRoutes = [
      { label: 'Controls Library', path: '/controls' },
      { label: 'Assessment', path: '/assessment' },
      { label: 'Remediation', path: '/remediation' },
      { label: 'Technical Scan', path: '/scan' },
      { label: 'People Tasks', path: '/people-tasks' },
      { label: 'Reports', path: '/reports' },
      { label: 'Settings', path: '/settings' },
      { label: 'NIS2 Overview', path: '/' },
    ]

    for (const { label, path } of sidebarRoutes) {
      await page.getByRole('link', { name: label }).click()
      await expect(page).toHaveURL(path === '/' ? /\/$/ : new RegExp(path))
    }
  })

  test('dashboard loads without errors', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('NIS2')
  })

  test('controls page loads', async ({ page }) => {
    await page.goto('/controls')
    await expect(page.locator('h1')).toContainText('Controls Library')
  })

  test('assessment page loads', async ({ page }) => {
    await page.goto('/assessment')
    await expect(page.locator('h1')).toContainText('Assessment')
  })

  test('remediation page loads', async ({ page }) => {
    await page.goto('/remediation')
    await expect(page.locator('h1')).toContainText('Remediation')
  })

  test('people-tasks page loads', async ({ page }) => {
    await page.goto('/people-tasks')
    await expect(page.locator('h1')).toContainText('People Tasks')
  })

  test('reports page loads', async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 10000 })
    const heading = await page.locator('h1').first().textContent()
    expect(heading?.toLowerCase()).toContain('report')
  })

  test('settings page loads', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.locator('h1')).toContainText('Settings')
  })

  test('scan page loads', async ({ page }) => {
    await page.goto('/scan')
    await expect(page.locator('h1')).toContainText('Scan')
  })
})
