---
name: wscrape
spec: specs/wscrape.spec.md
description: |
  wscrape handles all web operations: search, page scraping, site crawling,
  and URL discovery. Self-hosted, no subscription, no API key required.

  USE wscrape FOR:
  - Web, image, and news search
  - Research, investigation, fact-checking
  - Reading pages, docs, articles, documentation
  - "check the web", "look up", "find online", "search for", "research"
  - Content extraction, URL discovery, site crawling
  - Any URL without a dedicated CLI (see URL Routing below)

  wscrape is the default for URLs without a dedicated CLI.
  Replaces WebFetch and WebSearch entirely.
  Spec: specs/wscrape.spec.md
tools: [Bash, Read]
---

# wscrape

Self-hosted web scraping CLI. Uses trafilatura (static) + crawl4ai/Playwright
(JS-heavy) for scraping, DuckDuckGo for search. No API key. No credits.

## Tool exclusivity

**NEVER use WebSearch or WebFetch native tools.** wscrape replaces both entirely.
If WebSearch/WebFetch are available in context, ignore them — always use `wscrape` via Bash.

Any skill that needs web operations (research, etc.) MUST route through wscrape, not native tools.

## URL Routing

Before scraping a URL, check if a native CLI handles it better:

| URL pattern | Use instead | Examples |
|---|---|---|
| `github.com/*` | `gh` CLI | `gh repo view`, `gh issue view`, `gh pr view`, `gh api` |
| `npmjs.com/*` | `npm view <pkg>` | `npm view react versions`, `npm view express` |
| `pypi.org/*` | `pip show <pkg>` | `pip show requests`, `pip index versions flask` |
| `crates.io/*` | `cargo info <crate>` | `cargo info serde` |
| `reddit.com/*` | `wscrape reddit "<query>" --search` | Prefer `--search` (works any IP); URL/comment fetch is 403-blocked from data-centre IPs |
| `youtube.com/*`, `youtu.be/*` | `wscrape transcript <url>` | Extract video transcript/subtitles |
| `hub.docker.com/*` | `docker search` | `docker search nginx`, `docker manifest inspect` |

**Override**: Use wscrape for routed domains when the CLI can't provide the needed data (e.g., GitHub Pages sites, rendered HTML, READMEs with images, detailed package docs beyond metadata).

## Workflow

Follow this escalation:

1. **search** — no specific URL? Start here.
2. **scrape** — have a URL, want its content.
3. **map + scrape** — large site, need a specific subpage. Map to find URL, then scrape.
4. **crawl** — need bulk content from an entire section.
5. **gather** — have a *question*, not a URL list. Adaptively crawls from a start URL until it has enough to answer the query.
6. **scholar** — searching *academic literature*? Federates 7 keyless engines (Crossref, arXiv, Europe PMC, OpenAIRE, NTRS, DBLP, OSF) into one ranked, deduplicated result set. No URL needed.
7. **news** — searching *news articles*? Federates GDELT (and optional Google News) into one recency-ranked, deduplicated set.
8. **longtail** — hunting the *small web/communities* (forums, niche blogs, HN) rather than mainstream-indexed pages? Federates Marginalia + Discourse + HN Algolia.
9. **cdx** — need *historical* captures of a URL/domain (dead pages, pre-2010 web)? Enumerates Wayback (or Common Crawl) captures; `--fetch` pulls and extracts the top snapshots.

## Output directory

Always use `var/wscrape/` in the project working directory. Use `-o` to write to file.
`var/` is gitignored by convention — no need to add anything to `.gitignore`.

```bash
# Search
wscrape search "query" -o var/wscrape/search-query.json
wscrape search "query" --limit 10 -o var/wscrape/search-query.json
wscrape search "local events" --region uk-en --recent m   # anchor locale + past month (cuts noise)

# Scrape single page (returns boilerplate-stripped content by default)
wscrape scrape https://example.com -o var/wscrape/example.md
wscrape scrape https://example.com --js -o var/wscrape/example.md
wscrape scrape https://example.com --raw -o var/wscrape/example.md    # full page, no stripping
wscrape scrape https://example.com --query "pricing tiers" -o var/wscrape/example.md  # BM25 passages
wscrape scrape https://arxiv.org/pdf/2301.00234 -o var/wscrape/paper.md  # PDFs handled transparently (pypdf)

# URL discovery
wscrape map https://example.com -o var/wscrape/urls.txt
wscrape map https://example.com --search "auth" -o var/wscrape/auth-urls.txt
wscrape map https://example.com --seed sitemap --limit 100 -o var/wscrape/urls.txt  # sitemap/CC discovery

# Bulk crawl (native deep-crawl)
wscrape crawl https://docs.example.com -o var/wscrape/crawl.json
wscrape crawl https://docs.example.com --limit 50 --depth 3 -o var/wscrape/crawl.json
wscrape crawl https://docs.example.com --include /docs,/api -o var/wscrape/crawl.json
wscrape crawl https://docs.example.com --keywords "auth,oauth,token" -o var/wscrape/crawl.json  # crawl toward relevance

# Gather — answer a question by adaptive crawl
wscrape gather https://docs.example.com --query "how does token refresh work" -o var/wscrape/gather.md
wscrape gather https://docs.example.com --query "rate limits" --limit 15 --json -o var/wscrape/gather.json

# Scholar — academic literature (federated, keyless)
wscrape scholar "diffusion models for image generation" --limit 10 -o var/wscrape/papers.md
wscrape scholar "mRNA vaccine" --since-year 2023 --open-access --json -o var/wscrape/papers.json

# News — news articles (GDELT by default, keyless)
wscrape news "interest rate cuts" --recent w --limit 10 -o var/wscrape/news.md
wscrape news "central bank policy" --hydrate --limit 8 -o var/wscrape/news.md   # add real snippets

# Longtail — small web / communities (Marginalia + Discourse + HN Algolia, keyless)
wscrape longtail "vim macro recipes" --limit 10 -o var/wscrape/longtail.md
wscrape longtail "n64 linux port" --engines hn,discourse -o var/wscrape/longtail.md  # narrow engines
wscrape longtail someuser --author someuser --engines hn,discourse -o var/wscrape/author.md  # sweep a person's output (query is required but ignored in --author mode)

# CDX — historical-web captures (Wayback CDX; optional Common Crawl)
wscrape cdx example.com --limit 20 -o var/wscrape/cdx.md
wscrape cdx https://example.com/old-page --from 2005 --to 2010 -o var/wscrape/cdx.md
wscrape cdx example.com --fetch 3 -o var/wscrape/cdx-snapshots.md   # fetch + extract top 3 snapshots
wscrape cdx example.com --cc -o var/wscrape/cc.md                  # query Common Crawl instead

# Probe — attested batch probing (used by the /hunt skill; JSONL ledger as a side effect)
wscrape probe "obscure forum topic" --engines hn,marginalia --hunt-id 20260711-example --limit 5
```

### Fetch flags (scrape, map, crawl)

| Flag | Effect |
|---|---|
| `--raw` | Return full page content instead of boilerplate-stripped (scrape, crawl) |
| `--query` | Return only passages relevant to the query, via BM25 (scrape, crawl) |
| `--keywords` | Crawl *toward* relevant pages using relevance scoring (crawl only) |
| `--seed` | Discover URLs via sitemap/Common Crawl: `sitemap`, `cc`, `sitemap+cc` (map only) |
| `--magic` | Auto-dismiss cookie/consent overlays; uses the browser path (scrape, crawl) |
| `--scroll` | Scroll to load lazy / infinite-scroll content; uses the browser path (scrape, crawl) |
| `--cache` | Use crawl4ai's cache for speed on repeat fetches |
| `--fresh` | Bypass the cache and always fetch (this is the **default**) |
| `--robots` | Respect the site's robots.txt |

Search accepts `--region` (e.g. `uk-en`) and `--recent` (`d`/`w`/`m`/`y`) to
anchor locale and freshness — use them to cut noise on generic or dated queries.

By default `scrape`/`crawl` strip navigation, footers, and boilerplate for higher
signal density. Use `--raw` when you need the complete page (footnotes, sidebars,
disclaimers). If stripping collapses the content, wscrape auto-falls-back to the
full page and logs a notice to stderr.

## Reading output files

Never read entire wscrape output files at once — they can be large.

```bash
# Check size and preview
wc -l var/wscrape/file.md && head -50 var/wscrape/file.md

# Find specific content
grep -n "keyword" var/wscrape/file.md
grep -A 10 "## Section" var/wscrape/file.md
```

## Parallelisation

Run independent scrapes in parallel:

```bash
wscrape scrape https://site1.com -o var/wscrape/1.md &
wscrape scrape https://site2.com -o var/wscrape/2.md &
wait
```

## Academic search (scholar)

`scholar` federates **7 keyless engines** — **Crossref** (cross-publisher backbone), **arXiv** (preprints), **Europe PMC** (biomedical), **OpenAIRE** (grey literature — reports/theses), **NTRS** (NASA technical reports), **DBLP** (CS bibliography — no abstracts), **OSF Preprints** (title-substring search only, no authors) — merges them with reciprocal rank fusion, deduplicates by DOI (falling back to arXiv id/PMID/title), and surfaces citation counts where available. No API key required.

```bash
wscrape scholar "<query>" [--limit N] [--since-year YYYY] [--open-access] [--json]
```

- Markdown digest by default (title, authors, year, venue, citations, DOI/URL, abstract); `--json` emits structured records for programmatic use.
- A **coverage line on stderr** reports which engines answered, failed, or were skipped — read it to judge recall confidence (e.g. `crossref ok (10)  arxiv ok (10)  europepmc ok (8)  openaire ok (6)  ntrs ok (0)  dblp ok (4)  osf ok (2)`).
- Prefer `scholar` over `search` for papers, DOIs, citations, and literature reviews — it returns typed, deduplicated academic records rather than noisy web hits.
- **Honesty notes**: DBLP exposes no abstracts; NTRS has no journal venue, so report type/numbers are folded into the venue field; OSF's keyless search is title-substring only (no full-text query param) and returns no author list.

**Optional keyed engines** — OpenAlex and Semantic Scholar join the federation automatically when an API key is available; otherwise they're silently skipped and scholar works fully keyless.


## News search (news)

`news` federates news sources into one recency-ranked, deduplicated set. **GDELT 2.0** (keyless, global, 65 languages, ~3-month window) is the default workhorse. No API key required.

```bash
wscrape news "<query>" [--limit N] [--recent d|w|m|y] [--google-news] [--hydrate] [--json]
```

- Prefer `news` over `search` for current events, headlines, and press coverage — it returns typed, deduplicated articles ranked newest-first.
- GDELT returns title, outlet, date, and URL but **no snippet body**. Add `--hydrate` to fetch the top results and attach real snippets (bounded, so it stays cheap).
- **`--google-news`** additionally queries Google News RSS. Its terms permit **personal, non-commercial use only** — wscrape prints that caveat to stderr; keep it off when results may inform work product. Its `rss/articles/…` links can't be resolved without a browser, so `--hydrate` skips them.
- A **coverage line on stderr** reports which engines answered (GDELT rate-limits to ~1 request/5s, so an occasional `gdelt failed: HTTP 429` is normal — retry shortly).

**Known limitations**
- **GDELT may be unreachable on some networks** (data-centre / restricted egress → `gdelt failed: ConnectTimeout`). When that happens, `news` runs Google-News-only — still useful, but Google News is personal-use licensed, so prefer GDELT for work product where you can reach it.
- **Google News URLs are encrypted redirect stubs** (`news.google.com/rss/articles/…`) that can't be opened directly (they hit a consent wall). `--hydrate` resolves them by searching the headline and matching the source domain, then scrapes the real page for a snippet — so **use `--hydrate` whenever you need to actually read Google-News-sourced articles**, not just list them. Unresolvable stubs are reported on stderr.

## Small-web / community search (longtail)

`longtail` federates keyless small-web/community engines — **Marginalia** (small-web index), **Discourse fan-out** (a curated set of large public forums, one adapter covers thousands of instances), **HN Algolia** — for topics mainstream search under-indexes: forums, niche blogs, dead(ish) communities, HN threads. No API key required.

```bash
wscrape longtail "<query>" [--limit N] [--engines marginalia,discourse,hn] [--instances host1,host2] [--author <handle>] [--json]
```

- Reach for `longtail` over `search` when the target is plausibly a forum post, niche blog, or technical discussion rather than an indexed mainstream page.
- `--author <handle>` sweeps a person's own output instead of searching a term — HN via `tags=author_<handle>`, Discourse via `/u/<handle>/activity.json`. Marginalia has no author endpoint and is skipped in this mode (reported on stderr).
- `--instances` overrides the default Discourse roster; each instance is federated and reported individually on stderr, so one dead instance never hides the others.

## Historical-web captures (cdx)

`cdx` enumerates historical captures of a URL/domain via the Wayback CDX server (or a Common Crawl index with `--cc`). It is **URL-in, captures-out** — there is no keyless full-text search over archived content, so use it once you have a target, not to discover one.

```bash
wscrape cdx <url-or-domain> [--match exact|prefix|host|domain] [--from YYYY[MMDD]] [--to YYYY[MMDD]] [--filter field:regex] [--collapse field] [--limit N] [--cc [CRAWL-ID]] [--fetch [N]] [--json]
```

- `--cc` (bare, or with a crawl id like `CC-MAIN-2026-25`) queries Common Crawl instead of Wayback; bare `--cc` resolves the newest crawl automatically. `--cc` takes precedence over `--base`.
- `--fetch [N]` (Wayback only, default 3, cap 10) fetches and extracts the top N snapshots — paced politely (archive.org throttles hard); per-snapshot failures are reported, not fatal.
- Useful for dead links, pre-2010 topics, and person-sweeps that turn up a defunct blog/forum.

## Attested batch probing (probe)

`probe` is deterministic plumbing for the `/hunt` skill (`specs/hunt.spec.md`) — not something to reach for in normal research. It runs a batch of queries across one or more engines with per-engine pacing and canaries, appending an attested JSONL ledger record for every probe as it executes.

```bash
wscrape probe [query...] --engines ddg,marginalia,hn,discourse,scholar,dblp,openaire,ntrs [--hunt-id ID] [--ledger PATH] [--queries-file FILE] [--limit N]
```

See `skills/hunt/SKILL.md` for the workflow this drives.

## Reddit

No credentials needed. **Search** runs via DuckDuckGo (`site:reddit.com`), so it
works from any IP. **Post and subreddit fetches** use Reddit's public JSON
endpoints — these are **blocked (403) from data-center IPs**; they only work from
a residential IP. See Troubleshooting below.

```bash
# Search Reddit (via DuckDuckGo — always works)
wscrape reddit "WSL2 performance tips" --search -o var/wscrape/results.md
wscrape reddit "neovim config" --search --subreddit neovim --limit 5 -o var/wscrape/results.md
wscrape reddit "DIY float tank heater" --limit 8   # bare query = search

# Fetch a post with comments (residential IP only)
wscrape reddit https://reddit.com/r/linux/comments/abc123/post_title/ -o var/wscrape/post.md
wscrape reddit https://reddit.com/r/linux/comments/abc123/post_title/ --comments 20 -o var/wscrape/post.md

# Browse a subreddit's hot posts (residential IP only)
wscrape reddit https://reddit.com/r/linux/ --limit 20 -o var/wscrape/linux.md
```

## YouTube Transcripts

Uses yt-dlp to extract subtitles. Prefers human-authored subs, falls back to auto-generated.

```bash
# Extract transcript from a YouTube video
wscrape transcript https://www.youtube.com/watch?v=VIDEO_ID -o var/wscrape/transcript.md
wscrape transcript https://youtu.be/VIDEO_ID -o var/wscrape/transcript.md

# Use a bare video ID
wscrape transcript VIDEO_ID -o var/wscrape/transcript.md

# Specify subtitle language
wscrape transcript https://www.youtube.com/watch?v=VIDEO_ID --lang fr -o var/wscrape/transcript-fr.md
```

**Output**: Clean text with timestamps and HTML tags stripped, consecutive duplicate lines removed.

**Using the transcript**: summarise or quote briefly — do **not** reproduce long copyrighted content (song lyrics, full scripts) verbatim in your response.

**No subtitles?** Some videos have subtitles disabled. The command will exit with an error if no subs are available.

## Troubleshooting

- **Empty/thin output from scrape**: add `--js` flag (site needs Playwright)
- **Cookie/consent wall or thin dynamic page**: add `--magic` (dismiss overlays) and/or `--scroll` (load lazy content)
- **Cloudflare / anti-bot block**: wscrape can't reliably fetch bot-protected pages — use a real browser tool for those few pages; don't retry endlessly
- **Noisy or off-topic search results**: anchor with `--region` and `--recent`, and make the query geographically/temporally specific
- **Search returns few results**: DuckDuckGo may be rate-limiting, wait 30s and retry
- **Crawl visits wrong pages**: use `--include /path` to restrict to a site section
- **Reddit post/subreddit fetch returns `403 Blocked`**: Reddit blocks `.json` endpoints from data-center IPs. Use `--search` (DuckDuckGo, always works) to find content, or run from a residential IP for full post/comment fetches.
