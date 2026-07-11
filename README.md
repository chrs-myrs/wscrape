# wscrape

Self-hosted web research toolkit for Claude Code: the wscrape CLI plus research and research-brief skills. Fork it, add your own subcommands and skills, and maintain your own custom research tools.

## What's inside
- **`tools/wscrape`** — a self-hosted, credential-free web research CLI
  (search, scrape, crawl, gather, map, reddit, youtube transcript) built on
  trafilatura + crawl4ai + DuckDuckGo. No API keys.
- **`skills/`** — three Claude Code skills: `wscrape` (tool usage), `research`
  (execute a brief with sourced findings), `research-brief` (plan a portable brief).

## Use it
Two ways — it's both a GitHub template and a Claude Code plugin:
1. **Template**: click *Use this template*, then run `./install.sh`.
2. **Plugin**: add this repo to a Claude Code plugin marketplace and install it.

## Make it yours
See [`docs/CUSTOMISING.md`](docs/CUSTOMISING.md) to add a wscrape subcommand or
a new skill. You own your fork — diverge freely.

> Generated from a canonical source by a build script. Regenerating refreshes
> code and skills but never overwrites this README or `docs/`.
