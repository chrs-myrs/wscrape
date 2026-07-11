<!--
Certificate template for a hunt negative result.
Render this from var/hunt/<id>/probes.jsonl (and checkpoint.md's coverage
grid) — never from memory. Every claim below must trace to a ledger line.
Delete this comment block when rendering the real certificate.
-->

# Negative-results certificate — <id>

**Hunt closed:** <date>
**Ledger:** `var/hunt/<id>/probes.jsonl` (<N> probes, <first-date> to <last-date>)

## 1. The question, operationalised

**Question asked:** <the question as posed>

**What would have counted as a hit:** <state explicitly, before the verdict,
what kind of evidence — a name, a document, a thread, a dated post — would
have resolved this to FOUND. If this wasn't written down before the hunt
started, reconstruct it honestly and say so.>

## 2. Verdict

**<FOUND / NOT FOUND / INCONCLUSIVE — pick one>**

<One-paragraph plain-language summary a colleague can read without opening
the ledger: what was hunted, what was and wasn't found, and how confident
the negative is.>

## 3. Coverage grid

Surface × vocabulary-cluster × era. State from the ledger's canary data;
cause is judgement.

| Surface | Vocabulary cluster | Era | State | Cause (if blank) |
|---|---|---|---|---|
| <e.g. HN Algolia> | <e.g. modern jargon> | <e.g. 2015–present> | <searched-verified / searched-unverified / unsearched> | <wrong-vocab / dead-surface / genuine-absence / — > |
| ... | ... | ... | ... | ... |

## 4. Probes run (verbatim)

<Embed the actual query strings — not paraphrases. List all, or if long,
list all and mark the five spot-check probes (section 7).>

| # | Surface | Query (verbatim) | Outcome | Canary |
|---|---|---|---|---|
| 1 | <surface> | `<verbatim query>` | <ok / empty / timeout / blocked> | <verified / unverified> |
| ... | | | | |

## 5. Not-searched register

Everything deliberately or unavoidably left uncovered, with a reason.
**Always include the era clause** if pre-2010 surfaces weren't reachable.

| Not searched | Reason |
|---|---|
| <e.g. pre-2010 web> | <e.g. no archive read path available for this hunt / CDX not yet triggered> |
| <e.g. surface X> | <e.g. canary failed all session, excluded rather than reported as a false negative> |
| ... | ... |

## 6. Stopping rule invoked

<Name exactly which rule ended the hunt: "found the needle" / "two
vocabulary restarts added nothing new to the grid" / "parked pending
<specific input>". Do not leave this vague.>

## 7. Spot-check: re-run these five probes

A reader who doesn't want to open the ledger can verify the blank by
re-running these five representative queries themselves:

1. `<verbatim query>` — via `wscrape <command> ...`
2. `<verbatim query>` — via `wscrape <command> ...`
3. `<verbatim query>` — via `wscrape <command> ...`
4. `<verbatim query>` — via `wscrape <command> ...`
5. `<verbatim query>` — via `wscrape <command> ...`

## 8. Who would know

Named humans who plausibly have the answer, and a drafted (not sent)
approach for each. **Recommend outreach — never send it.**

| Person / handle | Why they'd know | Drafted approach |
|---|---|---|
| <name/handle> | <e.g. moderated the forum in question era> | <e.g. "Draft: a short message to X asking whether Y was ever documented, linking to what we found adjacent to it."> |
| ... | ... | ... |

## 9. Notes for the gazetteer

Any verifiable era-vocabulary crosswalks surfaced during this hunt, to be
appended to the project gazetteer (facts with citations only):

- <e.g. "pre-2005 term for X was Y" — source: `<url>`>
