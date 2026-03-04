import { test, expect, mockApi } from './fixtures'

test.describe('Reports Page', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('loads with heading', async ({ page }) => {
    // Listen for console errors
    const errors: string[] = []
    page.on('pageerror', err => errors.push(err.message))

    await page.goto('/reports')
    // Wait for the page to fully render
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 10000 })
    const heading = await page.locator('h1').first().textContent()
    expect(heading?.toLowerCase()).toContain('report')
  })

  test('displays report metadata cards', async ({ page }) => {
    await page.goto('/reports')
    await expect(page.getByText('Account', { exact: true })).toBeVisible()
    await expect(page.getByText('Region', { exact: true })).toBeVisible()
    await expect(page.getByText('Scan Date', { exact: true })).toBeVisible()
    await expect(page.getByText('Framework', { exact: true })).toBeVisible()
  })

  test('preview toggle shows and hides report preview', async ({ page }) => {
    await page.goto('/reports')

    // Preview is shown by default
    await expect(page.getByText('Report Preview')).toBeVisible()

    // Click "Hide Preview" button
    const toggleBtn = page.getByRole('button', { name: /hide preview/i })
    await toggleBtn.click()

    // Report preview section should be hidden
    await expect(page.getByText('Report Preview')).not.toBeVisible()

    // Click "Show Preview" to bring it back
    const showBtn = page.getByRole('button', { name: /show preview/i })
    await showBtn.click()
    await expect(page.getByText('Report Preview')).toBeVisible()
  })

  test('download PDF button exists and is clickable', async ({ page }) => {
    await page.goto('/reports')
    const downloadBtn = page.getByRole('button', { name: /download pdf/i })
    await expect(downloadBtn).toBeVisible()
    await expect(downloadBtn).toBeEnabled()
  })

  test('print button exists and is clickable', async ({ page }) => {
    await page.goto('/reports')
    const printBtn = page.getByRole('button', { name: /print/i })
    await expect(printBtn).toBeVisible()
    await expect(printBtn).toBeEnabled()
  })

  test('report summary section loads', async ({ page }) => {
    await page.goto('/reports')
    await expect(page.getByText('Report Summary')).toBeVisible()
  })

  test('findings sections are displayed', async ({ page }) => {
    await page.goto('/reports')
    await expect(page.getByText('Findings to Remediate')).toBeVisible()
    await expect(page.getByText('Passing Controls')).toBeVisible()
  })
})
