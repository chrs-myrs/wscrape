# wscrape

> Self-hosted web research for Claude Code — **no API keys, no subscriptions, no credentials.**

A small, forkable toolkit: the `wscrape` command-line tool plus two Claude Code
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
| `research` | Execute a research brief end-to-end — search, scrape, and synthesise sourced findings with confidence ratings and preserved evidence. |
| `research-brief` | Plan a portable, structured research brief through guided clarification, before any research runs. |

Typical flow: **`/research-brief`** (plan) → **`/research`** (execute) → sourced,
confidence-rated findings with the raw evidence preserved.

## The `wscrape` CLI

| Command | Purpose |
|---------|---------|
| `wscrape search` | Web search via DuckDuckGo — no API key. |
| `wscrape scrape` | Extract a page as clean markdown (boilerplate stripped by default; `--raw` for full, `--query` for BM25-relevant passages). |
| `wscrape map` | Discover URLs on a site (page links, or `--seed sitemap|cc` for sitemap / Common Crawl). |
| `wscrape crawl` | Bulk-crawl a section (native deep-crawl; `--keywords` to walk toward relevant pages). |
| `wscrape gather` | Adaptively crawl from a start URL until it has enough to answer a `--query`. |
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
