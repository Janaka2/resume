---
name: maintain-webmcp
description: Add, change or review the WebMCP tools janaka.me exposes to in-browser AI agents (assets/js/agent/) - tool names, descriptions, input schemas, page scoping, the capability layer behind them, the adapter lifecycle and their tests. Use when a domain capability exposed to agents changes, when the WebMCP standard changes, or when asked about agent access to the site.
---

# Maintain WebMCP

WebMCP is a progressive enhancement. The site must behave identically without it, and WebMCP is not a remote MCP
server: nothing here runs on a server.

## Layers (keep the boundary)

```
content + api/public/v1 JSON
  -> assets/js/agent/capabilities.js   domain queries; DOM-free; fetch and page reader injected
  -> assets/js/agent/tools.js          tool descriptors, input validation, page scope, {ok,data}|{ok:false,error}
  -> assets/js/agent/webmcp.js         the only code that touches document.modelContext
assets/js/includes.js                  feature-detects and lazy-imports webmcp.js
```

A new protocol (remote MCP, another browser API) gets a sibling adapter over `tools.js`. Domain logic never imports
an adapter.

## Workflow

1. If the change depends on the standard's shape (registration, annotations, lifecycle), run `standards-refresh`
   first: read https://webmachinelearning.github.io/webmcp/ and Chrome's WebMCP docs and note the date checked in
   the header comment of `webmcp.js` and in `docs/ai/webmcp.md`.
2. Design by user intent (`get_project({slug})`, not `click_card_3`). Prefer extending an existing tool over adding
   one; stay within 5–10 tools and register a tool only on pages where it helps (`scope`).
3. Contract per tool: `name` ≤ 30 chars snake_case, `title`, `description` ≤ 500 chars saying what, when and what it
   returns, `inputSchema` with `additionalProperties:false`, bounded strings (maxLength/enum/pattern), parameter
   descriptions ≤ 150 chars, `annotations.readOnlyHint: true`. Output compact JSON (~1.5K chars typical).
4. New data belongs in the public JSON (`scripts/gen-public-data.py`), not scraped from the DOM.
5. Update `tests/js/agent.test.mjs` (contract, validation, scoping, behaviour, lifecycle) and `docs/ai/webmcp.md`.
6. Run `node --test "tests/js/*.test.mjs"` and `python3 scripts/validate-site.py --only webmcp,public`.
7. Ask `quality-guardian` for a security read of the diff when a tool's inputs or data change.

## Security (non-negotiable)

Read-only tools only. Validate every argument; confine paths to janaka.me; never fetch arbitrary URLs, run code,
read cookies or storage, send messages or modify content. Contact stays a human action (email link on the page). No
private data in tool output (the public JSON guard applies).

## Done when

Tests and validator pass, the tool list in `docs/ai/webmcp.md` matches `TOOLS`, and the page still works with the
API absent (the "unsupported browser" test).
