# WebMCP on janaka.me

WebMCP lets a web page offer tools to an AI agent running in the visitor's browser. janaka.me offers a small set of
read-only tools so an agent can answer "who is Janaka Premathilaka, what has been built, what has been written" from the site's own
data instead of scraping the DOM. It is a progressive enhancement: the site behaves identically without it.

WebMCP is **not** a remote MCP server. Nothing runs on a server; the tools execute in the page, over static JSON.

## Standard (checked 2026-09-25)

- Spec: [WebMCP, W3C Web Machine Learning Community Group draft](https://webmachinelearning.github.io/webmcp/)
  (Draft CG Report, 17 September 2026). Explainer: https://github.com/webmachinelearning/webmcp.
- API: `document.modelContext.registerTool(tool, { signal })` → `Promise<undefined>`; tool =
  `{ name, title, description, inputSchema, execute(input, { signal }), annotations }`; annotations
  `readOnlyHint`, `untrustedContentHint`, `consequentialHint`. Unregistration = abort the signal (there is no
  `unregisterTool`, no `provideContext`; older tutorials using `navigator.modelContext` are outdated).
- Declarative (form-attribute) API: still a TODO in the draft; not used.
- Browser support: Chrome origin trial, Chrome 149–156, ending 2026-11-16; locally via
  `chrome://flags/#enable-webmcp-testing`. Without a token `document.modelContext` is undefined for visitors.
- Chrome guidance used for budgets: tool/parameter names ≤ 30 chars, descriptions ≤ 500, parameter descriptions
  ≤ 150, output around 1.5K characters ([WebMCP tool security](https://developer.chrome.com/docs/ai/webmcp/secure-tools)).

## Architecture

```
api/public/v1/*.json  (generated, public)
        │ fetchJson (same-origin)
capabilities.js   getProfile · getExperience · listProjects · getProject · searchSite · listResources · getPage
        │                              (DOM-free; page reader injected)
tools.js          TOOLS[] descriptors · validate() · createAgentService(caps).toolsFor(path) / .call(name, input)
        │                              (protocol-neutral; MCP-shaped)
webmcp.js         connect({ modelContext, service, pathname }) · start(window)
        │                              (only file touching document.modelContext)
includes.js       if (document.modelContext && isSecureContext) import('/assets/js/agent/webmcp.js')
```

Cost for ordinary visitors: one property check. The adapter (~20 kB unminified across three modules, uncompressed) and the JSON are
fetched only in browsers that expose the API; the JSON only when a tool runs.

## Tools

All are read-only (`readOnlyHint: true`), have no side effects, validate input against their schema
(`additionalProperties: false`), and return `{ ok: true, data }` or `{ ok: false, error: { code, message } }` with
`code` ∈ `invalid_input | not_found | unavailable | internal`.

| Tool | Registered on | Input | Returns |
|---|---|---|---|
| `get_profile` | every page | – | name, title, positioning, summary, location, work radius, languages, skills, contact email and page, links |
| `get_experience` | `/`, `/resume/` | `include_highlights?: boolean` | roles (period, title, organisation, location[, highlights, technologies]), certifications, education |
| `list_projects` | `/`, `/products/`, `/lab/…`, `/ai/…` | `kind?: all \| product \| reference-application` | slug, name, kind, summary, live URL, janaka.me page |
| `get_project` | same as above | `slug` (`^[a-z0-9-]{1,40}$`) | full project record (stack, source, status, availability, privacy, related pages) |
| `search_site` | every page | `query` (2–100 chars), `section?`, `limit?` 1–10 | total and top matches: title, URL, section, description |
| `list_resources` | `/blog/…`, `/academy/…`, `/lab/…`, `/ai/…` | `section`, `limit?` 1–20, `offset?` 0–500 | newest-first page list with dates |
| `get_page` | every page | `path?` (≤ 300 chars, must be a janaka.me path) | title, description, dates, reading time; for the current page also its h2 outline |

No tool sends messages, runs code, fetches arbitrary URLs, reads cookies or storage, or changes anything. Contact
remains a human action (the email link on the page).

## Lifecycle

`start(window)` builds the service, registers the tools in scope for `location.pathname` with one
`AbortController`, aborts it on `pagehide` (all tools withdrawn), and registers again on a `pageshow` from the
back/forward cache. A failing `registerTool` is logged and ignored. `start` is idempotent.

## Enabling it in production (manual)

1. Register janaka.me for the WebMCP origin trial (https://developer.chrome.com/origintrials/).
2. Paste the token into `WEBMCP_OT_TOKEN` in `assets/js/includes.js` (it injects the `origin-trial` meta before the
   feature check), or add `<meta http-equiv="origin-trial" content="…">` to page heads. Tokens are public by design.
3. Renew or remove the token when the trial ends (2026-11-16) or when the API ships by default.

## Upgrading when the standard changes

1. Run the `standards-refresh` skill for WebMCP; note the new API shape and date here and in `webmcp.js`.
2. Change `assets/js/agent/webmcp.js` only (registration call, options, lifecycle, result format). `tools.js` changes
   only if the descriptor fields themselves change; `capabilities.js` should not change at all.
3. Update the fake `modelContext` in `tests/js/agent.test.mjs` to the new shape, then `node --test "tests/js/*.test.mjs"`.
4. `python3 scripts/validate-site.py --only webmcp`.

Adding another protocol later (a remote MCP server, a different browser API): write a sibling adapter that iterates
`TOOLS` / calls `createAgentService(caps).call()`. For a server, give `createCapabilities` a `fetchJson` that reads
the same files from disk or HTTP.

## Testing locally

`node --test "tests/js/*.test.mjs"` covers contract budgets, validation, path confinement, behaviour on real data,
unsupported browsers, registration with an `AbortSignal`, teardown and bfcache restore. In a browser: Chrome with
`chrome://flags/#enable-webmcp-testing`, `python3 -m http.server 8000` (localhost counts as a secure context), then
`window.__jpWebMCP.tools` lists what the page registered.
