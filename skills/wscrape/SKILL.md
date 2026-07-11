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
6. **scholar** — searching *academic literature*? Federates Crossref + arXiv + Europe PMC into one ranked, deduplicated result set. No URL needed.
7. **news** — searching *news articles*? Federates GDELT (and optional Google News) into one recency-ranked, deduplicated set.

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

`scholar` federates keyless academic APIs — **Crossref** (cross-publisher backbone), **arXiv** (preprints), **Europe PMC** (biomedical) — merges them with reciprocal rank fusion, deduplicates by DOI, and surfaces citation counts. No API key required.

```bash
wscrape scholar "<query>" [--limit N] [--since-year YYYY] [--open-access] [--json]
```

- Markdown digest by default (title, authors, year, venue, citations, DOI/URL, abstract); `--json` emits structured records for programmatic use.
- A **coverage line on stderr** reports which engines answered, failed, or were skipped — read it to judge recall confidence (e.g. `crossref ok (10)  arxiv ok (10)  europepmc ok (8)`).
- Prefer `scholar` over `search` for papers, DOIs, citations, and literature reviews — it returns typed, deduplicated academic records rather than noisy web hits.

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
