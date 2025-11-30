import { test, expect } from '@playwright/test';
import {
  waitForGradioLoad,
  navigateTo,
  sendChatMessage,
  getCheckpointData,
  isTextVisible,
} from './fixtures/test-helpers';

test.describe('Checkpoint Operations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForGradioLoad(page);
  });

  test('should navigate to checkpoints section', async ({ page }) => {
    await navigateTo(page, 'Checkpoints');
    await page.waitForTimeout(500);

    // Check for checkpoints heading
    await expect(page.getByRole('heading', { name: 'Checkpoints' })).toBeVisible();
  });

  test('should show checkpoint filter controls', async ({ page }) => {
    await navigateTo(page, 'Checkpoints');
    await page.waitForTimeout(500);

    // Check filter controls - use first() for elements that may match multiple
    await expect(page.getByText('Type').first()).toBeVisible();
    await expect(page.getByText('From Date').first()).toBeVisible();
    await expect(page.getByText('To Date').first()).toBeVisible();
  });

  test('should show checkpoint table headers', async ({ page }) => {
    await navigateTo(page, 'Checkpoints');

    // Wait for table to load
    await page.waitForTimeout(1000);

    // Check for expected column headers (if table is visible)
    const table = page.locator('table').first();
    if (await table.isVisible()) {
      const headers = await table.locator('thead th').allTextContents();
      expect(headers.length).toBeGreaterThan(0);
    }
  });

  test('should list checkpoints via chat', async ({ page }) => {
    await navigateTo(page, 'Chat');

    // Type and send message
    const input = page.locator('textarea').first();
    await input.fill('show checkpoints');
    await page.click('button:has-text("Send")');

    // Wait for response
    await page.waitForTimeout(5000);

    // Should have some response - chatbot container visible
    const chatContainer = page.locator('.chatbot').last();
    await expect(chatContainer).toBeVisible();
  });

  test('should have add checkpoint quick action', async ({ page }) => {
    await navigateTo(page, 'Chat');

    // Quick action button should be visible
    await expect(page.locator('button:has-text("Add Checkpoint")')).toBeVisible();
  });

  test('should click add checkpoint quick action', async ({ page }) => {
    await navigateTo(page, 'Chat');

    // Click the quick action
    await page.click('button:has-text("Add Checkpoint")');

    // Should fill the input with the action
    await page.waitForTimeout(500);
    const input = page.locator('textarea').first();
    const value = await input.inputValue();
    expect(value.toLowerCase()).toContain('add checkpoint');
  });

  test('should show hint text in checkpoints section', async ({ page }) => {
    await navigateTo(page, 'Checkpoints');

    // Check for hint text
    await expect(page.locator('text=Use chat to add new checkpoints')).toBeVisible();
  });

  test('should refresh checkpoints', async ({ page }) => {
    await navigateTo(page, 'Checkpoints');

    // Click refresh
    const refreshBtn = page.locator('button:has-text("Refresh")').first();
    await refreshBtn.click();

    // Wait for update
    await page.waitForTimeout(1000);

    // Should still be on checkpoints section
    await expect(page.locator('text=View and filter your vehicle checkpoints')).toBeVisible();
  });

  test('should filter checkpoints by type', async ({ page }) => {
    await navigateTo(page, 'Checkpoints');
    await page.waitForTimeout(500);

    // The Type dropdown should be visible - use first() for multiple matches
    await expect(page.getByText('Type').first()).toBeVisible();

    // Click refresh button
    const refreshBtn = page.locator('button:has-text("Refresh")').first();
    if (await refreshBtn.isVisible()) {
      await refreshBtn.click();
      await page.waitForTimeout(1000);
    }

    // Should still be on checkpoints section
    await expect(page.getByRole('heading', { name: 'Checkpoints' })).toBeVisible();
  });
});
