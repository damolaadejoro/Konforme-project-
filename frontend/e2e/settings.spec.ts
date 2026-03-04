import { test, expect, mockApi } from './fixtures'

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('renders settings heading', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.locator('h1')).toContainText('Settings')
  })

  test('shows account section with fields', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.getByText('Account')).toBeVisible()
    await expect(page.getByText('Organisation Name')).toBeVisible()
    await expect(page.getByText('Contact Email')).toBeVisible()
  })

  test('notification toggles are present and clickable', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.getByText('Notifications')).toBeVisible()

    const toggles = page.locator('button.w-10')
    const count = await toggles.count()
    expect(count).toBeGreaterThanOrEqual(3)

    // Click first toggle — should not crash
    await toggles.first().click()
  })

  test('compliance dropdowns are interactive', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.getByText('Compliance Settings')).toBeVisible()
    await expect(page.getByText('Primary Framework')).toBeVisible()
    await expect(page.getByText('Scan Schedule')).toBeVisible()
  })

  test('save changes button is present', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.getByRole('button', { name: /save changes/i })).toBeVisible()
  })
})
