# ADR Template (MADR Format)

This template follows the **Markdown Architectural Decision Records (MADR)** format.

Copy this template to create a new ADR:
1. Copy this file to `/docs/arch/adr/NNNN-title-with-dashes.md`
2. Replace NNNN with next sequential number (e.g., 0001, 0002, etc.)
3. Fill in all sections
4. Submit as part of your PR

---

# ADR-NNNN: [Short Title of Decision]

**Status**: [PROPOSED | ACCEPTED | DEPRECATED | SUPERSEDED by ADR-XXXX]

**Date**: YYYY-MM-DD

**Deciders**: [List of people involved in the decision]

**Technical Story**: [Link to related requirements (REQ-XXX) and change request (CR-YYYY-MM-DD-XXX)]

---

## Context and Problem Statement

[Describe the context and background that led to this decision. What is the issue we're trying to address? What constraints exist? Why is a decision needed now?]

**Example**:
> We need to choose a logging framework for our application. The system will process thousands of log events per second, and we need structured logging with JSON output for integration with our monitoring stack. The framework must be lightweight and performant.

---

## Decision Drivers

[List the factors that influenced the decision. These are the priorities and constraints that guided the choice.]

* [Driver 1 - e.g., Performance requirements]
* [Driver 2 - e.g., Team familiarity]
* [Driver 3 - e.g., Ecosystem compatibility]
* [Driver 4 - e.g., License constraints]
* [Driver 5 - e.g., Operational requirements]

**Example**:
* Must support structured JSON logging
* Must have minimal performance overhead (< 5% CPU)
* Must integrate with OpenTelemetry
* Must have active maintenance and community support
* Team already familiar with Python logging ecosystem

---

## Considered Options

[List all options that were seriously considered. For each option, provide a brief description.]

* **Option 1**: [Name of option 1]
* **Option 2**: [Name of option 2]
* **Option 3**: [Name of option 3]

**Example**:
* **Option 1**: Standard Python `logging` library with JSON formatter
* **Option 2**: `structlog` library
* **Option 3**: `loguru` library
* **Option 4**: Build custom logging solution

---

## Decision Outcome

**Chosen option**: "[Name of chosen option]"

[Explain why this option was chosen. What made it better than the alternatives?]

**Example**:
> **Chosen option**: "structlog library"
>
> We chose structlog because it provides the best balance of performance, features, and ease of use. It offers native structured logging with minimal performance overhead, excellent OpenTelemetry integration, and the team can leverage existing Python logging knowledge while gaining better structure and consistency.

### Consequences

#### Good (Positive Impacts)

* [Positive consequence 1]
* [Positive consequence 2]
* [Positive consequence 3]

**Example**:
* Structured logs will be easier to parse and analyze
* OpenTelemetry integration provides distributed tracing out of the box
* Active community and regular updates ensure long-term maintainability
* Minimal performance overhead measured at < 2% CPU

#### Bad (Negative Impacts)

* [Negative consequence 1]
* [Negative consequence 2]

**Example**:
* Additional dependency to manage
* Learning curve for team members unfamiliar with structured logging
* Migration required for existing logging statements

#### Neutral (Other Impacts)

* [Neutral consequence 1]
* [Neutral consequence 2]

**Example**:
* Requires configuration changes in deployment scripts
* Log aggregation system needs to be configured for JSON parsing

---

## Validation

[How will we measure the success of this decision? What metrics or indicators will tell us this was the right choice?]

**Success Criteria**:
* [Criterion 1]
* [Criterion 2]
* [Criterion 3]

**Measurement Plan**:
* [How will we measure each criterion?]

**Review Date**: [Date to review decision effectiveness]

**Example**:
> **Success Criteria**:
> * Log processing overhead remains < 5% CPU
> * All critical code paths emit structured logs within 2 sprints
> * Zero log-related incidents after migration
> * Developer satisfaction score > 4/5 in retrospective
>
> **Measurement Plan**:
> * Monitor CPU metrics in production for 30 days post-deployment
> * Track code coverage of logging instrumentation
> * Review incident reports for logging-related issues
> * Survey team in sprint retrospectives
>
> **Review Date**: 2026-06-09 (4 months after implementation)

---

## Pros and Cons of the Options

[For each considered option, provide detailed pros and cons]

### Option 1: [Name]

[Brief description of option 1]

**Pros**:
* [Advantage 1]
* [Advantage 2]
* [Advantage 3]

**Cons**:
* [Disadvantage 1]
* [Disadvantage 2]
* [Disadvantage 3]

**Example**:
> ### Option 1: Standard Python `logging` with JSON formatter
>
> Use the built-in Python logging library with a custom JSON formatter.
>
> **Pros**:
> * No additional dependencies
> * Team already familiar with the API
> * Battle-tested and stable
>
> **Cons**:
> * Verbose configuration required
> * Limited structured logging features
> * Manual work to add context to each log call
> * No native OpenTelemetry integration

---

### Option 2: [Name]

[Brief description of option 2]

**Pros**:
* [Advantage 1]
* [Advantage 2]

**Cons**:
* [Disadvantage 1]
* [Disadvantage 2]

---

### Option 3: [Name]

[Brief description of option 3]

**Pros**:
* [Advantage 1]
* [Advantage 2]

**Cons**:
* [Disadvantage 1]
* [Disadvantage 2]

---

## More Information

[Optional section for additional context, links, research, or implementation notes]

**Research Links**:
* [Link to relevant documentation]
* [Link to performance benchmarks]
* [Link to similar decisions in other projects]

**Implementation Notes**:
* [Important details for implementation]
* [Migration considerations]
* [Rollback plan]

**Related Decisions**:
* [Link to related ADR-XXXX]
* [Link to related ADR-YYYY]

**Discussion**:
* [Link to issue or RFC where this was discussed]
* [Key points from discussion]

**Example**:
> **Research Links**:
> * [structlog documentation](https://www.structlog.org/)
> * [Performance comparison benchmark](https://example.com/logging-benchmark)
> * [OpenTelemetry Python integration guide](https://opentelemetry.io/docs/python/)
>
> **Implementation Notes**:
> * Begin with one service as pilot
> * Create wrapper library for common logging patterns
> * Document migration guide for team
> * Plan 2-sprint migration window
>
> **Rollback Plan**:
> * Keep old logging code in place but deprecated for 1 sprint
> * Can revert by removing structlog dependency and un-deprecating old code
> * No data loss risk - logs will continue to flow either way
>
> **Related Decisions**:
> * ADR-0003: Observability strategy
> * ADR-0005: Monitoring and alerting architecture
>
> **Discussion**:
> * Issue #42: Logging strategy RFC
> * Key consensus: Team agreed performance and structure were top priorities

---

## Status History

[Track status changes over time]

| Date | Status | Note |
|------|--------|------|
| YYYY-MM-DD | PROPOSED | Initial proposal |
| YYYY-MM-DD | ACCEPTED | Approved by architecture team |

**Example**:
| Date | Status | Note |
|------|--------|------|
| 2026-02-01 | PROPOSED | Initial proposal after logging issues in production |
| 2026-02-05 | ACCEPTED | Approved by architecture team after benchmark review |

---

## Template Version

**MADR Template Version**: 3.0.0  
**Repository Version**: 1.0.0

---

## Notes for Template Users

**Before submitting your ADR**:
- [ ] Replace all `[bracketed placeholders]` with actual content
- [ ] Delete example text in gray quotes
- [ ] Remove this "Notes for Template Users" section
- [ ] Update the date to current date
- [ ] Set status to PROPOSED
- [ ] Ensure all sections are filled out (or explicitly marked N/A)
- [ ] Link to relevant requirements (REQ-XXX)
- [ ] Link to change request (CR-YYYY-MM-DD-XXX)
- [ ] Add to PR with code changes

**Tips for writing good ADRs**:
- Be concise but complete
- Focus on the "why" not just the "what"
- Include enough context for future readers
- Document alternatives to show you considered options
- Make consequences explicit
- Define how you'll validate the decision
- Keep it readable - use clear language

**When to write an ADR**:
- Introducing new technology or framework
- Changing system architecture
- Making a decision with long-term impact
- Choosing between multiple valid approaches
- Setting a precedent for future work

**When NOT to write an ADR**:
- Trivial implementation details
- Following existing patterns
- Temporary/experimental changes
- Bug fixes (unless they reveal architectural issue)

---

**End of ADR Template**
