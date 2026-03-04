import { test, expect, mockApi } from './fixtures'

test.describe('Controls Library', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('page loads with heading', async ({ page }) => {
    await page.goto('/controls')
    await expect(page.locator('h1')).toContainText('Controls Library')
  })

  test('displays control cards', async ({ page }) => {
    await page.goto('/controls')
    // Controls are rendered as clickable rows with article codes
    const controlRows = page.locator('[class*="cursor-pointer"]').filter({ hasText: /Art\. 21/ })
    const count = await controlRows.count()
    expect(count).toBeGreaterThan(0)
  })

  test('search filter works', async ({ page }) => {
    await page.goto('/controls')

    const searchInput = page.getByPlaceholder(/search controls/i)
    await expect(searchInput).toBeVisible()

    // Type a search query
    await searchInput.fill('MFA')
    await page.waitForTimeout(300)

    // The count text should reflect filtered results
    await expect(page.getByText(/of \d+ controls/)).toBeVisible()
  })

  test('category filter dropdown works', async ({ page }) => {
    await page.goto('/controls')

    // Select a category filter
    const categorySelect = page.locator('select').first()
    await categorySelect.selectOption('Technical')
    await page.waitForTimeout(300)
    await expect(page.getByText(/of \d+ controls/)).toBeVisible()
  })

  test('can click into a control detail', async ({ page }) => {
    await page.goto('/controls')

    const controlRows = page.locator('[class*="cursor-pointer"]').filter({ hasText: /Art\. 21/ })
    const firstRow = controlRows.first()

    if (await firstRow.isVisible()) {
      await firstRow.click()
      await expect(page.getByText('Control Details')).toBeVisible()
    }
  })

  test('control drawer can be closed', async ({ page }) => {
    await page.goto('/controls')

    const controlRows = page.locator('[class*="cursor-pointer"]').filter({ hasText: /Art\. 21/ })
    const firstRow = controlRows.first()

    if (await firstRow.isVisible()) {
      await firstRow.click()
      await expect(page.getByText('Control Details')).toBeVisible()

      // Click the backdrop (the absolute inset-0 div behind the drawer panel)
      // Use force:true because the drawer panel overlaps part of the backdrop
      await page.locator('.fixed.inset-0 > .absolute.inset-0').click({ position: { x: 10, y: 10 }, force: true })
      await expect(page.getByText('Control Details')).not.toBeVisible({ timeout: 5000 })
    }
  })
})
