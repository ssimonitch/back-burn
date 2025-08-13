# Agent Orchestration Patterns (Backend)

This document provides patterns and strategies for coordinating multiple specialized backend agents to deliver complete, production-ready FastAPI features. Use this when orchestrating work across endpoint design, repository/DI implementation, testing, code review, and documentation.

## Available Specialized Agents

### Development Agents
- **api-designer**: Designs API contracts and models from a product perspective, aligns OpenAPI with project conventions
- **python-backend-engineer**: Implements FastAPI endpoints, repository layer, DI wiring, and small refactors

### Testing Agents
- **python-test-engineer**: Pytest-based unit/integration tests, repository-mocking fixtures, coverage gate enforcement

### Review & Planning Agents
- **code-reviewer**: Production readiness, error mapping consistency, security and quality checks
- **sprint-manager**: Sprint planning, task breakdown, dependency analysis, progress tracking (planning only)

## Core Orchestration Patterns

### CRITICAL: Always Use Task Tool for Delegation
When orchestrating agents, invoke them with the Task tool. Delegate to specialized agents; do not implement inside orchestration steps.

### CRITICAL: Always use "ultrathink" with agents using the Sonnet model
When invoking agents configured with the Sonnet model, include the phrase "ultrathink" in the prompt to ensure subagents take enough time to think about the task.

### 1. Sequential Implementation Pattern (Backend)
For features where each phase depends on the previous.

Conceptual Flow:
```
1. api-designer → Define/adjust OpenAPI and models (planning-level)
2. python-backend-engineer → Implement endpoints + repositories + DI
3. python-test-engineer → Add/adjust unit/integration tests
4. code-reviewer → Final quality and security review
```

Actual Implementation with Task Tool:
```python
# Step 1: API contract
Task(
  subagent_type="api-designer",
  description="Design workout logging contract",
  prompt="Define/adjust the OpenAPI contract for workout logging per project conventions (auth model, pagination where applicable, error mapping)."
)

# Step 2: Backend implementation
Task(
  subagent_type="python-backend-engineer",
  description="Implement workout logging",
  prompt="Implement FastAPI endpoint(s) and repository/DI for workout logging. Follow repository pattern + DI and model-first endpoints."
)

# Step 3: Tests
Task(
  subagent_type="python-test-engineer",
  description="Test workout logging",
  prompt="Write unit/integration tests using repository-based fixtures. Maintain >= 80% coverage."
)

# Step 4: Review
Task(
  subagent_type="code-reviewer",
  description="Quality and security review",
  prompt="Review for error mapping consistency, auth coverage, and adherence to OpenAPI contract."
)
```

When to use: New endpoints, repository additions, contract updates.

### 2. Parallel Execution Pattern
For independent backend tasks to maximize efficiency.

Conceptual Flow:
```
Parallel:
├── python-backend-engineer → Implement Endpoint A
├── python-backend-engineer → Implement Repository method B
└── python-test-engineer → Write tests for existing Endpoint C
Then:
└── code-reviewer → Integration/consistency review
```

Actual Implementation with Task Tool:
```python
# Execute ALL in a single message for parallel processing
Task(
  subagent_type="python-backend-engineer",
  description="Implement GET /workouts",
  prompt="Implement listing endpoint using repository filtering + pagination contract."
)

Task(
  subagent_type="python-backend-engineer",
  description="Add repository method: list_recent_sessions",
  prompt="Add a thin repo method and DI. Keep types via minimal TypedDicts."
)

Task(
  subagent_type="python-test-engineer",
  description="Tests for plans detail endpoint",
  prompt="Add edge case tests using repo-based dependency overrides."
)

# After parallel work completes
Task(
  subagent_type="code-reviewer",
  description="Cross-feature consistency",
  prompt="Review error mapping, auth guards, and OpenAPI alignment across new changes."
)
```

When to use: Multiple independent endpoints/methods or test-only tasks.

### 3. Iterative Refinement Pattern
For tasks requiring back-and-forth until acceptance criteria are met.

Conceptual Flow:
```
Loop until AC met:
1. python-backend-engineer → Implementation
2. python-test-engineer → Tests identify issues
3. If issues: return to step 1
4. code-reviewer → Final approval
```

Actual Implementation with Task Tool:
```python
# Iteration 1: Initial implementation
Task(
  subagent_type="python-backend-engineer",
  description="Implement update endpoint for workouts",
  prompt="Implement PUT endpoint with validation and repository calls."
)

# Test the implementation
Task(
  subagent_type="python-test-engineer",
  description="Test workout update",
  prompt="Add tests for valid update, no-op update, and forbidden update scenarios."
)

# If issues found, iterate
Task(
  subagent_type="python-backend-engineer",
  description="Fix update validation",
  prompt="Address issues found by tests. Ensure consistent HTTP error mapping with plans endpoints."
)

# Re-test after fixes
Task(
  subagent_type="python-test-engineer",
  description="Verify fixes",
  prompt="Re-run tests and expand edge cases if needed. Maintain >= 80% coverage."
)

# Final review
Task(
  subagent_type="code-reviewer",
  description="Final review",
  prompt="Production readiness review: error mapping, security, and OpenAPI conformance."
)
```

When to use: Validation-heavy endpoints, nuanced business rules.

### 4. Debug-Fix-Verify Pattern
For systematic backend bug resolution.

Conceptual Flow:
```
1. python-test-engineer → Reproduce and isolate failing case
2. python-backend-engineer → Fix implementation or repository logic
3. python-test-engineer → Verify fix with tests
4. code-reviewer → Ensure no regressions, consistent behavior
```

Actual Implementation with Task Tool:
```python
# Step 1: Reproduce
Task(
  subagent_type="python-test-engineer",
  description="Reproduce pagination bug",
  prompt="Create failing test demonstrating incorrect pagination total for workouts."
)

# Step 2: Fix
Task(
  subagent_type="python-backend-engineer",
  description="Fix pagination bug",
  prompt="Correct repository list method to apply user_id filtering and deterministic order."
)

# Step 3: Verify
Task(
  subagent_type="python-test-engineer",
  description="Verify pagination fix",
  prompt="Ensure totals and page boundaries are correct, including edge cases."
)

# Step 4: Review
Task(
  subagent_type="code-reviewer",
  description="Regression check",
  prompt="Confirm no error mapping regressions and OpenAPI alignment."
)
```

When to use: Behavior regressions, data filtering issues, auth mistakes.

### 5. Sprint Task Completion Pattern
To move tasks through the sprint board.

Conceptual Flow:
```
For each task:
1. sprint-manager → Review requirements and acceptance criteria
2. api-designer → Confirm/adjust API contract (if needed)
3. python-backend-engineer → Implement endpoints/repositories/DI
4. python-test-engineer → Add/adjust tests
5. code-reviewer → Final approval
6. sprint-manager → Update sprint documentation
```

Actual Implementation with Task Tool:
```python
# Step 1: Review the task
Task(
  subagent_type="sprint-manager",
  description="Review Sprint 4 Task 3",
  prompt="Summarize requirements and AC for workout logging from sprint doc."
)

# Step 2: Contract (optional)
Task(
  subagent_type="api-designer",
  description="Contract check",
  prompt="Verify the OpenAPI contract for workout logging aligns with project conventions."
)

# Step 3: Implementation
Task(
  subagent_type="python-backend-engineer",
  description="Implement logging endpoint",
  prompt="Create endpoint + repository/DI using model-first approach."
)

# Step 4: Testing
Task(
  subagent_type="python-test-engineer",
  description="Test logging endpoint",
  prompt="Add repository-mocked tests and integration tests covering auth and validation."
)

# Step 5: Review
Task(
  subagent_type="code-reviewer",
  description="Final review",
  prompt="Ensure error mapping and OpenAPI conformance; no unused imports, clean diffs."
)

# Step 6: Update docs
Task(
  subagent_type="sprint-manager",
  description="Update sprint docs",
  prompt="Mark Task 3 as complete with notes on blockers and outcomes."
)
```

When to use: Progressing through Sprint 4 tasks.

## Agent Documentation Requirements

### Documentation Protocol
Each agent MUST create a summary in `docs/temp/`:

Filename: `agent_[YYYYMMDD_HHMMSS]_[agent-name]_[task-brief].md`

Content Structure:
```markdown
# Agent Summary: [Agent Name] - [Task]
Date: [YYYY-MM-DD HH:MM:SS]

## Task Overview
[Brief description]

## Key Decisions
1. **[Decision]**: [Rationale]
2. **[Decision]**: [Rationale]

## Assumptions Made
- [Assumption]

## Implementation Details
- [What changed]

## Blockers & Resolutions
- **Blocker**: [Description]
  **Resolution**: [Resolution]

## Handoff Notes
- [Next steps]

## Quality Validation
- mypy: ✅/❌ [details]
- ruff: ✅/❌ [details]
- pytest: ✅/❌ [X/Y passing, coverage %]
```

### When to Document
- Always after significant work
- Before handoff
- On escalation

## Blocker Escalation Protocol

### Critical Blockers (STOP IMMEDIATELY)
Require immediate user intervention:

1. Security Vulnerabilities
```
🔴 SECURITY ALERT: [Description]
Impact: [What could happen]
Options: [Possible solutions]
```

2. Data Integrity Risks
```
🔴 DATA RISK: [Description]
Affected: [Data/Systems]
Recommendation: [Safe path forward]
```

3. Architectural Conflicts
```
🟡 ARCHITECTURE CONFLICT: [Description]
Current Design: [What exists]
Required Change: [What's needed]
User Decision Needed: [Options]
```

### Design Ambiguity Escalation
```
🟡 CLARIFICATION NEEDED:
Requirement: [What was requested]
Ambiguity: [What's unclear]
Options:
1. [Option A]
2. [Option B]
Recommendation: [If applicable]
```

### Technical Debt Warning
```
⚠️ TECHNICAL DEBT WARNING:
Quick Fix: [Workaround]
Debt Impact: [Future problems]
Proper Solution: [Time/effort]
User Decision: Proceed with workaround or invest in proper solution?
```

## Context Passing Strategies

### Initial Context for First Agent
```
"[TASK DESCRIPTION]

Please ensure you:
1. Read @CLAUDE.md for project conventions
2. Read @docs/00_project_brief.md for overview
3. Follow the repository pattern + DI conventions
4. Use OpenAPI workflow (generate → verify → publish)
5. Follow testing best practices (repo-based fixtures)

Documentation Requirement:
Create summary in docs/temp/agent_[timestamp]_[your-name]_[task].md

Escalation Protocol:
STOP and alert user for security issues, architectural conflicts, or high-debt workarounds.

[SPECIFIC REQUIREMENTS]

Use project tasks (poe): fix, test, generate-openapi, verify-openapi, publish-openapi.
Ensure mypy, ruff, and tests all pass (coverage ≥ 80%)."
```

### Handoff Context Between Agents
```
"The previous agent (@agent-[NAME]) has completed:
[SUMMARY OF WORK]

Previous agent's documentation: docs/temp/agent_[timestamp]_[name]_[task].md
Key decisions made: [Brief list]

Now please:
[NEXT TASKS]

Create your own summary: docs/temp/agent_[timestamp]_[your-name]_[task].md
Build upon previous work ensuring compatibility.
Alert if previous decisions conflict with best practices."
```

### Context for Parallel Agents
```
"Working in parallel on related components.
Your specific task: [ENDPOINT/REPOSITORY]
Ensure your work integrates with: [OTHER TASKS]

Document in: docs/temp/agent_[timestamp]_[your-name]_[task].md
Note any integration assumptions for other agents."
```

## Quality Gates

Between every handoff, enforce these validations:

### Required Checks
1. mypy: `uv run poe typecheck` (or equivalent) - Zero errors
2. ruff: `uv run poe fix` - Lint and format pass
3. pytest: `uv run poe test` - All tests pass, coverage ≥ 80%
4. OpenAPI: `uv run poe generate-openapi` + `uv run poe verify-openapi` + `uv run poe publish-openapi` - Contract up to date

### Forbidden Patterns
- No broad `# type: ignore` without justification and scope limitation
- No blanket `ruff` disables; target specific rules with reason if needed
- No skipped tests without documented rationale
- No direct Supabase mocking in API tests; prefer repository DI overrides
- No divergence from OpenAPI source of truth

## Error Recovery Patterns

### Test Failure Recovery
```
When: Tests fail after implementation
1. Collect specific failure details from test agent
2. Document failure in docs/temp/
3. Create focused fix requirements
4. Return to backend engineer with fixes
5. Maximum 3 iterations before escalating
6. If still failing: ESCALATE with options
```

### mypy/ruff Failure Recovery
```
When: Type or lint checks fail
1. Identify specific violations
2. Document attempted fixes in docs/temp/
3. Return to responsible agent with requirements
4. Fix without broad ignores
5. If unfixable without ignore: ESCALATE for guidance
```

### Architecture Conflict Recovery
```
When: Implementation conflicts with design
1. Document the conflict in docs/temp/
2. ESCALATE if it affects core functionality
3. Adjust contract/design via api-designer if needed
4. Cascade changes and update docs
```

## Complex Workflow Examples

### Example 1: Complete Workout Logging Feature
```
Workflow:
1. @agent-sprint-manager: Break down requirements
2. @agent-api-designer: Confirm OpenAPI contract
3. @agent-python-backend-engineer: Implement endpoint + repository/DI
4. @agent-python-test-engineer: Add unit/integration tests
5. @agent-code-reviewer: Production readiness review
6. @agent-sprint-manager: Update sprint docs
```

### Example 2: Error Mapping Consistency Pass
```
Workflow:
1. @agent-python-test-engineer: Add tests verifying error responses
2. @agent-python-backend-engineer: Normalize exceptions and mappings
3. @agent-code-reviewer: Verify consistency across endpoints
```

### Example 3: OpenAPI Contract Update
```
Workflow:
1. @agent-api-designer: Update contract (non-breaking)
2. @agent-python-backend-engineer: Align models/endpoints
3. @agent-python-test-engineer: Update tests
4. @agent-code-reviewer: Verify schema determinism and publish workflow
```

## Communication Templates

### Progress Update Template
```
✅ Completed: [AGENT] - [WHAT WAS DONE]
🔄 In Progress: [AGENT] - [CURRENT WORK]
⏳ Next: [AGENT] - [UPCOMING WORK]

Quality Status:
- mypy: ✅/❌ [details]
- ruff: ✅/❌ [details]
- pytest: ✅/❌ [X/Y passing, coverage %]
- OpenAPI: ✅/❌ [generated/verified/published]
```

### Handoff Summary Template
```
@agent-[PREVIOUS] has completed:
- [Achievement 1]
- [Achievement 2]
- All validations passing

Handing off to @agent-[NEXT] for:
- [Task 1]
- [Task 2]

Context: [Considerations]
```

### Final Summary Template
```
Feature: [NAME] - Complete ✅

Agents Involved:
1. @agent-[NAME]: [Contribution]
2. @agent-[NAME]: [Contribution]

Deliverables:
- [Endpoint/Repository]
- [Docs updated]
- [X tests added]

Quality Validation:
- mypy: ✅ No errors
- ruff: ✅ All rules pass
- tests: ✅ X/X passing (≥ 80% coverage)
- OpenAPI: ✅ generated/verified/published

[Follow-up items]
```

## Best Practices

### DO:
- ✅ Delegate to specialized agents via Task tool
- ✅ Run agents in parallel when tasks are independent
- ✅ Pass context to avoid redundant work
- ✅ Enforce quality gates between handoffs
- ✅ Document why specific agents were chosen
- ✅ Plan for recovery paths
- ✅ Respect agent expertise boundaries

### DON'T:
- ❌ Skip validations between agents
- ❌ Force agents outside their domain
- ❌ Forget to provide context documents
- ❌ Run sequentially when parallel is possible
- ❌ Proceed without clear acceptance criteria
- ❌ Accumulate technical debt without documenting
- ❌ Bypass OpenAPI workflow

## When to Use Explicit Orchestration

Use explicit orchestration for:
1. Multi-sprint planning
2. Complex backend features (multiple endpoints/repositories)
3. Architecture adjustments affecting multiple modules
4. Urgent bug fixes requiring coordination
5. Cross-functional work (backend + documentation + planning)

## Measuring Success

Successful orchestration achieves:
- ✅ Acceptance criteria met
- ✅ mypy/ruff clean
- ✅ Tests passing with coverage ≥ 80%
- ✅ OpenAPI generated/verified/published
- ✅ Clear handoffs and updated docs
- ✅ User requirements fulfilled

## Troubleshooting

### Common Issues and Solutions

Issue: Agents produce incompatible changes
Solution: Ensure all reference the same sprint doc and prior agent summaries.

Issue: Validation failures between handoffs
Solution: Return to responsible agent with focused fix requirements; avoid ignores.

Issue: Conflicting contracts and implementations
Solution: Re-run api-designer to reconcile; document changes and cascade.

Issue: Performance concerns in endpoints
Solution: Add focused tests; consider repository-level optimizations; verify results.

---

## Proposed Agent Additions (Suggestions)
- **database-architect**: Plans DB schema and RLS policy changes; coordinates with Supabase. Scope: planning/design only; implementation via backend engineer.
- **security-auditor**: Focused security reviews (auth paths, RLS assumptions, input validation), complements code-reviewer for sensitive changes.
- **load-tester**: Targeted performance testing for high-traffic endpoints (optional for later sprints).

If adopted, add them under `.claude/agents/` with responsibilities aligned to this document.
