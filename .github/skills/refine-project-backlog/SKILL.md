---
name: refine-project-backlog
description: Review a GitHub Projects backlog URL, find Ready cards with incomplete User Stories or Acceptance Criteria, and complete those fields from the card title.
---

# Refine GitHub Project backlog

Use this skill when the user provides a GitHub Projects URL and asks to review or complete backlog cards.

## Required input

- A GitHub Project URL in one of these forms:
  - `https://github.com/orgs/<owner>/projects/<number>`
  - `https://github.com/users/<owner>/projects/<number>`
  - `https://github.com/orgs/<owner>/projects/<number>/views/<number>`
  - `https://github.com/users/<owner>/projects/<number>/views/<number>`

If the URL is missing or cannot be parsed, ask for a project URL before making any changes.

## Workflow

1. Parse the URL into `owner`, `ownerType` (`ORGANIZATION` or `USER`), and `projectNumber`.
2. Authenticate with the GitHub account available to the agent. Do not ask the user to paste a token.
3. Read the project with GraphQL and retrieve:
   - Project title and URL.
   - All project items, including pagination.
   - Each item's content title, body, URL, and issue or draft-issue identity.
   - The project's single-select, text, and iteration fields and each item's field values.
4. Locate the status field. Treat a card as **Ready** only when its status field value is exactly `Ready` (case-sensitive after trimming). Do not infer Ready from labels, title, position, or a similar status.
5. For every Ready card, inspect the fields or body that represent:
   - **User Story**
   - **Acceptance Criteria**

   Field matching is case-insensitive and ignores surrounding whitespace. Accept common variants such as `User story`, `User Story`, `user_story`, `Acceptance criteria`, and `AC`. Prefer dedicated project text fields. If the project has no dedicated fields, inspect clearly labelled sections in the issue or draft-issue body.
6. Consider a field incomplete when it is absent, blank, only a placeholder, or does not contain a complete outcome-oriented statement. Acceptance Criteria are incomplete when they do not contain at least one independently verifiable criterion.
7. Before generating content, identify the feature's business rules and external standards from the card title, issue body, labels, linked issue context, repository documentation, tests, and existing implementation:
   - Look for threshold tables, classification names, formulas, units, boundary rules, effective dates, and the authoritative source of those rules.
   - For domain-specific features such as BMI, medical, military-service, legal, tax, or financial classification, treat the applicable standard as a required requirement, not an optional implementation detail.
   - Acceptance Criteria must state how the system obtains or uses the standard, including the source/reference, the classification ranges or decision rules, boundary behavior, units, and what happens when the standard is missing, invalid, or changed.
   - If the title implies a standard-based result but no authoritative standard can be found, do not invent thresholds or claim the requirement is complete. Mark the card as blocked and ask the user to provide or approve the standard before updating it. A threshold supplied by the user or already documented as the project's approved rule may be used, but it must be recorded explicitly in the Acceptance Criteria with its source or approval status.
8. For each incomplete field, generate content from the card title and any existing description, labels, linked issue context, and discovered business rules:
   - User Story must use this exact three-part format, with each placeholder replaced by specific content:
     ```
     **As a** [身分 / Persona]
     **I want to** [功能 / Need]
     **So that** [價值 / Purpose]
     ```
     Keep the three parts on separate lines. The Persona must identify the user role, Need must describe the capability from the title, and Purpose must describe the user or business value.
   - Acceptance Criteria must use a Markdown checklist with at least three concrete, independently testable criteria where the title supports them. For standard-based features, include criteria covering all of the following when applicable:
     - the authoritative standard or approved source;
     - the input formula, units, and valid range;
     - each relevant classification range and inclusive/exclusive boundary;
     - a representative example or boundary test;
     - missing, invalid, or unavailable standard data.
     ```
     - [ ] Given the approved <standard/source>, when the system evaluates <inputs>, then it applies the documented formula and units.
     - [ ] Given an input at each classification boundary, when the system evaluates it, then the result follows the documented inclusive/exclusive rule.
     - [ ] Given <edge or invalid case>, when the user requests a calculation, then <expected handling>.
     - [ ] The change is complete when the result can be verified against the approved standard and representative examples.
     ```
     Every criterion must begin with `- [ ]`; do not use numbered lists or unchecked text without a checkbox.
     Never invent integrations, permissions, numeric limits, or implementation details that are not supported by the title or existing context. When the title is too vague to derive safe criteria, report the card and ask the user for clarification instead of writing speculative requirements.
9. Before updating anything, present a compact plan listing each card, its URL, the fields to be changed, the discovered standard/source, and the proposed text. If the user explicitly requested automatic completion in the current request, proceed with the updates; otherwise ask for confirmation.
10. Update only the incomplete User Story and Acceptance Criteria fields. Preserve existing text and all other project fields. Use the project field IDs and item IDs returned by GraphQL; never update a field by display name alone.
11. Re-read every updated item and verify that the saved values exactly match the proposed content and include the discovered standard, rules, and boundary behavior.
12. Report:
    - Number of Ready cards inspected.
    - Number of cards changed.
    - Each changed card with a Markdown link and the fields updated.
    - Any skipped or blocked cards and the precise reason, including missing domain standards or unresolved ambiguity.
    - Verification results.

## GraphQL guidance

Use cursor pagination for both project items and project fields. Query organization and user projects separately based on `ownerType`.

The project lookup should include `id`, `number`, `title`, `url`, fields, and items. For items, request `fieldValues(first: 100)` and handle `ProjectV2ItemFieldTextValue`, `ProjectV2ItemFieldSingleSelectValue`, and `ProjectV2ItemFieldIterationValue`.

Use these mutations as appropriate:

- `updateProjectV2ItemFieldValue` for dedicated text fields. Supply the project ID, item ID, field ID, and `text`.
- `updateIssue` for an issue body when the project's configured convention stores the fields in the body.
- `updateProjectV2DraftIssue` for a draft issue body when the item is a draft issue.

Do not use a destructive replacement of the complete issue body when only a labelled section needs changing. Preserve unrelated sections and update only the matching User Story or Acceptance Criteria section. If a dedicated text field and a body section both exist, update the dedicated field only unless the user explicitly requests both.

## Safety and error handling

- Never modify cards that are not Ready.
- Never silently treat a missing status, missing field, permission error, API error, or ambiguous title as success.
- Do not create new cards, change status, reorder cards, edit titles, alter labels, or modify unrelated fields.
- Do not expose access tokens or put credentials in output.
- If a project has multiple fields that could represent User Story or Acceptance Criteria, report the ambiguity and ask the user to select the field.
- If the authenticated account cannot read or write the project, report the exact permission failure and leave the project unchanged.
- If an update partially fails, report successful and failed updates separately and re-read the affected cards before retrying.

## Output format

Use this structure:

```markdown
## Backlog refinement

- Project: [project name](project URL)
- Ready cards inspected: <count>
- Cards updated: <count>

### Updated
- [Card title](card URL)
  - User Story: added / already complete using the `As a / I want to / So that` format
  - Acceptance Criteria: added / already complete as a Markdown checklist

### Skipped or blocked
- [Card title](card URL): <reason>

### Verification
- <what was re-read and confirmed>
```
