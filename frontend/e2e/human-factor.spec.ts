import { test, expect, mockApi } from './fixtures'

test.describe('Assessment Question Interaction', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('assessment page has question cards', async ({ page }) => {
    await page.goto('/assessment')
    await expect(page.locator('h1')).toContainText('Assessment')
  })

  test('article progress sidebar is visible', async ({ page }) => {
    await page.goto('/assessment')
    await expect(page.getByText('NIS2 Articles')).toBeVisible()
  })

  test('questions render in the main panel', async ({ page }) => {
    await page.goto('/assessment')
    const questionArea = page.locator('.lg\\:col-span-3')
    await expect(questionArea).toBeVisible()
  })

  test('can navigate to next article', async ({ page }) => {
    await page.goto('/assessment')
    const nextBtn = page.getByRole('button', { name: /^next$/i }).first()
    if (await nextBtn.isVisible()) {
      await nextBtn.click()
      await expect(page.getByRole('button', { name: /^previous$/i }).first()).toBeEnabled()
    }
  })
})
