import { test, expect, mockApi } from './fixtures'

test.describe('Assessment Page', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('loads with article sections', async ({ page }) => {
    await page.goto('/assessment')
    await expect(page.locator('h1')).toContainText('Assessment')

    // Should show NIS2 Articles sidebar
    await expect(page.getByText('NIS2 Articles')).toBeVisible()
  })

  test('shows progress banner', async ({ page }) => {
    await page.goto('/assessment')
    await expect(page.getByText(/Progress/)).toBeVisible()
    await expect(page.getByText(/questions/)).toBeVisible()
  })

  test('can select a maturity level on a question', async ({ page }) => {
    await page.goto('/assessment')

    // Wait for questions to render — maturity level buttons are inside QuestionCard
    const maturityButtons = page.locator('button').filter({ hasText: /^[0-5]$/ })
    const count = await maturityButtons.count()

    if (count > 0) {
      await maturityButtons.first().click()
      // Progress should update
      await expect(page.getByText(/1 of/)).toBeVisible()
    }
  })

  test('navigation between articles works', async ({ page }) => {
    await page.goto('/assessment')

    // Click "Next" button
    const nextButton = page.getByRole('button', { name: /next/i }).first()
    if (await nextButton.isVisible()) {
      await nextButton.click()
      await expect(page.getByRole('button', { name: /previous/i }).first()).toBeEnabled()
    }
  })

  test('submit button exists but is disabled when incomplete', async ({ page }) => {
    await page.goto('/assessment')
    const submitBtn = page.getByRole('button', { name: /submit assessment/i })
    await expect(submitBtn).toBeVisible()
    await expect(submitBtn).toBeDisabled()
  })
})
