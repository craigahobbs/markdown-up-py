# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`markdown-up` is the Python backend for MarkdownUp, a local Markdown viewer. It is a `chisel`/`waitress`
WSGI application, launched by the `markdown-up` CLI, that serves files from a directory and hosts
BareScript-based frontend applications and backend APIs. **Markdown is never rendered server-side** —
the backend serves an HTML stub that loads the client-side [MarkdownUp frontend](https://github.com/craigahobbs/markdown-up)
which fetches and renders the Markdown in the browser.

## Build system

Uses [python-build](https://github.com/craigahobbs/python-build). `Makefile.base` and `pylintrc` are
downloaded on demand (git-ignored, removed by `make clean`); edit `Makefile` for local overrides, not
`Makefile.base`. All targets run inside an auto-created venv under `build/venv/` — there is no need to
manually create a venv or `pip install`.

```
make test      # run Python unit tests (src/tests/)
make lint      # pylint over src/ (config in pylintrc + Makefile overrides)
make cover     # tests + coverage; enforces 100% branch coverage
make doc       # build build/doc/ (config.json, api.json from docstrings, static/)
make test-app  # run the BareScript unit tests (see "Two test suites" below)
make commit    # test + lint + doc + cover + test-app — run this before committing
make run ARGS='README.md -p 9000'   # run the markdown-up CLI from the venv
```

Run a single Python test (discovery root is `src/`, so the module path starts at `tests.`):

```
make test TEST=tests.test_app.TestMarkdownUp.test_init
make cover TEST=tests.test_app.TestMarkdownUp.test_init
```

Run a single BareScript test: `make test-app TEST=<testName>`.

Coverage must stay at 100% (both Python via `make cover` and BareScript via the `coverageMin: 100` in
`runTests.bare`). New code needs corresponding tests to pass `make commit`.

## Architecture

Three Python modules under `src/markdown_up/`:

- **`main.py`** — CLI entry point (`markdown-up`). Parses args, resolves the root directory, loads and
  schema-validates `markdown-up.json` (`MarkdownUpConfig`) and `markdown-up-api.json` (`MarkdownUpAPIConfig`),
  then serves `MarkdownUpApplication` via `waitress`. CLI flags override config-file values. The full
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

- **`api.py`** — Backend API support. `load_api_requests` parses the schema-markdown schema files and
  executes the BareScript files named in `markdown-up-api.json`, then yields a `chisel.Action` per configured
  API wrapping the matching BareScript function. BareScript API functions receive the schema-validated
  request and can call the injected globals `apiHeader`/`apiError` to set response headers/errors; APIs
  flagged `wsgi` return a raw `[status, headers, body]` WSGI response instead of a validated struct.

Frontend static assets live in `src/markdown_up/static/` (packaged as `package_data`): `index.html` (file
browser HTML stub) and `markdownUpIndex.bare` (the file browser's client-side BareScript app).

## Two test suites

1. **Python** (`src/tests/`, unittest) — covers `main`, `app`, `api`. Run with `make test` / `make cover`.
2. **BareScript** (`src/markdown_up/static/test/`) — unit tests for the `.bare` frontend apps, run by the
   `bare` interpreter via `make test-app`. `make test-app` also `-x` lints all `.bare` files. This is part
   of `make commit` but is separate from the Python `make test`.

## Working with BareScript

The `.bare` files (frontend apps in `static/`, and any backend API scripts) are BareScript, not Python.
When reading, writing, or reviewing BareScript, the `markdown-up.json`/`markdown-up-api.json` config files,
`markdown-script` fenced blocks, or Schema Markdown (`.smd`), use the **bare-script** skill.

## Dependencies

Runtime: `bare-script` (pinned `>=4.2.0,<4.3.0`), `chisel` (`>=2.0.0,<2.1.0`), `waitress`. `bare-script`
provides the BareScript interpreter/library and `chisel` provides the WSGI app, actions, and schema-markdown
validation used throughout.
