import { expect, test } from '@playwright/test';

test('activity hub opens and supports quick flows without console/cors errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', (err) => errors.push(err.message));

  await page.goto('/login');
  await page.getByPlaceholder('Email').fill(process.env.PW_TEST_EMAIL ?? 'admin@example.com');
  await page.getByPlaceholder('Password').fill(process.env.PW_TEST_PASSWORD ?? 'ChangeMe123!');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('**/');

  const fab = page.getByLabel('Log activity');
  await expect(fab).toBeVisible();
  await fab.click();
  await expect(page.getByRole('dialog', { name: 'Log Activity' })).toBeVisible();

  await page.getByRole('button', { name: 'Log Water' }).click();
  await page.getByRole('button', { name: 'Save water' }).click();

  await fab.click();
  await page.getByRole('button', { name: 'Log Meal' }).click();
  await page.getByLabel('Food item id').fill('1');
  await page.getByLabel('Servings').fill('1');
  await page.getByRole('button', { name: 'Save meal' }).click();

  await fab.click();
  await page.getByRole('button', { name: 'Log Upload Report' }).click();
  await expect(page.getByRole('dialog', { name: 'Upload Report' })).toBeVisible();

  expect(errors.filter((error) => /CORS/i.test(error))).toEqual([]);
  expect(errors).toEqual([]);
});
