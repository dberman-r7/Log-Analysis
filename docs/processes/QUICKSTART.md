# Quick Reference Guide

**For Developers New to This Repository**

This is your TL;DR guide to working in this repository. For complete details, see the full documentation.

---

## ⚡ 5-Minute Quick Start

### Before You Start ANY Work

1. **Read**: [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) (at least skim it)
2. **Understand**: Every change needs approval before implementation
3. **Remember**: Tests before code (TDD), always

### The Basic Workflow

```
1. User makes request
2. You create CR (Change Request) document
3. You do Impact Assessment
4. You create Implementation Plan
5. Wait for user to say "Approved to Proceed" (ATP)
6. NOW you can write code (TDD: Red→Green→Refactor)
7. Submit PR with DoD checklist completed
```

**DO NOT SKIP STEP 5!** No coding until ATP received.

---

## 📝 Common Tasks

### Creating a Change Request (CR)

```bash
# 1. Copy template
cp docs/processes/templates/cr-template.md docs/processes/change-requests/CR-2026-02-09-001.md

# 2. Fill it out with:
# - What you're changing
# - Why you're changing it
# - Impact assessment (files, security, performance)
# - Implementation plan (step-by-step)

# 3. Present to user and wait for ATP
```

### Updating the RTM

Every code change = RTM update. No exceptions.

```bash
# Edit docs/requirements/rtm.md

# Add new requirement:
REQ-042: [FUNC] System shall do XYZ

# Update implementation details when code is written
# Link tests when tests are written
```

### Creating an ADR

If you're making an architectural decision (new tech, new pattern, significant change):

```bash
# 1. Copy template
cp docs/arch/adr-template.md docs/arch/adr/0001-my-decision.md

# 2. Fill out:
# - What decision you're making
# - Options you considered
# - Why you chose this option
# - Consequences (good and bad)
```

### TDD Workflow

```bash
# RED: Write failing test
pytest tests/test_feature.py  # Should fail

# GREEN: Write minimum code to pass
# ... write code ...
pytest tests/test_feature.py  # Should pass

# REFACTOR: Improve code quality
# ... refactor ...
pytest tests/test_feature.py  # Should still pass
```

---

## 🚫 Common Mistakes to Avoid

### ❌ "I'll just quickly..."

**NO.** Every change needs:
- Change Request (CR)
- Approval (ATP)
- Tests
- Documentation update

There are no "quick" changes that bypass governance.

### ❌ "The test is wrong"

**NO.** If a test fails, the code is wrong, not the test.

Only change tests if:
- The requirement changed (document it!)
- The test itself has a bug (prove it with another test)

### ❌ "I'll document it later"

**NO.** Documentation is code. It gets updated with the code, not "later".

If you modify src/, you MUST update docs/requirements/rtm.md in the same PR.

### ❌ "Coverage slows me down"

**NO.** 80% coverage is mandatory. No exceptions.

If you can't test it, you can't merge it.

### ❌ "It's just a config change"

**NO.** Even config changes need:
- CR documentation
- Impact assessment
- Review
- Testing

---

## ✅ The DoD Checklist (Required for Every PR)

Before you create a PR, verify:

- [ ] CR created and ATP received
- [ ] Tests written FIRST (TDD Red)
- [ ] Code works (TDD Green)
- [ ] Code refactored (TDD Refactor)
- [ ] RTM updated
- [ ] Coverage ≥ 80%
- [ ] Linter passes (zero warnings)
- [ ] Security scan clean
- [ ] Documentation updated
- [ ] ADR created (if architectural)
- [ ] No hardcoded secrets

If even ONE item is unchecked, the PR is not ready.

See [full DoD checklist](./definition-of-done.md) for complete list.

---

## 🔍 Where Do I Find...?

### Requirements

➡️ [`docs/requirements/rtm.md`](../requirements/rtm.md)

Every requirement in the system, with REQ-ID, status, implementation location, and test coverage.

### Architectural Decisions

➡️ [`docs/arch/adr/`](../arch/adr/)

History of significant decisions made, with rationale and alternatives considered.

### Change Management Process

➡️ [`docs/processes/change-management.md`](./change-management.md)

Complete guide to CR creation, Impact Assessment, and approval workflow.

### Definition of Done

➡️ [`docs/processes/definition-of-done.md`](./definition-of-done.md)

Checklist of everything needed before a PR can be merged.

### Technical Debt

➡️ [`docs/processes/tech-debt.md`](./tech-debt.md)

Known issues, shortcuts taken, and repayment plans.

### Templates

➡️ [`docs/processes/templates/`](./templates/)

Templates for CR, ADR, and other documents.

---

## 💡 Tips for Success

### 1. Start Small
Your first few CRs should be small changes to learn the process. Don't tackle a massive feature until you're comfortable with governance.

### 2. Use Templates
Every template exists for a reason. Don't skip sections - they catch important things.

### 3. Ask Questions
Better to ask "Is this an architectural change?" than to skip the ADR and have it pointed out in review.

### 4. Automate Checks
Run linter, tests, and security scans locally before pushing. Don't wait for CI to tell you.

### 5. Read Other CRs and ADRs
See how others document changes. Learn from good examples.

### 6. Think "Blast Radius"
Every change has an impact. Think through all the places it might affect before you start coding.

---

## 🆘 I'm Stuck - What Do I Do?

### Problem: "I don't know if I need an ADR"

**Ask yourself**:
- Am I introducing new technology?
- Am I changing how components interact?
- Will future developers need to understand why I made this choice?
- Is this decision hard to reverse?

If any answer is "yes" → Create ADR.

If unsure → Ask in code review.

### Problem: "My change is too small for all this process"

**Wrong!** Size doesn't matter. Even one-line changes:
- Could break something (need tests)
- Need documentation (for future you)
- Need review (fresh eyes catch issues)

The governance exists to prevent small changes from causing big problems.

### Problem: "The user won't give me ATP"

**Good!** The process is working. Either:
- Your plan needs improvement (revise CR and IA)
- The user has concerns (address them)
- The change shouldn't be made (okay to not do something)

Don't work around the approval process. Fix the plan or communicate better.

### Problem: "I can't get 80% coverage on this code"

**Then the code is wrong.** Untestable code is usually poorly designed code.

Options:
1. Refactor to make it testable (usually best)
2. Document why it can't be tested (requires exemption)
3. Rethink the approach entirely

If you can't test it, users can't rely on it.

---

## 🎯 Success Criteria

You're successful when:

✅ Every PR has CR-ID in title  
✅ RTM is always up-to-date  
✅ Tests exist for all code  
✅ Coverage is ≥ 80%  
✅ Zero hardcoded secrets  
✅ Documentation matches code  
✅ ADRs explain significant decisions  
✅ CI passes on every push  

---

## 🚀 Pro Tips from Experienced Developers

### "I batch my documentation updates"

Write CR → Write tests → Write code → Update docs ALL IN ONE SITTING.

Don't context switch. Finish the whole thing while it's fresh.

### "I use the templates as checklists"

Even if I don't fill out the template file, I use it as a mental checklist to ensure I thought through everything.

### "I test in production... with feature flags"

Use feature flags to deploy code that isn't user-facing yet. Test in prod without risk.

### "I ask for early review"

Before implementing, I share my CR and IA with a colleague. Catches issues before I waste time coding.

### "I keep a personal checklist"

In addition to DoD, I have my own checklist of things I commonly forget. I run through it before every PR.

---

## 📚 Next Steps

1. **Read the full governance framework**: [`.github/copilot-instructions.md`](../.github/copilot-instructions.md)
2. **Review a few existing CRs**: See how others document changes
3. **Practice with a small change**: Start with a minor bug fix or doc update
4. **Ask questions**: No question is too basic

---

## 🔗 Essential Links

- **Main Governance**: [`.github/copilot-instructions.md`](../.github/copilot-instructions.md)
- **Change Management**: [`change-management.md`](./change-management.md)
- **Definition of Done**: [`definition-of-done.md`](./definition-of-done.md)
- **RTM**: [`../requirements/rtm.md`](../requirements/rtm.md)
- **ADR Template**: [`../arch/adr-template.md`](../arch/adr-template.md)

---

**Remember**: The governance framework exists to help you, not slow you down. It catches issues early when they're cheap to fix, not late when they're expensive.

**When in doubt, ask. When confident, still ask.**

Good luck! 🎉
