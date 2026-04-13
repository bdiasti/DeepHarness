---
name: test_automation
description: Write automated tests using JUnit for Java, Jest for React, and Playwright for E2E. Apply the AAA pattern, Page Object Model, and proper test data management.
---

# Test Automation Skill

You are an expert QA Engineer. When asked to write automated tests, follow the standards, patterns, and examples below.

## Core Principle: The AAA Pattern

Every automated test MUST follow the **Arrange-Act-Assert** pattern:

```
// Arrange — set up test data, mocks, and preconditions
// Act    — execute the action under test (one action only)
// Assert — verify the outcome
```

Rules:
- Each test has exactly ONE act step. If you need two acts, write two tests.
- Keep arrange minimal. Use factories or builders for complex setup.
- Assert on behavior, not implementation. Test what the code does, not how it does it.
- A test that never fails is useless. Verify your test can fail by temporarily breaking the code.

## 1. Unit Tests with JUnit 5 (Java / Spring)

### Basic Structure

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.BeforeEach;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class OrderServiceTest {

    private OrderService orderService;
    private InventoryRepository inventoryRepository;

    @BeforeEach
    void setUp() {
        inventoryRepository = mock(InventoryRepository.class);
        orderService = new OrderService(inventoryRepository);
    }

    @Test
    @DisplayName("should calculate total with 10% discount for premium members")
    void shouldApplyPremiumDiscount() {
        // Arrange
        var customer = CustomerFixture.premiumCustomer();
        var items = List.of(
            new OrderItem("SKU-001", 2, new BigDecimal("50.00"))
        );

        // Act
        BigDecimal total = orderService.calculateTotal(customer, items);

        // Assert
        assertThat(total).isEqualByComparingTo(new BigDecimal("90.00"));
    }

    @Test
    @DisplayName("should throw InsufficientStockException when item is out of stock")
    void shouldRejectOrderWhenOutOfStock() {
        // Arrange
        var items = List.of(new OrderItem("SKU-999", 5, new BigDecimal("10.00")));
        when(inventoryRepository.getAvailableQuantity("SKU-999")).thenReturn(0);

        // Act & Assert
        assertThatThrownBy(() -> orderService.placeOrder(items))
            .isInstanceOf(InsufficientStockException.class)
            .hasMessageContaining("SKU-999");
    }
}
```

### JUnit Conventions

- **Class name**: `<ClassUnderTest>Test` (e.g., `OrderServiceTest`).
- **Method name**: `should<ExpectedBehavior>` or `should<ExpectedBehavior>When<Condition>`.
- **@DisplayName**: Use a human-readable sentence that describes the scenario.
- **Assertions**: Prefer AssertJ (`assertThat`) over JUnit assertions for readability.
- **Mocking**: Use Mockito. Mock dependencies, not the class under test.
- **Parameterized tests**: Use `@ParameterizedTest` with `@CsvSource` or `@MethodSource` for data-driven tests.

```java
@ParameterizedTest
@CsvSource({
    "100.00, 10, 90.00",
    "200.00, 15, 170.00",
    "50.00,  0,  50.00"
})
@DisplayName("should apply discount correctly")
void shouldApplyDiscount(BigDecimal price, int discountPercent, BigDecimal expected) {
    BigDecimal result = PricingUtil.applyDiscount(price, discountPercent);
    assertThat(result).isEqualByComparingTo(expected);
}
```

## 2. Unit and Component Tests with Jest (React / Node.js)

### React Component Test

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProductFilter } from './ProductFilter';

describe('ProductFilter', () => {
  it('should display filtered results when price range is applied', async () => {
    // Arrange
    const onFilter = jest.fn();
    render(<ProductFilter onFilter={onFilter} />);
    const user = userEvent.setup();

    // Act
    await user.type(screen.getByLabelText('Min Price'), '20');
    await user.type(screen.getByLabelText('Max Price'), '100');
    await user.click(screen.getByRole('button', { name: 'Apply Filter' }));

    // Assert
    expect(onFilter).toHaveBeenCalledWith({ minPrice: 20, maxPrice: 100 });
  });

  it('should show validation error when min price exceeds max price', async () => {
    // Arrange
    render(<ProductFilter onFilter={jest.fn()} />);
    const user = userEvent.setup();

    // Act
    await user.type(screen.getByLabelText('Min Price'), '200');
    await user.type(screen.getByLabelText('Max Price'), '50');
    await user.click(screen.getByRole('button', { name: 'Apply Filter' }));

    // Assert
    expect(screen.getByText('Minimum price cannot exceed maximum price')).toBeInTheDocument();
  });
});
```

### Node.js Service Test

```typescript
import { OrderService } from './order.service';
import { mockInventoryRepo } from '../test/mocks';

describe('OrderService', () => {
  let service: OrderService;

  beforeEach(() => {
    service = new OrderService(mockInventoryRepo());
  });

  it('should calculate total with tax for US orders', () => {
    // Arrange
    const items = [{ sku: 'SKU-001', quantity: 2, unitPrice: 50.0 }];

    // Act
    const total = service.calculateTotal(items, 'US', 'CA');

    // Assert
    expect(total).toBeCloseTo(108.63); // $100 + 8.63% CA sales tax
  });
});
```

### Jest Conventions

- **File name**: `<module>.test.ts` or `<Component>.test.tsx`, co-located with the source file.
- **describe/it**: `describe('<Component or Module>')` and `it('should <expected behavior>')`.
- **User interaction**: Always use `@testing-library/user-event` over `fireEvent`.
- **Queries**: Prefer accessible queries: `getByRole`, `getByLabelText`, `getByText`. Avoid `getByTestId` except as a last resort.
- **Async**: Use `waitFor` or `findBy*` for asynchronous UI updates.
- **Mocking**: Use `jest.fn()` for functions, `jest.mock()` for modules. Reset mocks in `beforeEach`.

## 3. E2E Tests with Playwright

### Page Object Model (POM)

Always use the Page Object Model for E2E tests. Every page or major component gets its own class.

**Page Object:**

```typescript
// pages/login.page.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  private readonly page: Page;
  private readonly emailInput: Locator;
  private readonly passwordInput: Locator;
  private readonly signInButton: Locator;
  private readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.signInButton = page.getByRole('button', { name: 'Sign In' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.signInButton.click();
  }

  async getErrorMessage(): Promise<string> {
    return await this.errorMessage.textContent() ?? '';
  }
}
```

**Test using the Page Object:**

```typescript
// tests/auth.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';

test.describe('Authentication', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('should redirect to dashboard after successful login', async ({ page }) => {
    // Act
    await loginPage.login('maria@example.com', 'SecurePass123!');

    // Assert
    const dashboard = new DashboardPage(page);
    await expect(dashboard.welcomeMessage).toHaveText('Hello, Maria');
    expect(page.url()).toContain('/dashboard');
  });

  test('should display error for invalid credentials', async () => {
    // Act
    await loginPage.login('maria@example.com', 'WrongPassword');

    // Assert
    expect(await loginPage.getErrorMessage()).toBe('Invalid email or password');
  });
});
```

### POM Rules

- One file per page or major UI section.
- Locators are defined in the constructor, not in test files.
- Page objects expose **actions** (methods) and **state** (getters), never raw locators to test files.
- Page objects do NOT contain assertions. Assertions belong in the test file.
- Navigation methods return the next page object when the action causes a page transition.

### Playwright Conventions

- **Locator strategy**: Prefer `getByRole`, `getByLabel`, `getByText`, `getByPlaceholder`. Avoid CSS/XPath selectors.
- **Auto-waiting**: Playwright auto-waits for elements. Do NOT add explicit waits or sleeps unless testing time-dependent behavior.
- **Assertions**: Use `expect(locator).toHaveText()`, `expect(locator).toBeVisible()`, etc. These auto-retry.
- **Test isolation**: Each test runs in a fresh browser context. Do not rely on state from previous tests.
- **API setup**: For preconditions (e.g., creating a user), use Playwright's `request` API to call backend endpoints directly instead of navigating through the UI.

```typescript
test.beforeEach(async ({ request }) => {
  // Create test user via API instead of UI
  await request.post('/api/test/users', {
    data: { email: 'maria@example.com', password: 'SecurePass123!', name: 'Maria' }
  });
});
```

## 4. Test Data Management

### Principles

1. **Tests must not depend on shared mutable data.** Each test creates its own data and cleans up after itself.
2. **Use factories or builders** to create test data. Never hardcode large JSON objects inline.
3. **Use unique identifiers** to avoid collisions when tests run in parallel.

### Factory Pattern (TypeScript)

```typescript
// test/factories/user.factory.ts
import { randomUUID } from 'crypto';

interface UserOverrides {
  email?: string;
  name?: string;
  role?: 'admin' | 'member';
}

export function createTestUser(overrides: UserOverrides = {}) {
  const id = randomUUID();
  return {
    id,
    email: overrides.email ?? `test-${id}@example.com`,
    name: overrides.name ?? `Test User ${id.slice(0, 8)}`,
    role: overrides.role ?? 'member',
    createdAt: new Date().toISOString(),
  };
}
```

### Factory Pattern (Java)

```java
// test/fixtures/CustomerFixture.java
public class CustomerFixture {

    public static Customer premiumCustomer() {
        return Customer.builder()
            .id(UUID.randomUUID())
            .name("Test Premium Customer")
            .email("premium-" + UUID.randomUUID() + "@example.com")
            .tier(CustomerTier.PREMIUM)
            .build();
    }

    public static Customer standardCustomer() {
        return Customer.builder()
            .id(UUID.randomUUID())
            .name("Test Standard Customer")
            .email("standard-" + UUID.randomUUID() + "@example.com")
            .tier(CustomerTier.STANDARD)
            .build();
    }
}
```

### Database Cleanup Strategies

| Strategy | When to Use | Example |
|---|---|---|
| **Transaction rollback** | Unit/integration tests with a real database | Wrap each test in a transaction, rollback after |
| **Truncate tables** | Integration test suites | `@AfterEach` truncates all tables |
| **Unique data per test** | E2E tests against shared environments | Use UUID-based emails so tests don't collide |
| **Docker containers** | CI integration tests | Testcontainers spins up a fresh database per suite |

## 5. CI Pipeline Integration

Structure test execution in the CI pipeline following the test pyramid:

```yaml
# Example GitHub Actions workflow
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:unit -- --coverage
      # Fail fast: if unit tests fail, don't run slower suites

  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: testdb
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:integration

  e2e-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

Rules:
- Run faster test suites first. Fail fast.
- Upload test reports and screenshots as artifacts on failure.
- Set timeout limits per suite to prevent hanging pipelines.
- Run E2E tests with retries (`playwright test --retries=1`) to handle flakiness, but investigate and fix flaky tests rather than hiding them behind retries.

## Output Checklist

Before delivering automated tests, verify:

- [ ] Every test follows the AAA pattern (Arrange-Act-Assert)
- [ ] Each test has exactly one act and one logical assertion group
- [ ] Test names describe the expected behavior clearly
- [ ] Page Object Model is used for all E2E tests
- [ ] Page objects do not contain assertions
- [ ] Locators use accessible queries (getByRole, getByLabel), not CSS selectors
- [ ] Test data is created per test using factories, not shared globally
- [ ] Mocks are reset between tests
- [ ] No hardcoded sleep/wait calls (use framework auto-waiting)
- [ ] Tests can run in parallel without interfering with each other
