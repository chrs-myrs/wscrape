---
name: research
description: Execute research briefs systematically using wscrape. Every finding needs sources, every claim needs evidence, every gap needs honesty.
---


# Research Command

Execute research briefs systematically using wscrape. Every finding needs sources, every claim needs evidence, every gap needs honesty.

## Core Behaviour

Follow brief-driven research methodology:
- Always work from defined questions (brief or inline)
- Every finding attributed to sources
- Match effort to depth setting
- Preserve raw evidence for verification
- Acknowledge gaps over fabricating completeness

## Workflow

### Phase 1: Brief Loading [GATE:required: user must provide a brief-id or topic]

Determine research scope from user input:

**If brief-id provided** (e.g., `20260126-163012-react-state-management`):
- Load brief from `var/research/briefs/{brief-id}.md`
- Extract questions, depth, type, and constraints
- Confirm brief loaded with summary

**If topic string provided** (e.g., `research best practices for error handling`):
- Create inline brief: derive 3-5 focused questions from topic
- Set default depth to `moderate`
- Present derived questions for confirmation

Display brief summary:
```
[BRIEF LOADED]
> Topic: {topic}
> Type: {type}
> Depth: {shallow|moderate|deep}
> Questions: {count}
> Q1: {first question}
> Q2: {second question}
> ...
```

**GATE**: Cannot proceed without a brief (loaded or generated).

### Phase 2: Search Planning

Plan search strategy before executing:
- Map each question to 2-3 search queries
- Identify target domains (prefer engineering blogs, official docs)
- Note domain exclusions if relevant

```
[PLANNING SEARCHES]
> Q1 "{question}" -> {n} queries
> Q2 "{question}" -> {n} queries
> ...
> Target domains: {preferred sources}
```

### Phase 3: Source Collection

Execute searches and collect sources using wscrape:

1. **Search first**: Use wscrape search to find candidate sources
2. **Filter**: Identify relevant results (skip low-quality, duplicates)
3. **Scrape selectively**: Deep-read only promising sources
4. **Stop when confident**: Do not over-collect once questions are answered

Calibrate effort to depth setting:

| Depth | Sources | Approach |
|-------|---------|----------|
| shallow | 3-5 | Quick answers, top results only |
| moderate | 8-15 | Balanced coverage, verify key claims |
| deep | 15+ | Comprehensive, multiple perspectives |

```
[COLLECTING SOURCES]
> Search 1: {n} results, {m} relevant
> Search 2: {n} results, {m} relevant
> Scraping {total} sources...
> Evidence saved to var/research/results/{brief-id}/evidence/
```

**Tool constraint**: Use wscrape for all web search and scraping. Do NOT use other research tools.

### Phase 4: Synthesis [GATE:required: sources must be collected before synthesis]

Answer each question from the brief:
- Synthesize across sources, do not just summarise one
- Include code examples when relevant (technical research)
- Assign confidence per finding:
  - **High**: Multiple corroborating sources, consistent information
  - **Medium**: Few sources or some contradictions
  - **Low**: Single source, anecdotal, or extrapolated
- Note where sources disagree

**GATE**: Cannot synthesise without collected sources.

### Phase 5: Documentation

Produce results in this structure and save to `var/research/results/{brief-id}/results.md`:

```markdown
---
brief_id: {original-brief-id}
executed: {ISO-8601}
tool: wscrape
sources_checked: {N}
---

# Research Results: {Topic}

## Summary
Executive summary of findings (3-5 sentences).

## Findings by Question

### Q1: {Question from brief}
**Answer**: Synthesized answer with context.
**Sources**: [Source 1](url), [Source 2](url)
**Confidence**: High|Medium|Low

### Q2: {Next question}
...

## Sources Consulted
| Source | URL | Relevance |
|--------|-----|-----------|
| Title | url | High/Med/Low |

## Gaps & Limitations
- What couldn't be determined
- Questions not fully answered
- Source limitations
```

### Phase 6: Persistence

Save all outputs:
- `var/research/results/{brief-id}/results.md` -- synthesised findings
- `var/research/results/{brief-id}/evidence/` -- raw scraped content

Create directories if they do not exist. Report saved locations:
```
> Results: var/research/results/{brief-id}/results.md
> Evidence: var/research/results/{brief-id}/evidence/ ({n} files)
```

### Phase 7: Presentation

Display the executive summary and key findings inline. Point user to the full results file for detail.


## Anti-Patterns

**NEVER**:
- Research without defined questions (always have a brief)
- Present findings without source attribution
- Ignore the brief's depth setting
- Claim high confidence without multiple corroborating sources
- Expand scope beyond what the brief defines
- Use tools other than wscrape
- Over-collect sources when confident answers are already found
- Fabricate or hallucinate sources

## Failure Recovery

- **Brief not found**: Ask user to confirm brief-id or create inline brief from topic
- **wscrape unavailable**: Report tool unavailability, do not fall back to unverifiable answers
- **Insufficient sources**: Report honestly in Gaps section, lower confidence ratings
- **All questions unanswered**: Document what was searched and why it failed, suggest refined queries

## Integration Points

- **Before research**: `/research-brief` to create or refine a brief

## Policy Emphasis

- **evidence-first**: Every claim linked to a source, confidence honestly assessed
- **clean-project**: Results organised in var/research/, evidence preserved, no scattered files
- **msl-minimalism**: Thorough but focused -- answer the questions, do not write a thesis
