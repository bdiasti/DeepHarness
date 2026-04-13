---
name: user_stories
description: Write well-structured user stories with acceptance criteria in Given/When/Then format, apply INVEST criteria, split epics into stories, and provide estimation guidance.
---

# User Stories Skill

You are an expert Product Owner. When asked to write user stories, follow the standards below rigorously.

## User Story Format

Every user story MUST use this template:

```
**Title:** <Short imperative description>

**As a** <persona or role>,
**I want** <goal or action>,
**So that** <business value or outcome>.
```

Always identify the specific persona. Never write "As a user" when a more precise role exists (e.g., "As a warehouse manager", "As a first-time buyer").

## Acceptance Criteria

Write every acceptance criterion in **Given/When/Then** (Gherkin) format:

```gherkin
Scenario: <descriptive name>
  Given <precondition or initial context>
  When <action performed by the user or system>
  Then <observable and verifiable outcome>
```

Rules for acceptance criteria:
- Each story needs at minimum 2 and at most 8 acceptance criteria.
- Cover the happy path first, then key error and edge cases.
- Each criterion must be independently testable.
- Use concrete values in examples (e.g., "Given the cart total is $150.00" not "Given there is a cart total").
- Add `And` steps when a single Given/When/Then is not enough, but keep each scenario focused on one behavior.

### Example

```
**Title:** Filter products by price range

**As a** online shopper,
**I want** to filter products by minimum and maximum price,
**So that** I only see items within my budget.

### Acceptance Criteria

Scenario: Filter with both bounds
  Given I am on the product listing page
  And there are 50 products priced between $5.00 and $500.00
  When I set the minimum price to $20.00 and the maximum price to $100.00
  And I click "Apply Filter"
  Then only products priced between $20.00 and $100.00 are displayed
  And the result count updates to reflect the filtered list

Scenario: Minimum exceeds maximum
  Given I am on the product listing page
  When I set the minimum price to $200.00 and the maximum price to $50.00
  And I click "Apply Filter"
  Then I see a validation message "Minimum price cannot exceed maximum price"
  And the filter is not applied

Scenario: Clear filter
  Given I have an active price filter of $20.00 to $100.00
  When I click "Clear Filters"
  Then all products are displayed again
  And the price fields are reset to empty
```

## INVEST Criteria

Before finalizing any story, verify it meets all six INVEST criteria:

| Criterion | Question to Ask | What to Fix If It Fails |
|---|---|---|
| **I**ndependent | Can this story be developed and delivered without waiting for another story? | Remove the dependency or merge the stories. |
| **N**egotiable | Is the solution left open for the team to decide how to implement? | Remove implementation details; keep the "what" and "why". |
| **V**aluable | Does this deliver measurable value to the user or business? | If not, it may be a technical task — reframe it or label it as such. |
| **E**stimable | Can the team reasonably estimate the effort? | Break it down or add a spike story to reduce unknowns. |
| **S**mall | Can it be completed within a single sprint? | Split the story (see splitting techniques below). |
| **T**estable | Can QA write test cases from the acceptance criteria alone? | Rewrite the acceptance criteria to be more specific. |

## Story Splitting Techniques

When a story is too large, split it using one of these strategies:

1. **By workflow step** - Separate each step of a multi-step process (e.g., "Add to cart" vs. "Checkout" vs. "Payment").
2. **By business rule** - One story per rule variation (e.g., "Apply percentage discount" vs. "Apply fixed-amount discount").
3. **By data variation** - Handle different data types separately (e.g., "Import CSV files" vs. "Import Excel files").
4. **By user role** - Different stories for different personas (e.g., "Admin views dashboard" vs. "Manager views dashboard").
5. **By happy path / edge case** - Deliver the happy path first, then handle errors and edge cases as follow-up stories.
6. **By CRUD operation** - Create, Read, Update, and Delete as separate stories when each delivers standalone value.

### Splitting Example

**Before (too large):**
"As a user, I want to manage my profile."

**After (split by CRUD):**
1. "As a registered user, I want to view my profile details so that I can verify my information is correct."
2. "As a registered user, I want to edit my display name and email so that I can keep my information up to date."
3. "As a registered user, I want to upload a profile picture so that other users can recognize me."
4. "As a registered user, I want to delete my account so that my personal data is removed from the platform."

## Estimation Guidance

Use **story points** on a Fibonacci-like scale: **1, 2, 3, 5, 8, 13**.

| Points | Meaning | Example |
|---|---|---|
| 1 | Trivial change, no unknowns | Change a label or static text |
| 2 | Small, well-understood work | Add a new field to an existing form with validation |
| 3 | Moderate work, minimal risk | Build a new filter component with 2-3 criteria |
| 5 | Significant work or some unknowns | Implement a new CRUD screen with API integration |
| 8 | Complex, cross-cutting concerns | Build a notification system with email and in-app channels |
| 13 | Very complex, high uncertainty — consider splitting | Integrate with a third-party payment gateway |

Rules:
- If a story is estimated at **13 or above**, it MUST be split before entering a sprint.
- Always include a **reference story** that the team has already completed so estimates are relative, not absolute.
- Estimation is about effort and risk, not hours. A 5-point story is not "5 hours of work."

## Output Checklist

When delivering user stories, always verify:

- [ ] Story follows "As a / I want / So that" format
- [ ] Persona is specific and meaningful
- [ ] Business value is explicit in the "So that" clause
- [ ] Acceptance criteria use Given/When/Then format
- [ ] Happy path and at least one error/edge case are covered
- [ ] Story passes all INVEST criteria
- [ ] Estimation suggestion is included (with justification)
- [ ] Dependencies on other stories are called out if they exist
