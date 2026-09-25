---
paths:
  - "assets/js/agent/**"
  - "assets/js/**"
  - "api/**"
  - "scripts/gen-public-data.py"
  - "chatbot/**"
  - ".github/workflows/**"
  - ".claude/settings.json"
  - "scripts/hooks/**"
---

# Security rules

- Everything under `api/public/v1/`, `llms*.txt` and the WebMCP tools is public. Only already-published facts; never
  phone numbers, credentials (including the AssetCare demo password), tokens, env values, admin data or drafts.
  `gen-public-data.py` `assert_public()` enforces this; extend its patterns rather than bypass it.
- WebMCP tools are read-only. Validate every argument against the tool's `inputSchema` (types, lengths, enums,
  patterns, no unknown keys); paths must normalise to a janaka.me path. No tool may fetch arbitrary URLs, execute
  code, read cookies or `localStorage`, send messages or change content. Errors are `{ok:false,error:{code,message}}`
  without stack traces.
- `document.modelContext` is touched only in `assets/js/agent/webmcp.js`; `validate-site.py --only webmcp` enforces it.
- No secrets in the repo: `chatbot/.env` stays ignored; GitHub Actions use `permissions: contents: read` unless a job
  must push; never echo secrets.
- User-supplied HTML is never injected with `innerHTML`; `includes.js` injects only same-origin partials.
- External links: `target="_blank"` with `rel="noopener"`.
- Hooks are deterministic, fast, read-only, and never call the network.
