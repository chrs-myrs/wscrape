# wscrape

> Self-hosted web research for Claude Code — **no API keys, no subscriptions, no credentials.**

A small, forkable toolkit: the `wscrape` command-line tool plus Claude Code
skills that turn it into a disciplined research workflow. Built on trafilatura,
crawl4ai, DuckDuckGo, and yt-dlp. Use it as-is, or fork it and grow your own
custom research tools.

## Why

- **Credential-free** — nothing to sign up for, no keys to leak.
- **Self-hosted** — runs locally; your queries stay yours.
- **Composable** — a plain CLI any tool can call, plus skills that add method.
- **Yours to extend** — add subcommands and skills; you own your fork.

## Skills

| Skill | What it does |
|-------|--------------|
| `wscrape` | The engine — a CLI for web search, scraping, crawling, and content extraction. No API keys. |
| `hunt` | Needle-hunting for hard-to-find evidence — small-web and community search, historical-web resurrection, attested probe ledgers, and defensible negative results. |
| `research` | Execute a research brief end-to-end — search, scrape, and synthesise sourced findings with confidence ratings and preserved evidence. |
| `research-brief` | Plan a portable, structured research brief through guided clarification, before any research runs. |

Typical flow: **`/research-brief`** (plan) → **`/research`** (execute) → sourced,
confidence-rated findings with the raw evidence preserved. When plain search
bounces off a question, **`/hunt`** goes needle-hunting: small-web and
community surfaces, historical-web resurrection, and a defensible "no evidence
found" when the answer genuinely isn't there.

## The `wscrape` CLI

| Command | Purpose |
|---------|---------|
| `wscrape search` | Web search via DuckDuckGo — no API key. |
| `wscrape scrape` | Extract a page as clean markdown (boilerplate stripped by default; `--raw` for full, `--query` for BM25-relevant passages). Reads PDFs too. |
| `wscrape map` | Discover URLs on a site (page links, or `--seed sitemap|cc` for sitemap / Common Crawl). |
| `wscrape crawl` | Bulk-crawl a section (native deep-crawl; `--keywords` to walk toward relevant pages). |
| `wscrape gather` | Adaptively crawl from a start URL until it has enough to answer a `--query`. |
| `wscrape longtail` | Search the small web and communities — federates Marginalia, Discourse forums, and Hacker News (keyless); `--author` sweeps a person's output. |
| `wscrape cdx` | Enumerate historical-web captures (Wayback CDX; `--cc` for Common Crawl); `--fetch` resurrects and extracts snapshots. |
| `wscrape probe` | Attested batch probing across engines — per-engine pacing, health canaries, and an append-only JSONL ledger of every probe. |
| `wscrape scholar` | Search academic literature — federates Crossref, arXiv, Europe PMC, OpenAIRE, NTRS, DBLP, and OSF (keyless), rank-fused and DOI-deduplicated. |
| `wscrape news` | Search news — GDELT by default (keyless, global); optional Google News; `--hydrate` for snippets. |
| `wscrape reddit` | Search Reddit discussions (via DuckDuckGo — works from any IP). |
| `wscrape transcript` | Extract a YouTube video transcript via yt-dlp. |

Every command writes clean markdown/JSON to stdout or a file (`-o`). Scraping
strips boilerplate by default for high signal density.

## Install

**As a GitHub template** — click *Use this template*, then:
```bash
./install.sh          # symlinks the CLI + skills, installs crawl4ai
wscrape search "hello world" --limit 3
```

**As a Claude Code plugin** — add this repo to a plugin marketplace and install
it; the skills in `skills/` are discovered automatically.

## Make it yours

- **Add a wscrape subcommand** — add an arg parser + `cmd_<name>` handler in
  `tools/wscrape`, register it in the `dispatch` table, add a test in
  `tests/test_wscrape.py`, and document it in `skills/wscrape/SKILL.md`.
- **Add a skill** — create `skills/<name>/SKILL.md` (with `name` +
  `description` frontmatter) and a light spec at `specs/<name>.spec.md`. As a
  plugin it's auto-discovered.
- **Add credentialled extraction (optional)** — `wscrape` is credential-free by
  design. If you add LLM-backed extraction, read credentials from the
  environment at runtime — never hardcode keys in the repo.
- **Keep it legible** — each skill has a light spec describing WHAT it does;
  update the spec when you change behaviour.

## Under the hood

`trafilatura` (static extraction) · `crawl4ai` (JS rendering, deep crawl,
adaptive gather) · `ddgs` (DuckDuckGo search) · `yt-dlp` (transcripts). Python
via [`uv`](https://docs.astral.sh/uv/) (PEP 723 inline deps — no venv to manage).

---

> This README and the toolkit are generated from a canonical source. Only
> `LICENSE` is preserved across regenerations.
