# Customising the toolkit

## Add a wscrape subcommand
1. Add an argument parser + `cmd_<name>` handler in `tools/wscrape`.
2. Register it in the `dispatch` table.
3. Add a test in `tests/test_wscrape.py` and document it in `skills/wscrape/SKILL.md`.

## Add a new skill
1. Create `skills/<name>/SKILL.md` with `name` + `description` frontmatter.
2. Add a light spec at `specs/<name>.spec.md`.
3. If distributing as a plugin, it is auto-discovered from `skills/`.

## Add credentialled extraction (optional)
`wscrape` is credential-free by design. If you add LLM-backed extraction, read
credentials from the environment at runtime — never hardcode keys in the repo.

## Keep it maintainable
Each skill has a light spec describing WHAT it does. Update the spec when you
change behaviour so your fork stays legible.
