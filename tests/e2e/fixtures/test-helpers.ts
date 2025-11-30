import { Page, expect } from '@playwright/test';

/**
 * Test helpers for Car Log Gradio UI.
 *
 * Gradio uses dynamic element IDs, so we use text selectors and roles.
 */

/**
 * Wait for Gradio app to be fully loaded.
 */
export async function waitForGradioLoad(page: Page) {
  // Wait for the main title to appear
  await page.waitForSelector('text=Car Log - Slovak Mileage Tracker', { timeout: 30000 });
  // Wait for navigation buttons
  await page.waitForSelector('button:has-text("Dashboard")', { timeout: 10000 });
}

/**
 * Navigate to a section using sidebar buttons.
 */
export async function navigateTo(page: Page, section: 'Dashboard' | 'Checkpoints' | 'Trips' | 'Reports' | 'Chat') {
  await page.click(`button:has-text("${section}")`);
  // Wait for section to become visible
  await page.waitForTimeout(500);
}

/**
 * Send a chat message.
 */
export async function sendChatMessage(page: Page, message: string) {
  // Find the message input (textbox without a visible label)
  const input = page.locator('textarea').filter({ hasText: '' }).first();
  await input.fill(message);

  // Click send button
  await page.click('button:has-text("Send")');

  // Wait for response (chatbot updates)
  await page.waitForTimeout(2000);
}

/**
 * Get chat messages from the chatbot.
 */
export async function getChatMessages(page: Page): Promise<string[]> {
  const messages = await page.locator('.chatbot-message, [data-testid="chatbot"] .message').allTextContents();
  return messages;
}

/**
 * Click a quick action button.
 */
export async function clickQuickAction(page: Page, actionText: string) {
  await page.click(`button:has-text("${actionText}")`);
  await page.waitForTimeout(500);
}

/**
 * Get the currently selected vehicle from dropdown.
 */
export async function getSelectedVehicle(page: Page): Promise<string | null> {
  const dropdown = page.locator('label:has-text("Vehicle")').locator('..').locator('input, select').first();
  const value = await dropdown.inputValue().catch(() => null);
  return value;
}

/**
 * Select a vehicle from dropdown.
 */
export async function selectVehicle(page: Page, vehicleName: string) {
  // Click the dropdown to open it
  const dropdown = page.locator('label:has-text("Vehicle")').locator('..');
  await dropdown.click();

  // Select the option
  await page.click(`text=${vehicleName}`);
  await page.waitForTimeout(500);
}

/**
 * Get dashboard stat values.
 */
export async function getDashboardStats(page: Page) {
  await navigateTo(page, 'Dashboard');
  await page.waitForTimeout(1000);

  const stats: Record<string, string> = {};

  // Extract stats from markdown cards
  const statCards = page.locator('text=/^###.*$/');
  const count = await statCards.count();

  for (let i = 0; i < count; i++) {
    const text = await statCards.nth(i).textContent();
    if (text) {
      stats[text.replace('### ', '')] = '';
    }
  }

  return stats;
}

/**
 * Get checkpoint table data.
 */
export async function getCheckpointData(page: Page) {
  await navigateTo(page, 'Checkpoints');
  await page.waitForTimeout(1000);

  // Look for dataframe
  const table = page.locator('table').first();
  if (await table.isVisible()) {
    const rows = await table.locator('tbody tr').all();
    return rows.length;
  }
  return 0;
}

/**
 * Get trip table data.
 */
export async function getTripData(page: Page) {
  await navigateTo(page, 'Trips');
  await page.waitForTimeout(1000);

  const table = page.locator('table').first();
  if (await table.isVisible()) {
    const rows = await table.locator('tbody tr').all();
    return rows.length;
  }
  return 0;
}

/**
 * Wait for chat response containing specific text.
 */
export async function waitForChatResponse(page: Page, containsText: string, timeout = 10000) {
  await page.waitForFunction(
    (text) => {
      const messages = document.querySelectorAll('.chatbot-message, [data-testid="chatbot"] .message');
      return Array.from(messages).some(m => m.textContent?.includes(text));
    },
    containsText,
    { timeout }
  );
}

/**
 * Check if an element with text is visible.
 */
export async function isTextVisible(page: Page, text: string): Promise<boolean> {
  try {
    await page.waitForSelector(`text=${text}`, { timeout: 3000 });
    return true;
  } catch {
    return false;
  }
}
