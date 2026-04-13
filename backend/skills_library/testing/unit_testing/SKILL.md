---
name: unit_testing
description: Unit testing patterns — AAA, mocks, fixtures, test isolation
---

# Unit Testing

Verify the smallest meaningful unit (function, method, class) in isolation.

## AAA Pattern

```python
def test_discount_applies_to_total():
    # Arrange
    cart = Cart(items=[Item(price=100)])
    coupon = Coupon(percent=10)

    # Act
    total = cart.total(coupon)

    # Assert
    assert total == 90
```

One logical assertion per test. Multiple `assert` lines OK if they describe one behavior.

## Test Isolation

- No shared mutable state between tests.
- Fresh fixtures per test; tear down side effects.
- Order-independent — tests must pass in any order, including parallel.
- No network, no real DB, no filesystem (except tmp dirs).

## Fixtures

```python
# pytest
import pytest

@pytest.fixture
def account():
    return Account(balance=100)

def test_withdraw(account):
    account.withdraw(30)
    assert account.balance == 70
```

Prefer **factories / builders** over fixtures when many variants are needed:

```python
def make_user(**overrides):
    return User(**{'name': 'Ana', 'age': 30, **overrides})
```

## Test Doubles (Meszaros)

| Type | Purpose |
|------|---------|
| **Dummy** | Passed but unused (fill args). |
| **Stub** | Returns canned responses. |
| **Fake** | Working impl, unsuitable for prod (in-memory DB). |
| **Spy** | Records calls for later assertion. |
| **Mock** | Pre-programmed with expectations; fails if unmet. |

## Mocking Example

```python
from unittest.mock import Mock

def test_notifies_on_signup():
    notifier = Mock()
    service = SignupService(notifier=notifier)

    service.signup('ana@x.com')

    notifier.send.assert_called_once_with('ana@x.com', 'welcome')
```

Mock at **architectural boundaries** (I/O, external services), not every collaborator.

## Parametrize

```python
@pytest.mark.parametrize("n, expected", [
    (0, 1), (1, 1), (2, 2), (5, 120),
])
def test_factorial(n, expected):
    assert factorial(n) == expected
```

## What to Test

- Happy path.
- Edge cases (empty, null, zero, max, boundary±1).
- Error paths (exceptions raised, messages).
- Invariants (state before/after).

Don't test: framework code, trivial getters, language features.

## Coverage

Coverage is a floor, not a goal. 80%+ line is a reasonable target, but **branch coverage** and **mutation testing** (e.g., `mutmut`, Stryker) reveal assertion quality.

## Anti-patterns

- **Testing implementation details** → brittle, refactor-hostile.
- **Over-mocking** → tests pass, production breaks.
- **Logic in tests** (loops, conditionals) → who tests the test?
- **Snapshot abuse** → accepted without reading.
- **Time / randomness** without injection → flaky.
