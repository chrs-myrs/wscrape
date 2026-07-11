---
name: hunt
spec: specs/hunt.spec.md
description: |
  Needle-hunting for hard-to-find evidence on the web, with defensible negatives.
  For questions that plain search gives up on too early: obscure people, dead
  communities, era-shifted vocabulary, planted-absent verification. Drives
  wscrape (search, scrape, gather, longtail, cdx, probe) via Bash — never a
  loop-orchestration engine, just a validated prompt plus honesty conventions.

  USE hunt FOR:
  - "did anyone ever...", "does evidence exist that...", "find the person who..."
  - Pre-2010 / dead-forum / tribal-vocabulary topics
  - Cases where you need to defensibly report "not found" to a colleague
  - Anything wscrape's plain search bounced off after a couple of tries
---

# hunt

A needle-hunt finds hard-to-find evidence on the web and, when nothing turns
up, produces a negative result someone else can trust. It is a prompt plus a
small set of artefact conventions — **not** a loop, not a state machine, not
a swarm. Validation testing showed a frontier
agent with a one-page hunt prompt already does HyDE naming, vocabulary
re-anchoring, and pivot mining unprompted, and even invented a CDX-based
archive read path mid-hunt with no scaffolding telling it to. Judgement
carries the hunt. This skill's job is to package that judgement with enough
convention that the negative result at the end is defensible.

## The hunt prompt

This is the core of the skill. Hold it in mind for the whole hunt, not just
the opening move.

> You are on a needle-hunt: find hard-to-find evidence on the web. Use ONLY
> the `wscrape` CLI via Bash. Hunt hard: reformulate queries, try alternative
> vocabulary (imagine what insiders call the thing, and what it was called in
> earlier eras), follow leads from partial hits, mine every hit for pivots
> (names, handles, jargon, product codes, dates), check niche communities.
> Persist — do not give up after a few searches.

Four moves that keep a hunt from stalling, named so you reach for them
deliberately rather than by luck:

- **HyDE naming.** Before searching, write the document that would exist if
  the thing you're hunting were documented — in several voices (a forum post,
  a changelog entry, an academic abstract, a product page). Search the
  distinctive phrases you just wrote, not just the question. This surfaces
  vocabulary you wouldn't have guessed cold.
- **Person-sweep.** Identify who would know — the moderator, the maintainer,
  the person who gave the talk, the one who answered every thread on this for
  years. Sweep their output across surfaces with `wscrape longtail --author
  <handle>` (HN Algolia `tags=author_<handle>`, Discourse
  `/u/<handle>/activity.json`; Marginalia has no author endpoint and is
  skipped in this mode). DBLP has no dedicated author endpoint either —
  search the person's name as a normal query. Otherwise, site-scoped search
  on their handle. Every hunt that breaks open usually breaks on a person,
  not a query.
- **Era-shifted vocabulary.** Names change by decade. What is this called now,
  what was it called ten and twenty years ago, what did the community that
  used it call themselves? For dead domains and pre-2010 surfaces, use
  `wscrape cdx <domain>` to find archived snapshots a live search can't reach.
- **Area-scan.** A hit in a forum, blog, or mailing list is a neighbourhood,
  not an endpoint. Scan the author's other posts, the thread's siblings, the
  blogroll, the "related threads" rail. The pivot is usually one click away
  from the hit that felt like a dead end.

Reach for `wscrape longtail` (federated Marginalia + Discourse + HN Algolia)
when the target is plausibly a forum post, niche blog, or technical
discussion rather than an indexed mainstream page — it is built for exactly
this recall gap. Use `wscrape search`, `scrape`, and `gather` as normal
(see `skills/wscrape/SKILL.md`) for everything else in the toolkit.

## Rhythm

Work in bursts, not a continuous stream:

1. **Burst** — run 5–10 probes via `wscrape probe "<query>" [...] --hunt-id
   <id> --engines <engine[,engine...]>` (`--engines` is required; pick from
   `ddg,marginalia,hn,discourse,scholar,dblp,openaire,ntrs`). Multiple
   queries can be batched in one call. Every probe carries the hunt-id so it
   lands in the ledger automatically — this is what makes the eventual
   certificate defensible. Don't run ad-hoc `wscrape search` calls outside
   `probe` once a hunt is under way; untracked probes are invisible to the
   certificate.
2. **Attest** — the ledger write happens as a side effect of `probe` itself.
   Nothing to do here except not bypass it.
3. **Digest** — read back what the burst found. Update the coverage grid and
   the clue board (below). Decide what pivoted open and what dead-ended.
4. **Pivot-or-park** — either the burst opened a new vocabulary/person/era
   lead (pivot, start another burst) or it didn't (park: write a checkpoint
   and either continue with a genuinely different angle or stop).

There is no daemon and no scheduler. A hunt that spans days is just this
loop re-invoked — by you, by `/loop`, or by a cron re-run of `/hunt resume
<id>` — reading the checkpoint each time. The checkpoint file is the pacing
mechanism; nothing runs unattended.

## Artefact conventions

All artefacts for a hunt live under `var/hunt/<id>/`. Use a short slug for
`<id>` (e.g. `20260711-n64-linux`). These conventions are contractual — they
are what makes a "not found" defensible later, so don't improvise around
them.

| Artefact | Author | Lifecycle |
|---|---|---|
| `var/hunt/<id>/probes.jsonl` | **Tool** (`wscrape probe` writes it) | Append-only. Never hand-edit. Kept forever — it's the audit trail. |
| `var/hunt/<id>/clueboard.md` | **Skill** (you write it) | Working memory: hypotheses, pivots tried, current best guess. Dies with the hunt. **Never auto-loaded into a future hunt** — a fresh hunt starts from the question, not from an old hunt's interpretation of it. |
| `var/hunt/<id>/checkpoint.md` | **Skill**, written at every pause | Re-anchoring point. `/hunt resume <id>` reads checkpoint + `probes.jsonl` (never the clue board) to pick the hunt back up. |
| `var/hunt/<id>/certificate.md` | **Skill**, rendered from the ledger | Written once, at hunt close, only on a negative result. See below. |
| `registries/gazetteer.md` (or `gazetteer.md` at project root if the project has no `registries/` directory — one project-level file, not per-hunt) | **Skill**, appended at hunt close | Facts only, forever. See Gazetteer below. |

### Coverage grid

Kept inside `checkpoint.md` (and reproduced in the certificate). A grid over
**surface × vocabulary-cluster × era**. Each cell has:

- **State** — `searched-verified`, `searched-unverified`, or `unsearched`.
  Derived from the ledger's canary data, not from memory: a probe against a
  surface whose canary failed is `searched-unverified` regardless of what it
  returned, because you can't tell a genuine empty from a silently broken
  adapter.
- **Cause** (when the cell is a blank) — `wrong-vocab`, `dead-surface`, or
  `genuine-absence`. This is the skill's judgement call, not something the
  ledger can tell you — record your reasoning, not just the label.

One file, two authors: the ledger supplies state, you supply cause.

## Stopping rule

Stop the hunt when **the last two vocabulary restarts add nothing new to the
grid** — no cell moves from unsearched to searched, no new pivot (person,
term, era) surfaces. When you stop, say explicitly which rule ended the
hunt: found the needle, hit the stopping rule (name it — "two restarts, no
new cells"), or parked pending a specific input (e.g. "waiting on archive.org
rate limits to clear" or "waiting on a human reply").

## Negative-results certificate

On a blank, **always** render `var/hunt/<id>/certificate.md` from
`skills/hunt/certificate-template.md`, populated from the ledger — never
from memory of the hunt. If you can't point to the ledger line that backs a
claim in the certificate, don't make the claim. Required contents:

1. **The question operationalised** — what would have counted as a hit, stated before the verdict.
2. **The coverage grid**, with canary status per cell.
3. **Probe count, date range, and a pointer to `probes.jsonl`.**
4. **Verbatim queries** — embed the actual query strings, not paraphrases. A summary that says "I searched for X" without the exact string is not colleague-showable.
5. **A not-searched register** — every surface/era/vocabulary cluster you didn't cover, with a reason. Always include the era clause when pre-2010 surfaces weren't reached with `wscrape cdx`: "pre-2010 web: unsearched (archive read path not exercised for this hunt)".
6. **The stopping rule invoked.**
7. **Named humans who would know**, with a drafted outreach approach — recommend contacting them, never send anything yourself.
8. **A plain-language summary** a colleague can read without the ledger open.
9. **Spot-check instructions** — "re-run these five probes yourself" — pick five representative queries from the ledger so the reader can independently verify the blank in minutes.

## Gazetteer

At hunt close, append any verifiable era-vocabulary crosswalks you turned up
to the project-level gazetteer — `registries/gazetteer.md`, or `gazetteer.md`
at the project root if the project has no `registries/` directory (e.g.
"pre-2005 term for X was Y — source: `<url>`"). One line per entry, always
with a source. This file is **facts-only, forever**: entries without a
citation get deleted on sight, because an uncited "fact" is just a stale
hypothesis wearing a lab coat. The gazetteer may be consulted at the start of
a hunt for candidate vocabulary — it never marks a grid cell as searched; it
can only suggest what to search for.

## Anti-patterns

- **Never assert a negative from a surface whose canary failed.** An
  `UNVERIFIED` surface is not evidence of absence — it's evidence you don't
  know.
- **Never write the certificate from memory.** If the ledger doesn't back
  it, it doesn't go in the certificate.
- **Never auto-load a previous hunt's clue board.** It's the rejected corpus
  reborn as interpretation — anchoring bias with a filing system.
- **Never send outreach.** Draft the approach, name the person, stop there.
- **Never invent a probability.** No Bayesian arithmetic, no invented
  priors, no "posterior: 8%". The coverage grid with stated causes is the
  honest artefact; a number with decimals is decoration wearing a lab coat.
- **Never build loop orchestration.** If a hunt needs a state machine to
  function, that's evidence the judgement has left the skill — stop and
  reconsider before adding scaffolding.
