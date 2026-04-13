---
name: playwright
description: Playwright E2E testing — page object model, selectors, assertions
---

# Playwright

Cross-browser E2E testing (Chromium, Firefox, WebKit) with auto-waiting.

## Install & Init

```bash
npm init playwright@latest
npx playwright test
npx playwright codegen <url>   # record flows
npx playwright show-report
```

## Selector Priority (user-facing first)

1. `page.getByRole('button', { name: 'Submit' })`
2. `page.getByLabel('Email')`
3. `page.getByPlaceholder('Search…')`
4. `page.getByText('Welcome')`
5. `page.getByTestId('checkout-cta')` — for ambiguous cases
6. CSS / XPath — last resort, brittle.

Avoid selectors based on styling classes or DOM structure.

## Basic Test

```ts
import { test, expect } from '@playwright/test';

test('user can log in', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('secret');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

## Auto-waiting & Web-First Assertions

`expect(locator).toBeVisible()` retries until timeout — no `sleep`. Never use `page.waitForTimeout` in real tests.

Common assertions:
- `toBeVisible / toBeHidden / toBeEnabled`
- `toHaveText / toContainText / toHaveValue`
- `toHaveURL / toHaveTitle`
- `toHaveCount(n)`

## Page Object Model (POM)

```ts
// pages/LoginPage.ts
export class LoginPage {
  constructor(private page: Page) {}
  goto = () => this.page.goto('/login');
  email = () => this.page.getByLabel('Email');
  password = () => this.page.getByLabel('Password');
  submit = () => this.page.getByRole('button', { name: 'Sign in' });

  async login(email: string, pw: string) {
    await this.email().fill(email);
    await this.password().fill(pw);
    await this.submit().click();
  }
}
```

Use in tests:

```ts
test('login', async ({ page }) => {
  const login = new LoginPage(page);
  await login.goto();
  await login.login('u@x.com', 'pw');
  await expect(page).toHaveURL('/dashboard');
});
```

## Fixtures & Auth Reuse

```ts
// global-setup saves storageState after one login
// playwright.config.ts → use: { storageState: 'auth.json' }
```

Cuts login from every test; keep one "auth" spec for the login flow itself.

## Network & Mocking

```ts
await page.route('**/api/users', r =>
  r.fulfill({ json: [{ id: 1, name: 'Ana' }] })
);
```

## Debugging

- `npx playwright test --debug` (Inspector).
- `--ui` for time-travel UI mode.
- Traces: `use: { trace: 'on-first-retry' }` → `npx playwright show-trace`.
- Screenshots + video on failure via config.

## Anti-patterns

- `waitForTimeout(ms)` — flaky; use web-first assertions.
- CSS selectors tied to styling (`.btn-primary.mt-4`).
- Sharing state between tests — use fresh context.
- Asserting on implementation details (internal DOM structure).
