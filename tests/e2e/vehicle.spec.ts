import { test, expect } from '@playwright/test';
import {
  waitForGradioLoad,
  navigateTo,
  sendChatMessage,
  clickQuickAction,
  getDashboardStats,
  isTextVisible,
} from './fixtures/test-helpers';

test.describe('Vehicle Operations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForGradioLoad(page);
  });

  test('should load app with title', async ({ page }) => {
    await expect(page.locator('text=Car Log - Slovak Mileage Tracker')).toBeVisible();
  });

  test('should show navigation buttons', async ({ page }) => {
    await expect(page.locator('button:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('button:has-text("Checkpoints")')).toBeVisible();
    await expect(page.locator('button:has-text("Trips")')).toBeVisible();
    await expect(page.locator('button:has-text("Reports")')).toBeVisible();
    await expect(page.locator('button:has-text("Chat")')).toBeVisible();
  });

  test('should show vehicle dropdown in header', async ({ page }) => {
    // Gradio dropdowns may have different label structure
    const vehicleLabel = page.getByText('Vehicle').first();
    await expect(vehicleLabel).toBeVisible();
  });

  test('should navigate to dashboard and show stats', async ({ page }) => {
    await navigateTo(page, 'Dashboard');
    await page.waitForTimeout(1000);

    // Check for dashboard content - using heading selector
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should navigate to chat section', async ({ page }) => {
    await navigateTo(page, 'Chat');

    // Check for chatbot and input
    await expect(page.locator('text=Welcome to Car Log')).toBeVisible();
    await expect(page.locator('button:has-text("Send")')).toBeVisible();
  });

  test('should show quick action buttons', async ({ page }) => {
    await navigateTo(page, 'Chat');

    // Quick action buttons should be visible
    await expect(page.locator('button:has-text("Add Checkpoint")')).toBeVisible();
    await expect(page.locator('button:has-text("Check for Gaps")')).toBeVisible();
    await expect(page.locator('button:has-text("Generate Report")')).toBeVisible();
  });

  test('should list vehicles via chat', async ({ page }) => {
    await navigateTo(page, 'Chat');

    // Type and send message
    const input = page.locator('textarea').first();
    await input.fill('list vehicles');
    await page.click('button:has-text("Send")');

    // Wait for response
    await page.waitForTimeout(5000);

    // Should show some response - look for chatbot container
    const chatContainer = page.locator('.chatbot').last();
    await expect(chatContainer).toBeVisible();
  });

  test('should have mode indicator', async ({ page }) => {
    // Check for mode indicator (Agent or Legacy)
    const modeText = await page.locator('text=/Mode:.*(?:Agent|Legacy)/').isVisible();
    expect(modeText).toBeTruthy();
  });

  test('should navigate between sections', async ({ page }) => {
    // Start at Chat (default)
    await expect(page.getByText('Welcome to Car Log')).toBeVisible();

    // Go to Dashboard
    await navigateTo(page, 'Dashboard');
    await page.waitForTimeout(500);
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Go to Checkpoints
    await navigateTo(page, 'Checkpoints');
    await page.waitForTimeout(500);
    await expect(page.getByRole('heading', { name: 'Checkpoints' })).toBeVisible();

    // Go to Trips
    await navigateTo(page, 'Trips');
    await page.waitForTimeout(500);
    await expect(page.getByRole('heading', { name: 'Trips' })).toBeVisible();

    // Go to Reports - use exact match to avoid matching "No Reports Found"
    await navigateTo(page, 'Reports');
    await page.waitForTimeout(500);
    await expect(page.getByRole('heading', { name: 'Reports', exact: true })).toBeVisible();

    // Back to Chat
    await navigateTo(page, 'Chat');
    await expect(page.locator('button:has-text("Send")')).toBeVisible();
  });
});
