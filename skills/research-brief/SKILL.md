---
name: research-brief
description: Create portable, structured research briefs through guided clarification. Planning only -- never execute research during brief creation.
---


# Research Brief Command

Create portable, structured research briefs through guided clarification. Planning only -- never execute research during brief creation.

## Core Behaviour

Separate research planning from execution:
- Clarify before generating (eliminate assumptions)
- Produce dual-format output (YAML frontmatter + human-readable sections)
- Bound every brief with explicit scope and question limits
- Make briefs portable -- they work when pasted into any AI tool

## Workflow

### Phase 1: Parsing

Extract topic and detect research type from the user's input:

| Type | Signals | Focus |
|------|---------|-------|
| Technical | how to, implementation, library, API | Capabilities, patterns, code |
| Competitive | competitors, market, vs, compare | Players, features, positioning |
| Market | market, trend, opportunity, growth | Size, segments, drivers |
| Literature | research, studies, evidence, papers | Academic findings, best practices |
| General | (default) | Mixed appropriate focus |

**Type detection rules**:
- Default to **technical** when ambiguous
- Architecture topics: technical with scalability focus

Announce: `[PARSING] -> Topic: {topic} -> Detected type: {type} -> Complexity: {simple|moderate|complex} ({rationale})`

### Phase 2: Clarification [GATE:required: user must answer clarifying questions before brief generation]

Ask clarifying questions to eliminate ambiguity. Adapt question count to complexity:
- **Simple** (single-domain, obvious type): 2-3 questions
- **Complex** (multi-domain, ambiguous): 4-5 questions

```
Question 1: Scope (always ask)
Header: "Scope"
Question: "What specifically about [topic] do you want to research?"
Options:
- [Detected focus 1] - Most likely interpretation
- [Detected focus 2] - Alternative angle
- [Broader] - Multiple aspects
```

```
Question 2: Depth (always ask)
Header: "Depth"
Question: "How deep should this research go?"
Options:
- "Quick overview" - 3-5 sources, surface level
- "Balanced coverage" - 8-15 sources [Default]
- "Deep dive" - 15+ sources, comprehensive
```

```
Question 3: Key Questions (complex topics, multi-select)
Header: "Priority"
Question: "Which questions matter most?"
Options: [multi-select from 5-7 inferred questions]
```

```
Question 4: Sources (complex/specialised)
Header: "Sources"
Question: "Any source preferences?"
Options:
- "No preference" - Let me decide
- "Official/authoritative" - Docs, specs, standards
- "Practical/experiential" - Blogs, case studies, production experience
- "Specific" - I'll name them
```

```
Question 5: Output Format (complex topics)
Header: "Format"
Question: "What format for findings?"
Options:
- "Summary" - Narrative overview
- "Comparison matrix" - Side-by-side table
- "Implementation guide" - Step-by-step actionable
```

**GATE**: Cannot generate brief until all required questions are answered and scope is bounded.

### Phase 3: Brief Generation

Generate the brief in dual format. The frontmatter contains machine hints; the body is human-readable.

**Search query hints**: Generate 3-5 specific search queries. Always include `-medium.com` in domain exclusions. Prefer engineering blogs and official docs.

Structure:
```markdown
---
id: {YYYYMMDD}-{HHMMSS}-{slug}
type: research-brief
research_type: competitive|technical|market|literature|general
created: {ISO-8601}
hints:
  queries: ["query 1", "query 2", "query 3"]
  domains: ["preferred1.com", "-medium.com"]
  depth: shallow|moderate|deep
---

# Research Brief: {Topic}

## Objective
What we're trying to learn (1-2 sentences, specific and actionable).

## Scope
- **In scope**: What to include
- **Out of scope**: What to exclude
- **Timeframe**: If relevant

## Key Questions
1. Specific question (3-7 max, never more)
2. Another question

## Source Guidance
- Preferred source types
- Sources to avoid
- Credibility requirements

## Output Format
What the deliverable should look like.

## Notes
Additional context (optional).
```

### Phase 4: Persistence

Save the brief to `var/research/briefs/{id}.md` and confirm the path.

### Phase 5: Next Steps

After saving, present execution options: `/research {id}` to execute locally, copy to ChatGPT Deep Research for external execution, share with team, or edit the brief file directly.

## Anti-Patterns

**NEVER**:
- Execute research during brief creation (no searching, no scraping)
- Accept vague objectives like "learn about X" (force specificity)
- Allow unbounded scope (always define out-of-scope)
- Exceed 7 key questions (forces prioritisation)
- Skip the clarification gate
- Generate hints without domain exclusions
- Combine brief creation with brief execution in one session

## Failure Recovery

- **Vague topic**: Ask for specific angle before proceeding to clarification
- **Too broad**: Suggest splitting into multiple briefs
- **User skips questions**: Explain gate requirement, apply sensible defaults for skipped optional questions
- **Ambiguous type**: Default to technical, note the assumption

## Policy Emphasis

- **msl-minimalism**: Briefs capture the essential what, not how. Every question must justify its inclusion
- **clean-project**: All briefs persist to var/research/briefs/, no orphaned output
- **spec-driven**: Brief structure adapts to detected research type
- Dual format ensures portability across tools and teams
- Clarification phase prevents wasted research effort
