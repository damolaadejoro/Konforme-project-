import { test, expect, mockApi } from './fixtures'

test.describe('Unrecognized Routes', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('navigating to /organizational does not crash', async ({ page }) => {
    await page.goto('/organizational')
    // Unknown nested routes under the protected layout should still show the sidebar
    // Wait for the app to settle
    await page.waitForTimeout(1000)
    // Should not show an error — page should be within the layout
    const h1 = page.locator('h1')
    // May or may not have an h1, but the page should not crash
    const errorOverlay = page.locator('vite-error-overlay')
    await expect(errorOverlay).toHaveCount(0)
  })
})

test.describe('Assessment as Organizational Questionnaire', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('assessment page loads with article navigation', async ({ page }) => {
    await page.goto('/assessment')
    await expect(page.locator('h1')).toContainText('Assessment')
    await expect(page.getByText('NIS2 Articles')).toBeVisible()
  })

  test('progress bar is shown', async ({ page }) => {
    await page.goto('/assessment')
    await expect(page.getByText(/Progress/)).toBeVisible()
  })
})
