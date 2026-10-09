# CLAUDE.md

Notes for coding agents working in this repository.

## What this is

`markdown-up` is the Python backend for MarkdownUp, a local Markdown viewer. It is a `chisel`/`waitress`
WSGI application, launched by the `markdown-up` CLI, that serves files from a directory and hosts
BareScript-based frontend applications. **Markdown is never rendered server-side** —
the backend serves an HTML stub that loads the client-side [MarkdownUp frontend](https://github.com/craigahobbs/markdown-up)
which fetches and renders the Markdown in the browser.

## python-build

This is a [python-build](https://github.com/craigahobbs/python-build#readme) package. Read the python-build skill before running tests, lint, coverage, or changing the Makefile: [`../python-build/SKILL.md`](../python-build/SKILL.md) if that file exists, otherwise [https://raw.githubusercontent.com/craigahobbs/python-build/main/SKILL.md](https://raw.githubusercontent.com/craigahobbs/python-build/main/SKILL.md).

Local Makefile overrides:

- `GHPAGES_SRC` — `build/doc/`
- `TESTS_REQUIRE` — `bare-script`, for the `bare` CLI used by `test-app` and `doc` (not a runtime dependency)
- `PYLINT_ARGS` — missing docstring checks disabled
- no `SPHINX_DOC` — `doc` is a custom recipe (config.json, `static/`)
- `commit` also depends on `test-app`

Package-specific targets:

- `make test-app` — BareScript unit tests for `src/markdown_up/static/` (`TEST=` is an exact BareScript test name)
- `make run ARGS='...'` — run the `markdown-up` CLI from the default venv

Coverage must stay at 100% for both Python (`make cover`) and BareScript (`coverageMin: 100` in `runTests.bare`).

## Architecture

Two Python modules under `src/markdown_up/`:

- **`main.py`** — CLI entry point (`markdown-up`). Parses args, resolves the root directory, loads and
  schema-validates `markdown-up.json` (`MarkdownUpConfig`), then serves `MarkdownUpApplication` via `waitress`. CLI flags override config-file values. The full
  config schema lives inline as `CONFIG_TYPES` (schema-markdown) — update it here when adding config options.

- **`app.py`** — `MarkdownUpApplication(chisel.Application)`. Its `__call__` is the routing core: it first
  tries to match a registered chisel request (APIs, docs); otherwise it serves a static file from `root`.
  Key behaviors:
  - Directory requests → trailing-slash redirect, then serve `index.html`/`index.htm`, else generate a
    MarkdownUp stub from `index.md`/`README.md`.
  - A request for `X.html` with no real file but a sibling `X.md`/`X.markdown` → auto-generated MarkdownUp
    HTML stub (`create_markdown_up_stub`), which loads the client frontend from `/markdown-up/...`.
  - `markdown_up_index` is the chisel action powering the file browser (lists files/dirs; rewrites `.md`
    entries to their `.html` stub names). It guards against path traversal (`..`, absolute paths).
  - **Release mode** (`-r`): drops the doc/index apps, disables output validation, and lazily caches each
    served static as a registered request (guarded by `add_request_lock`).

Frontend static assets live in `src/markdown_up/static/` (packaged as `package_data`): `index.html` (file
browser HTML stub) and `markdownUpIndex.bare` (the file browser's client-side BareScript app).

## Two test suites

1. **Python** (`src/tests/`, unittest) — covers `main` and `app`. Run with `make test` / `make cover`.
2. **BareScript** (`src/markdown_up/static/test/`) — unit tests for the `.bare` frontend apps, run by the
   `bare` interpreter via `make test-app`. `make test-app` also `-x` lints all `.bare` files. This is part
   of `make commit` but is separate from the Python `make test`.

## Working with BareScript

The `.bare` files (frontend apps in `static/`) are BareScript, not Python.
When reading, writing, or reviewing BareScript, the `markdown-up.json` config file,
`markdown-script` fenced blocks, or Schema Markdown (`.smd`), use the **bare-script** skill.
