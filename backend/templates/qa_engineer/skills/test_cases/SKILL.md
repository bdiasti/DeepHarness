---
name: test_cases
description: Write structured test cases with ID, title, preconditions, steps, and expected results. Apply boundary value analysis, equivalence partitioning, and decision tables for thorough coverage.
---

# Test Cases Skill

You are an expert QA Engineer. When asked to write test cases, follow the standards and techniques below.

## Test Case Format

Every test case MUST use this structure:

```
**TC-<NNN>:** <Short descriptive title>

- **Priority:** P0 | P1 | P2
- **Type:** Functional | Non-Functional | Regression | Smoke
- **Preconditions:**
  - <condition 1>
  - <condition 2>
- **Test Data:**
  - <specific data values needed>
- **Steps:**
  1. <action>
  2. <action>
  3. <action>
- **Expected Result:**
  - <observable, verifiable outcome>
- **Postconditions:**
  - <state of the system after the test>
```

### Rules

- **ID**: Use a sequential numbering scheme scoped to the feature (e.g., TC-001, TC-002).
- **Title**: Must describe the scenario, not the feature. "Login with valid credentials" not "Login test".
- **Preconditions**: State everything that must be true before step 1. Include user state, data state, and system state.
- **Test Data**: Provide explicit values. Never say "valid email" — say "user@example.com".
- **Steps**: Each step is a single user or system action. Keep steps atomic. Number them.
- **Expected Result**: Describe what the user sees or what the system does. Must be objectively verifiable (no "works correctly").
- **Postconditions**: Describe the system state after the test completes (e.g., "record exists in the database").

### Example

```
**TC-001:** Successful login with valid credentials

- **Priority:** P0
- **Type:** Functional
- **Preconditions:**
  - User account exists with email "maria@example.com" and password "SecurePass123!"
  - User is not currently logged in
  - Account is not locked
- **Test Data:**
  - Email: maria@example.com
  - Password: SecurePass123!
- **Steps:**
  1. Navigate to /login
  2. Enter "maria@example.com" in the email field
  3. Enter "SecurePass123!" in the password field
  4. Click the "Sign In" button
- **Expected Result:**
  - User is redirected to /dashboard
  - Welcome message displays "Hello, Maria"
  - Session cookie is set with HttpOnly and Secure flags
- **Postconditions:**
  - User session is active in the sessions table with a TTL of 24 hours
```

## Test Design Techniques

Use the techniques below to generate test cases systematically. Do not rely on intuition alone.

### 1. Equivalence Partitioning

Divide input data into partitions (classes) where all values in a partition are expected to produce the same behavior. Test one representative value from each partition.

**Process:**
1. Identify each input field and its constraints.
2. Define valid and invalid partitions.
3. Pick one representative value per partition.

**Example: Age field (accepts 18-65)**

| Partition | Range | Representative Value | Expected Behavior |
|---|---|---|---|
| Invalid (below min) | < 18 | 15 | Rejected with error |
| Valid | 18-65 | 30 | Accepted |
| Invalid (above max) | > 65 | 70 | Rejected with error |
| Invalid (non-numeric) | text | "abc" | Rejected with error |
| Invalid (negative) | < 0 | -5 | Rejected with error |
| Invalid (empty) | null/empty | "" | Rejected with error |

This produces 6 test cases instead of testing every possible age.

### 2. Boundary Value Analysis (BVA)

Test values at the exact boundaries of each partition. Bugs cluster at boundaries.

**Process:**
1. Identify the boundaries from equivalence partitions.
2. Test the value ON the boundary, one BELOW, and one ABOVE.

**Example: Age field (accepts 18-65)**

| Boundary | Test Value | Expected Behavior |
|---|---|---|
| Just below minimum | 17 | Rejected |
| At minimum | 18 | Accepted |
| Just above minimum | 19 | Accepted |
| Just below maximum | 64 | Accepted |
| At maximum | 65 | Accepted |
| Just above maximum | 66 | Rejected |

Combined with equivalence partitioning, this gives thorough input coverage.

### 3. Decision Tables

Use decision tables when the behavior depends on combinations of multiple conditions.

**Process:**
1. List all conditions (inputs/states).
2. List all possible actions (outputs/behaviors).
3. Create columns for every relevant combination of conditions.
4. Mark which actions apply to each combination.

**Example: Discount calculation**

Conditions: Is the user a premium member? Is the order above $100? Does the user have a coupon?

| # | Premium Member | Order > $100 | Has Coupon | Discount Applied |
|---|---|---|---|---|
| 1 | Yes | Yes | Yes | 25% |
| 2 | Yes | Yes | No | 15% |
| 3 | Yes | No | Yes | 10% |
| 4 | Yes | No | No | 5% |
| 5 | No | Yes | Yes | 15% |
| 6 | No | Yes | No | 5% |
| 7 | No | No | Yes | 5% |
| 8 | No | No | No | 0% |

Each row becomes a test case. For 3 boolean conditions, there are 2^3 = 8 combinations. If conditions have more than 2 values, the table grows accordingly — in that case, use pairwise testing to reduce combinations.

### 4. State Transition Testing

Use when the system behaves differently depending on its current state.

**Process:**
1. Identify all states.
2. Identify all events/transitions.
3. Draw the state diagram.
4. Write test cases for each valid transition and key invalid transitions.

**Example: Order status**

```
[Created] --pay--> [Paid] --ship--> [Shipped] --deliver--> [Delivered]
    |                 |                                          |
    +---cancel--->[Cancelled]                            [Return Requested]
                      ^                                          |
                      +--------approve return--->[Returned]------+
```

Test cases:
- TC: Created -> Paid (valid: payment succeeds)
- TC: Created -> Cancelled (valid: user cancels before payment)
- TC: Paid -> Shipped (valid: warehouse processes order)
- TC: Shipped -> Delivered (valid: carrier confirms delivery)
- TC: Delivered -> Return Requested (valid: user requests return within 30 days)
- TC: Shipped -> Cancelled (invalid: should be rejected with error)
- TC: Delivered -> Paid (invalid: should be rejected with error)

## Organizing Test Cases

Group test cases into test suites by feature or module:

```
Test Suite: User Authentication
  TC-AUTH-001: Successful login with valid credentials
  TC-AUTH-002: Login rejected with incorrect password
  TC-AUTH-003: Login rejected with non-existent email
  TC-AUTH-004: Account locked after 5 failed attempts
  TC-AUTH-005: Successful password reset via email
  TC-AUTH-006: Login with expired password prompts reset

Test Suite: Shopping Cart
  TC-CART-001: Add single item to empty cart
  TC-CART-002: Add item that is already in the cart (quantity incremented)
  TC-CART-003: Remove item from cart
  ...
```

Use a prefix per module (AUTH, CART, PAY, etc.) so test cases can be cross-referenced from requirements and defect reports.

## Traceability

Every test case must trace back to a requirement. Include a traceability matrix:

| Requirement | Test Cases | Coverage |
|---|---|---|
| FR-001: Daily reconciliation | TC-REC-001, TC-REC-002, TC-REC-003 | 3 cases |
| FR-002: Discrepancy alert | TC-REC-004, TC-REC-005 | 2 cases |
| FR-003: Dashboard filtering | TC-DASH-001, TC-DASH-002, TC-DASH-003, TC-DASH-004 | 4 cases |

If a requirement has zero test cases, flag it as a coverage gap.

## Output Checklist

Before delivering test cases, verify:

- [ ] Every test case has an ID, title, priority, preconditions, steps, and expected result
- [ ] Test data uses explicit values, not vague descriptions
- [ ] Steps are atomic (one action per step)
- [ ] Expected results are objectively verifiable
- [ ] Equivalence partitioning covers all valid and invalid input classes
- [ ] Boundary values are tested at, above, and below each boundary
- [ ] Decision tables are used for multi-condition logic
- [ ] Negative test cases are included (invalid inputs, unauthorized access, error handling)
- [ ] Traceability matrix links every test case to a requirement
- [ ] Test cases are grouped into logical test suites with consistent naming
