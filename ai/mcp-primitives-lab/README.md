# MCP primitives lab — one server, one client, every feature, both handshakes

The worked example behind the Academy page **[MCP primitives lab](https://janaka.me/academy/modules/2026/FSE/mcp-primitives-lab.html)**.
It exists so that someone can learn the Model Context Protocol *by watching it happen*: a small server that
exposes every server-side feature, a client that exercises every one of them and prints the flags it tracks,
a raw wire trace with no SDK at all, and tests that prove the whole thing on three transports.

| File | What it is |
|---|---|
| `server.py` | `MCPServer` with 7 tools, 3 resources (one template, one dynamic), 1 prompt; sampling, roots, elicitation, progress. `--transport stdio` or `streamable-http` (`--stateless`, `--json-response`). |
| `client.py` | The host side: sampling, roots, elicitation and logging callbacks, a 12-step walk-through, and a `FLAGS` dict printed at the end. `--transport stdio` (launches the server) or `http`. |
| `wire_trace.py` | The handshakes by hand, over stdio and over HTTP: `server/discover` (2026-07-28) with a full input-required round, and `initialize` (2025-11-25) with sessions, `202 Accepted`, the GET stream and `DELETE`. |
| `test_lab.py` | `pytest`: the same assertions in-memory, over a stdio subprocess and over Streamable HTTP, plus both traces. |
| `verified/` | The output of every script and the tests, captured on 17 September 2026 with `mcp` 2.2.0 on Python 3.12. |

## Run it

```bash
pip install -r requirements.txt          # mcp>=2.2, httpx, pytest, pytest-asyncio

python client.py                         # stdio: the client launches server.py itself
python wire_trace.py stdio               # the raw bytes of both handshakes

python server.py --transport streamable-http        # terminal 1: http://127.0.0.1:8765/mcp
python client.py --transport http                   # terminal 2
python wire_trace.py http                           # terminal 2

pytest -q                                # 5 tests, about 15 s
```

Plug the server into Claude Code with `claude mcp add primitives-lab -- python /path/to/server.py`, or into
Claude Desktop with the same command in `claude_desktop_config.json`; then ask "call negotiation" and
"summarise the welcome note with my model" and watch the host answer the server's sampling request.

## What each primitive looks like here

| Primitive | Who controls it | In `server.py` | In `client.py` |
|---|---|---|---|
| Tools | the model | `@mcp.tool` with `ToolAnnotations` (read-only, destructive) | `list_tools`, `call_tool` |
| Resources | the application | `lab://notes`, template `lab://notes/{note_id}`, dynamic `lab://clock` | `list_resources`, `list_resource_templates`, `read_resource` |
| Prompts | the person | `@mcp.prompt explain(concept, level)` | `list_prompts`, `get_prompt` |
| Sampling | the client's model | `Resolve(ask_client_model)` returning `Sample(...)` | `sampling_callback` |
| Roots | the client's policy | `Resolve(ask_roots)` returning `ListRoots()` | `list_roots_callback` |
| Elicitation | the person | `Resolve(confirm_delete)` returning `Elicit(...)` | `elicitation_callback` |
| Progress | the server | `ctx.report_progress(i, n, message)` | `progress_callback=` on `call_tool` |
| List-changed | the server | `ctx.notify_resources_changed()` | `message_handler` / `listen()` |

## The flags to keep track of

The client keeps a `FLAGS` dict and prints it at the end. This is what a real host must know per connection:

| Flag | Where it is set | Why it matters |
|---|---|---|
| `protocol_version` | `server/discover` result (`supportedVersions`) or the `initialize` reply | decides which rules below apply |
| `server_capabilities` | same reply: `tools`, `resources` (`subscribe`, `listChanged`), `prompts` | do not call what was not offered |
| client capabilities | implied by the callbacks you register: `sampling`, `roots`, `elicitation` | the server may only ask for what you declared |
| `initialized` | legacy only: after `notifications/initialized` | before it, only `ping` and logging are allowed |
| `_meta` on every request | modern only: version, clientInfo, clientCapabilities | replaces per-connection state; enables stateless HTTP |
| `Mcp-Session-Id` | legacy HTTP: header on the `initialize` reply | must be echoed on every later request; `DELETE` ends it |
| `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name` | modern HTTP request headers | the transport routes and validates before the body is parsed |
| `requestState` | an `input_required` result | opaque; send it back unchanged on the retry with `inputResponses` |

## Two handshakes, and why sampling changed

Up to **2025-11-25**, a server that needed the client's model, roots or the person sent a JSON-RPC request
*back* over the connection, which needs a back-channel: stdio, or the SSE stream of a stateful HTTP session.

Since **2026-07-28**, those asks are **input-required rounds**: the tool result carries `resultType:
"input_required"`, the `inputRequests` and an opaque `requestState`; the client answers by retrying the
same call with `inputResponses`. No back-channel, so it works over stateless HTTP, behind load balancers,
with caching. In the Python SDK you express the need with a *resolver* (`Sample`, `ListRoots`, `Elicit`)
and the framework runs the round trip; `wire_trace.py stdio` shows the two messages by hand.

The separate logging channel and `ping` are gone in 2026-07-28 (the client run shows the server answering
`Method not found`): put a human-readable `message` on progress notifications, log to stderr, and let the
transport handle liveness.

## Verified

`verified/pytest.txt`: `5 passed`. `verified/client-stdio.txt` and `verified/client-http.txt`: all twelve
steps, `FLAGS` ending with `sampling_requests: 1, roots_requests: 1, elicitations: 1,
progress_notifications: 3`. `verified/wire-stdio.txt` and `verified/wire-http.txt`: both handshakes, the
input-required round, `Missing session ID` without the session header, `202` for the notification, and
`200` on `DELETE`.
