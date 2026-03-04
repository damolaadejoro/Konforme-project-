import { test, expect, mockApi } from './fixtures'

test.describe('Remediation Page', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('page loads with heading', async ({ page }) => {
    await page.goto('/remediation')
    await expect(page.locator('h1')).toContainText('Remediation')
  })

  test('shows status filter tabs', async ({ page }) => {
    await page.goto('/remediation')
    await expect(page.getByText(/^All$/)).toBeVisible()
    await expect(page.getByText('Open')).toBeVisible()
  })

  test('create task button is visible', async ({ page }) => {
    await page.goto('/remediation')
    await expect(page.getByRole('button', { name: /create task/i })).toBeVisible()
  })

  test('can open create task form', async ({ page }) => {
    await page.goto('/remediation')
    await page.getByRole('button', { name: /create task/i }).click()
    await expect(page.getByRole('heading', { name: 'Create Remediation Task' })).toBeVisible()
    await expect(page.getByText('Related Question')).toBeVisible()
  })

  test('empty state or task list is shown', async ({ page }) => {
    await page.goto('/remediation')
    const hasEmptyState = await page.getByText(/no tasks yet/i).isVisible().catch(() => false)
    const hasTaskList = await page.locator('[class*="border"]').filter({ hasText: /open|in progress|completed/i }).first().isVisible().catch(() => false)
    expect(hasEmptyState || hasTaskList).toBeTruthy()
  })
})
