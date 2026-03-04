import { test, expect } from '@playwright/test'

// Auth spec tests use a fresh context (no stored auth state)
// so we don't use the authenticated fixture

test.describe('Login Page', () => {
  test('renders login form fields', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('h1')).toContainText('Sign in to Konforme')
    await expect(page.getByPlaceholder('you@company.com')).toBeVisible()
    await expect(page.getByPlaceholder('Enter your password')).toBeVisible()
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })

  test('shows validation errors on empty submit', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page.getByText('Email is required')).toBeVisible()
    await expect(page.getByText('Password is required')).toBeVisible()
  })

  test('shows invalid email error', async ({ page }) => {
    await page.goto('/login')
    const emailInput = page.getByPlaceholder('you@company.com')
    await emailInput.fill('notanemail')
    await emailInput.blur()
    await expect(page.getByText('Please enter a valid email address')).toBeVisible()
  })

  test('has link to register page', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('link', { name: /register/i }).click()
    await expect(page).toHaveURL(/\/register/)
  })

  test('has link to reset password page', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('link', { name: /forgot password/i }).click()
    await expect(page).toHaveURL(/\/reset-password/)
  })
})

test.describe('Register Page', () => {
  test('renders registration form fields', async ({ page }) => {
    await page.goto('/register')
    await expect(page.locator('h1')).toContainText('Create your account')
    await expect(page.getByPlaceholder('Your name or company')).toBeVisible()
    await expect(page.getByPlaceholder('you@company.com')).toBeVisible()
    await expect(page.getByPlaceholder('At least 8 characters')).toBeVisible()
    await expect(page.getByPlaceholder('Repeat your password')).toBeVisible()
    await expect(page.getByRole('button', { name: /create account/i })).toBeVisible()
  })

  test('shows validation errors on empty submit', async ({ page }) => {
    await page.goto('/register')
    await page.getByRole('button', { name: /create account/i }).click()
    await expect(page.getByText('Name is required')).toBeVisible()
    await expect(page.getByText('Email is required')).toBeVisible()
    await expect(page.getByText('Password is required')).toBeVisible()
  })

  test('shows password strength indicator', async ({ page }) => {
    await page.goto('/register')
    const pwInput = page.getByPlaceholder('At least 8 characters')
    await pwInput.fill('Abcdefg1!')
    // Should show "Strong password" indicator
    await expect(page.getByText(/strong password/i)).toBeVisible()
  })

  test('has link to login page', async ({ page }) => {
    await page.goto('/register')
    await page.getByRole('link', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/login/)
  })
})

test.describe('Reset Password Page', () => {
  test('renders reset password form', async ({ page }) => {
    await page.goto('/reset-password')
    await expect(page.locator('h1')).toContainText('Reset Password')
    await expect(page.getByPlaceholder('you@company.com')).toBeVisible()
    await expect(page.getByPlaceholder('At least 8 characters')).toBeVisible()
    await expect(page.getByPlaceholder('Repeat your new password')).toBeVisible()
    await expect(page.getByRole('button', { name: /reset password/i })).toBeVisible()
  })

  test('has link back to login', async ({ page }) => {
    await page.goto('/reset-password')
    await page.getByRole('link', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/login/)
  })
})
