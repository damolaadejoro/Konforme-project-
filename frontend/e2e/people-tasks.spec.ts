import { test, expect, mockApi } from './fixtures'

test.describe('People Tasks Page', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('page loads with heading', async ({ page }) => {
    await page.goto('/people-tasks')
    await expect(page.locator('h1')).toContainText('People Tasks')
  })

  test('shows stats bar', async ({ page }) => {
    await page.goto('/people-tasks')
    await expect(page.getByText('Overall Completion')).toBeVisible()
    await expect(page.getByText('Active Campaigns')).toBeVisible()
  })

  test('empty state or campaigns list is shown', async ({ page }) => {
    await page.goto('/people-tasks')
    const hasEmptyState = await page.getByText(/no employee campaigns yet/i).isVisible().catch(() => false)
    const hasCampaigns = await page.getByText(/Active Campaigns/).isVisible().catch(() => false)
    expect(hasEmptyState || hasCampaigns).toBeTruthy()
  })

  test('page renders without crashing', async ({ page }) => {
    await page.goto('/people-tasks')
    // Page should show the heading without errors
    await expect(page.locator('h1')).toContainText('People Tasks')
    // No error overlay
    const errorOverlay = page.locator('vite-error-overlay')
    await expect(errorOverlay).toHaveCount(0)
  })

  test('create campaign button navigates to controls', async ({ page }) => {
    await page.goto('/people-tasks')
    const createBtn = page.getByRole('button', { name: /create campaign/i })
    if (await createBtn.isVisible()) {
      await createBtn.click()
      await expect(page).toHaveURL(/\/controls/)
    }
  })
})
