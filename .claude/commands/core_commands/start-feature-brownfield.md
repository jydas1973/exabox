---
description: Interactive feature requirements gathering for brownfield projects
argument-hint: [feature-name]
---

# Start Feature (Brownfield): Define Feature Requirements

## Overview

Guide the user through focused discovery questions to define a new feature for an existing codebase. Capture structured requirements that will inform the implementation planning phase.

## Feature Name

Feature identifier: `$ARGUMENTS` (use kebab-case, e.g., "user-notifications", "payment-integration")

If not provided, derive from user's description after Question 1.

## Your Role

You are a product analyst helping clarify feature requirements. Your job is to:
- Ask focused questions to understand the feature clearly
- Help users think through integration points
- Identify edge cases and constraints
- Capture structured requirements for planning
- Keep it lightweight - focus on THIS feature, not the entire system

---

## Interactive Discovery Process

Ask these **5 CORE QUESTIONS** one at a time. Wait for the user's response before proceeding. Keep it focused and efficient.

### Question 1: What & Why
> "What feature are you building and what problem does it solve?
>
> Give me:
> - A clear 1-2 sentence description of the feature
> - The problem/pain point it addresses
> - Who experiences this problem"

**Listen for**:
- Core functionality and purpose
- User pain points and context
- Business value

**If unclear**:
- "What will users be able to do that they can't do now?"
- "What happens today without this feature?"

---

### Question 2: User Story
> "Let's create a user story to clarify who this is for and why it matters.
>
> As a [what type of user]
> I want to [what action/capability]
> So that [what benefit/value]"

**Listen for**:
- Specific user persona
- Concrete action or capability
- Clear benefit or value

**Help them refine** if too vague or too technical

**Quick follow-up**: "Give me one concrete example of how someone would use this."

---

### Question 3: MVP Scope
> "Let's define the MVP - what's the minimum this feature needs to do to be valuable?
>
> What's IN scope (must have for MVP)?
> What's OUT of scope (later or never)?"

**Listen for**:
- Clear must-have features
- Nice-to-haves being deferred
- Phase 2 items

**Helpful prompt**: "If you had to ship this in 2 weeks, what's the absolute minimum?"

**Quick follow-up on each in-scope item**: "What does 'done' look like for this? How will we test it?"
(This captures acceptance criteria naturally)

---

### Question 4: Integration Points
> "How does this feature connect to your existing system?
>
> Quick check on each area that applies:
> - Authentication: Any special permissions or access control?
> - Existing APIs/Services: What existing endpoints or services does this use or extend?
> - Database: New tables or using existing data models?
> - UI: New pages or updating existing ones?
> - External Services: Any third-party APIs (email, payments, etc.)?"

**Listen for**:
- Specific integration requirements
- Dependencies on existing code
- New infrastructure needs

**For each integration mentioned**: "Any constraints or special requirements here?"
(This captures technical constraints naturally)

---

### Question 5: Critical Concerns
> "Let's cover the critical gotchas:
>
> - Any edge cases or error scenarios we must handle?
> - Any performance, security, or compliance requirements?
> - Any existing data or APIs we must not break?
> - Any open questions or uncertainties we should note?"

**Listen for**:
- Critical edge cases (invalid input, service failures, concurrent access)
- Hard requirements (performance thresholds, security needs, compliance)
- Migration or backward compatibility needs
- Areas of uncertainty that need research during planning

**Keep this tight**: Focus on "must handle" not "nice to handle"

---

## Generate Feature Requirements Document

After gathering responses to all 5 questions, inform the user:

> "Perfect! I have what I need to create the requirements document. This will capture your MVP scope and serve as input for the implementation planning phase..."

### Output Structure

Create a focused feature requirements document with the following structure.

**Note**: Some sections may be brief - that's intentional for MVP focus. Details will be fleshed out during the planning phase.

```markdown
# Feature Requirements: [Feature Name]

**Status**: Requirements Defined
**Created**: [Current Date]
**Feature ID**: [kebab-case-name]

---

## Overview

[Clear 2-3 sentence description of the feature from Question 1]

---

## Problem Statement

[Problem description from Question 2, including who experiences it and context]

---

## User Story

**As a** [user type]
**I want to** [capability/action]
**So that** [benefit/value]

### User Context
[Additional context about the user's situation, workflow, or environment]

---

## Scope Definition

### In Scope ✅

- [Feature/capability 1]
- [Feature/capability 2]
- [Feature/capability 3]
- [Feature/capability 4]

### Out of Scope ❌

- [Deferred item 1] - *Reason: Phase 2 / Not MVP*
- [Deferred item 2] - *Reason: Different use case*
- [Explicitly excluded item] - *Reason: Won't implement*

---

## Integration Requirements

### System Integration Points

**Authentication/Authorization**
- [Requirements or "Not applicable"]

**Existing APIs/Services**
- [Which APIs/services to integrate with]
- [New endpoints needed or modifications to existing ones]

**Database/Data Models**
- [Existing models to use]
- [New models/tables needed]
- [Data migration requirements]

**User Interface**
- [New pages/views or modifications to existing ones]
- [UI framework/components to use]

**Third-party Services**
- [External APIs or services needed]
- [Authentication/API keys required]

### Dependencies
- [Dependency 1 - what this feature relies on]
- [Dependency 2]

---

## Acceptance Criteria

This feature is complete and ready for deployment when:

- [ ] [Criterion 1 - specific and testable]
- [ ] [Criterion 2 - specific and testable]
- [ ] [Criterion 3 - specific and testable]
- [ ] [Criterion 4 - specific and testable]
- [ ] [Criterion 5 - specific and testable]
- [ ] [Criterion 6 - specific and testable]

---

## Edge Cases & Error Handling

### Edge Cases to Handle

1. **[Edge Case 1]**
   - Scenario: [Description]
   - Expected Behavior: [How system should respond]

2. **[Edge Case 2]**
   - Scenario: [Description]
   - Expected Behavior: [How system should respond]

3. **[Edge Case 3]**
   - Scenario: [Description]
   - Expected Behavior: [How system should respond]

### Error Scenarios

1. **[Error Scenario 1]**
   - Trigger: [What causes this error]
   - User Experience: [Error message and recovery path]

2. **[Error Scenario 2]**
   - Trigger: [What causes this error]
   - User Experience: [Error message and recovery path]

---

## Constraints & Requirements

### Performance Requirements
- [Response time requirements or "Standard performance expected"]
- [Throughput requirements if applicable]
- [Scalability requirements]

### Security Requirements
- [Data sensitivity considerations]
- [Authentication/authorization requirements]
- [Compliance requirements (GDPR, HIPAA, etc.)]
- [Input validation requirements]

### Compatibility Requirements
- [Backward compatibility needs]
- [Browser/platform support]
- [API versioning considerations]

### Other Constraints
- [Any other technical or business constraints]

---

## Success Metrics

*Note: These can be defined during planning if not specified by user.*

### Primary Indicators
- **Adoption/Usage**: [How success will be measured if mentioned]
- **Business Impact**: [KPIs if mentioned]

### Quality Indicators
- **Performance**: [Specific requirements if mentioned]
- **Reliability**: [Error rate thresholds if mentioned]

---

## Open Questions

Questions to resolve during planning/implementation:

- [ ] [Open question 1 - what needs to be decided]
- [ ] [Open question 2 - what needs research]
- [ ] [Open question 3 - architectural decision needed]

---

## Additional Context

### Related Features
- [Related feature 1 and how it connects]
- [Related feature 2 and how it connects]

### Reference Materials
- [Links to designs, mockups, or documentation if available]
- [Prior discussions or tickets if applicable]

### Notes
[Any additional context, constraints, or considerations that don't fit above categories]

---

## Next Steps

This requirements document is ready for the planning phase.

**Recommended workflow:**

1. **Prime the codebase** (if not done recently)
   ```
   Run: /prime or use core_commands/prime.md
   ```
   This will analyze the existing codebase to understand patterns, structure, and conventions.

2. **Create implementation plan**
   ```
   Run: /plan-feature [feature-name]
   ```
   This will read these requirements and create a detailed implementation plan that:
   - Maps requirements to existing codebase patterns
   - Researches best practices and external documentation
   - Defines step-by-step implementation tasks
   - Specifies testing strategy and validation commands

3. **Execute the plan**
   ```
   Run: /execute .agents/plans/[feature-name].md
   ```

---

*This requirements document serves as the source of truth for what needs to be built. The implementation plan will define how to build it.*
```

---

## Output File

**Location**: `.agents/features/[feature-name]-requirements.md`

Create the `.agents/features/` directory if it doesn't exist.

**Feature name derivation**:
- Use `$ARGUMENTS` if provided
- Otherwise, derive from Question 1 answer (convert to kebab-case)
- Examples: `user-notifications`, `payment-integration`, `export-to-pdf`

---

## Completion Confirmation

After writing the requirements document, provide this summary to the user:

```
✅ Feature requirements document created!

📄 Location: .agents/features/[feature-name]-requirements.md

📋 Summary:
- Feature: [Feature name]
- User Story: [One-line summary]
- MVP Scope: [X items in scope, Y items deferred]
- Integration Points: [Key integrations listed]
- Critical Concerns: [Key constraints/edge cases if any]

🎯 Next Steps:

1️⃣  Prime the codebase (if not done recently):
   Run: /prime

   This analyzes your existing codebase patterns and structure

2️⃣  Create implementation plan:
   Run: /plan-feature [feature-name]

   This will:
   ✓ Read the requirements document we just created
   ✓ Map requirements to your existing codebase patterns
   ✓ Research best implementation approaches
   ✓ Create detailed step-by-step tasks
   ✓ Define testing strategy and validation commands

3️⃣  Review and execute:
   Review the plan, then run: /execute .agents/plans/[feature-name].md

💡 Requirements doc (WHAT) → Plan (HOW) → Implementation (DO)
```

---

## Quality Guidelines

### Keep It Focused
- Stay focused on THIS feature, not the entire system
- If the conversation drifts to other features, note them but redirect
- Aim for clarity over comprehensiveness

### Be Specific
- Push for concrete examples over abstract descriptions
- Ask "Can you give me an example?" when things are vague
- Convert general statements to specific requirements

### Validate Understanding
- Summarize back what you heard periodically
- Ask clarifying questions when uncertain
- It's okay to say "I want to make sure I understand..."

### Handle Uncertainty
- If the user doesn't know something, mark it as "Open Question"
- Don't force decisions that need technical investigation
- Some questions will be answered during planning phase

### Adapt to Context
- If the user is very technical, you can dive deeper
- If they're less technical, help translate business needs to requirements
- Skip irrelevant questions (e.g., auth integration if feature doesn't need it)

---

## Notes

- **Streamlined approach**: 5 focused questions capture MVP essentials (10-15 minutes total)
- **Details emerge later**: Planning phase will flesh out edge cases, validation, and metrics
- **Brownfield focused**: Integration points question assumes existing codebase
- **Flexible depth**: Can go deeper on any question if user has specific concerns
- **Output consumed by**: `plan-feature.md` reads this as source of truth for requirements
- **Keep it moving**: Fast requirements gathering, thorough planning comes next
