import { test, expect } from '@playwright/test';

/**
 * E2E tests for authentication scenarios
 */

test.describe('Authentication E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should complete registration and login flow', async ({ page }) => {
    // Navigate to registration
    await page.click('a:has-text("Register")');

    // Fill registration form
    await page.fill('input[placeholder*="Username"]', 'e2e_testuser');
    await page.fill('input[placeholder*="Email"]', 'e2e@example.com');
    await page.fill('input[placeholder*="Password"]', 'E2EPassword123!');
    await page.fill(
      'input[placeholder*="Confirm"]',
      'E2EPassword123!'
    );

    // Submit registration
    await page.click('button:has-text("Register")');

    // Wait for success message or redirect
    await expect(page).toHaveURL(/\/(login|home)/);

    // Login
    if (page.url().includes('login') === false) {
      await page.click('a:has-text("Login")');
    }

    await page.fill('input[placeholder*="Username"]', 'e2e_testuser');
    await page.fill('input[placeholder*="Password"]', 'E2EPassword123!');
    await page.click('button:has-text("Login")');

    // Verify successful login
    await expect(page).toHaveURL(/\/(dashboard|home)/);
  });

  test('should handle login with invalid credentials', async ({ page }) => {
    await page.click('a:has-text("Login")');

    await page.fill('input[placeholder*="Username"]', 'testuser');
    await page.fill('input[placeholder*="Password"]', 'wrongpassword');
    await page.click('button:has-text("Login")');

    // Expect error message
    const errorMessage = await page.textContent('.error, .alert-danger');
    expect(errorMessage).toBeTruthy();
  });

  test('should persist session after page reload', async ({ page }) => {
    // Login first
    await page.click('a:has-text("Login")');
    await page.fill('input[placeholder*="Username"]', 'testuser');
    await page.fill('input[placeholder*="Password"]', 'TestPassword123!');
    await page.click('button:has-text("Login")');

    // Wait for dashboard
    await expect(page).toHaveURL(/\/(dashboard|home)/);

    // Reload page
    await page.reload();

    // Should still be logged in
    await expect(page).toHaveURL(/\/(dashboard|home)/);
  });
});

test.describe('Image Upload E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login before image upload tests
    await page.goto('/login');
    await page.fill('input[placeholder*="Username"]', 'testuser');
    await page.fill('input[placeholder*="Password"]', 'TestPassword123!');
    await page.click('button:has-text("Login")');
    await expect(page).toHaveURL(/\/(dashboard|workzone)/);
  });

  test('should upload image successfully', async ({ page }) => {
    // Navigate to upload page
    await page.click('a:has-text("Upload")');

    // Upload file
    const fileInput = await page.$('input[type="file"]');
    if (fileInput) {
      await fileInput.uploadFile(__dirname + '/fixtures/test-image.png');
    }

    // Click upload button
    await page.click('button:has-text("Upload")');

    // Wait for success notification
    await expect(page.locator('.success, .alert-success')).toBeVisible();
  });

  test('should reject invalid file types', async ({ page }) => {
    await page.click('a:has-text("Upload")');

    const fileInput = await page.$('input[type="file"]');
    if (fileInput) {
      await fileInput.uploadFile(__dirname + '/fixtures/test-file.txt');
    }

    // Should show error for invalid file type
    const errorMessage = await page.textContent('.error, .alert-danger');
    expect(errorMessage).toContain(/type|format|invalid/i);
  });
});

test.describe('Admin Dashboard E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('input[placeholder*="Username"]', 'admin');
    await page.fill('input[placeholder*="Password"]', 'AdminPassword123!');
    await page.click('button:has-text("Login")');
    await expect(page).toHaveURL(/\/(dashboard|admin)/);
  });

  test('should display user statistics on admin dashboard', async ({
    page,
  }) => {
    // Navigate to admin panel
    await page.click('a:has-text("Admin") >> first');

    // Wait for stats to load
    await expect(page.locator('[data-testid="stats"]')).toBeVisible();

    // Verify stats are displayed
    const userCount = await page.textContent('[data-testid="user-count"]');
    expect(userCount).toBeTruthy();
  });

  test('should manage users from admin panel', async ({ page }) => {
    await page.click('a:has-text("Admin")');
    await page.click('a:has-text("Users")');

    // Find and update a user
    const userRow = await page.$('tr:has-text("testuser") >> first');
    if (userRow) {
      await userRow.click();

      // Edit user role
      await page.click('button:has-text("Edit")');
      await page.selectOption('select[name="role"]', 'admin');
      await page.click('button:has-text("Save")');

      // Verify success
      await expect(page.locator('.success')).toBeVisible();
    }
  });
});
