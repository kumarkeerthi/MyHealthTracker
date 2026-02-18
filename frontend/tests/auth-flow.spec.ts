import { expect, test } from '@playwright/test';

test('register redirects to dashboard without runtime errors and sets auth cookie', async ({ page }) => {
  const email = `pw-${Date.now()}@example.com`;

  const errors: string[] = [];
  page.on('pageerror', (err) => errors.push(err.message));

  await page.goto('/register');
  await page.getByPlaceholder('Email').fill(email);
  await page.getByPlaceholder('Password').fill('Password123');
  await page.getByPlaceholder('Confirm password').fill('Password123');
  await page.getByRole('button', { name: 'Create account' }).click();

  await page.waitForURL('**/');
  await expect(page).toHaveURL(/\/$/);
  expect(errors).toEqual([]);

  const cookies = await page.context().cookies();
  expect(cookies.some((cookie) => cookie.name === 'refresh_token')).toBeTruthy();
});
