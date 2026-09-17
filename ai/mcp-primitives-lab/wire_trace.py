"""
wire_trace.py — the handshakes with NO SDK, so you can see exactly what is on the wire.

    python wire_trace.py stdio      spawn server.py and speak newline-delimited JSON-RPC over its stdin/stdout
    python wire_trace.py http       talk to a running `python server.py --transport streamable-http`
                                    with plain HTTP requests, and read the SSE stream by hand

Every line marked  ->  is bytes we sent, every line marked  <-  is bytes we received.

Two generations of handshake are shown, because you will meet both:

  2026-07-28  `server/discover`, then every request carries the version and the client's capabilities
              in `_meta`. No session state is required, so it works over stateless HTTP. A server that
              needs the client's model, roots or the person answers `resultType: "input_required"` and
              the client RETRIES the call with `inputResponses` and the opaque `requestState`.
  2025-11-25  `initialize` -> reply -> `notifications/initialized`. The version and capabilities are
              fixed once per connection; over HTTP the server issues an `Mcp-Session-Id`.

The flags to keep track of: the request id that must match; the protocol version proposed and
confirmed; the capabilities each side declares; `initialized` (legacy) or `_meta` on every request
(modern); over HTTP the `Mcp-Session-Id` and `MCP-Protocol-Version` headers; and, for an input-required
round, the `requestState` that must go back unchanged.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODERN = "2026-07-28"
LEGACY = "2025-11-25"
CLIENT_CAPS = {"roots": {"listChanged": True}, "sampling": {}, "elicitation": {"form": {}}}
META = {  # modern: rides on EVERY request instead of being fixed by initialize
    "io.modelcontextprotocol/protocolVersion": MODERN,
    "io.modelcontextprotocol/clientInfo": {"name": "wire-trace", "version": "1.0.0"},
    "io.modelcontextprotocol/clientCapabilities": CLIENT_CAPS,
}


def show(direction: str, payload: dict | str, note: str = "", width: int = 420) -> None:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    if len(text) > width:
        text = text[:width] + f" …({len(text)} chars)"
    print(f"{direction} {text}")
    if note:
        print(f"   {note}")


def stub_model_answer(request: dict) -> dict:
    """What a host would do with a sampling/createMessage request: call its own model. We fake it."""
    asked = request["params"]["messages"][-1]["content"]["text"]
    return {"role": "assistant", "model": "stub-model-1", "stopReason": "endTurn",
            "content": {"type": "text", "text": "In short: " + " ".join(asked.split("\n\n", 1)[-1].split()[:8]) + "…"}}


# ------------------------------------------------------------------ stdio
def trace_stdio() -> None:
    print("== stdio: one JSON-RPC message per line on the child's stdin/stdout; stderr is free for logs ==")

    def spawn():
        return subprocess.Popen([sys.executable, str(HERE / "server.py"), "--transport", "stdio"],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                text=True, encoding="utf-8")

    def rpc(proc, msg: dict, note_out: str = "", note_in: str = "") -> dict | None:
        show("->", msg, note_out)
        proc.stdin.write(json.dumps(msg) + "\n")        # newline-delimited; a message may not contain a raw newline
        proc.stdin.flush()
        if "id" not in msg:
            return None                                 # a notification gets no reply
        reply = json.loads(proc.stdout.readline())
        show("<-", reply, note_in)
        assert reply["id"] == msg["id"], "flag: the reply must carry the request's id"
        return reply

    print("\n-- A. modern handshake (2026-07-28): server/discover, then _meta on every request --")
    p = spawn()
    disc = rpc(p, {"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": META}},
               "flag: we say which version we speak and what we can do, inside _meta",
               "flag: supportedVersions, capabilities, instructions, cacheScope/ttlMs (the client may cache this), serverInfo in _meta")
    r = disc["result"]
    print(f"   supportedVersions={r['supportedVersions']} capabilities={json.dumps(r['capabilities'])} cache={r['cacheScope']}/{r['ttlMs']}ms")
    rpc(p, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"_meta": META, "name": "echo", "arguments": {"text": "raw bytes"}}},
        "flag: no notifications/initialized; _meta carries the version and capabilities again",
        "resultType: \"complete\" — content[] for any client, structuredContent because the SDK derived an output schema")

    call = {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"_meta": META, "name": "summarize", "arguments": {"text": "MCP separates tools, resources and prompts."}}}
    first = rpc(p, call, "the server needs OUR model for this one",
                "flag: resultType \"input_required\" + inputRequests (keyed) + requestState (opaque, encrypted, must go back unchanged)")
    res = first["result"]
    assert res["resultType"] == "input_required"
    key, req = next(iter(res["inputRequests"].items()))
    print(f"   the server asked for {req['method']} under key {key!r}")
    retry = {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
             "params": {**call["params"], "inputResponses": {key: stub_model_answer(req)}, "requestState": res["requestState"]}}
    rpc(p, retry, "the RETRY: same call, plus inputResponses for that key and the requestState we were given",
        "resultType \"complete\": the tool ran with the model's answer injected as an argument")
    p.stdin.close(); p.wait(timeout=10)
    print(f"   server exited with code {p.returncode} once stdin closed")

    print("\n-- B. legacy handshake (2025-11-25): initialize, reply, notifications/initialized --")
    p = spawn()
    init = rpc(p, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                   "params": {"protocolVersion": MODERN, "capabilities": CLIENT_CAPS, "clientInfo": {"name": "wire-trace", "version": "1.0.0"}}},
               "flag: we PROPOSE a protocolVersion",
               "flag: result.protocolVersion is what the server CONFIRMED (an initialize request lands you on the legacy version)")
    print(f"   negotiated protocolVersion = {init['result']['protocolVersion']}")
    rpc(p, {"jsonrpc": "2.0", "method": "notifications/initialized"},
        "flag: the handshake is complete only after this notification; before it, only ping and logging are allowed")
    rpc(p, {"jsonrpc": "2.0", "id": 2, "method": "ping"}, "ping exists on the legacy version", "an empty result is the pong")
    tools = rpc(p, {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}})
    print(f"   tools = {[t['name'] for t in tools['result']['tools']]}")
    p.stdin.close(); p.wait(timeout=10)
    print(f"   server exited with code {p.returncode} once stdin closed")


# ------------------------------------------------------------------ Streamable HTTP
def sse_events(body: str) -> list[dict]:
    """Parse a text/event-stream body: blank-line separated events, `data:` lines carry the JSON."""
    events = []
    for block in body.split("\n\n"):
        data = "\n".join(line[5:].lstrip() for line in block.splitlines() if line.startswith("data:"))
        if data:
            events.append(json.loads(data))
    return events


def trace_http(url: str = "http://127.0.0.1:8765/mcp") -> None:
    import httpx  # pip install httpx

    print(f"== Streamable HTTP: every client message is a POST to {url}; replies come as JSON or as an SSE stream ==")
    accept = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}

    def messages(r: httpx.Response) -> list[dict]:
        ct = r.headers.get("content-type", "")
        return sse_events(r.text) if ct.startswith("text/event-stream") else ([r.json()] if r.content else [])

    with httpx.Client(timeout=10) as http:
        print("\n-- A. modern (2026-07-28): server/discover, _meta on every POST, no session required --")
        disc = {"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": META}}
        show("->", disc, "first, WITHOUT the MCP-Protocol-Version header, to see what the flag does")
        r = http.post(url, json=disc, headers=accept)
        print(f"<- HTTP {r.status_code}: {r.text[:100]!r}")
        print("   flag: without the header the server applies the session rules of the older protocol and refuses")
        def modern_headers(method: str, tool: str | None = None) -> dict[str, str]:
            """The three modern flags ride as HTTP headers so a proxy or cache can route without parsing the body:
            MCP-Protocol-Version (which rules apply), Mcp-Method (must equal the JSON-RPC method), Mcp-Name (the tool)."""
            h = {**accept, "MCP-Protocol-Version": MODERN, "Mcp-Method": method}
            if tool:
                h["Mcp-Name"] = tool
            return h

        show("->", disc, "again, with headers MCP-Protocol-Version: 2026-07-28 and Mcp-Method: server/discover (Accept lists BOTH media types)")
        r = http.post(url, json=disc, headers=modern_headers("server/discover"))
        print(f"<- HTTP {r.status_code} content-type={r.headers.get('content-type')} Mcp-Session-Id={r.headers.get('mcp-session-id')}")
        show("<-", messages(r)[-1], "flag: no session id issued; the answer is plain JSON because nothing needs streaming")
        r = http.post(url, json=disc, headers={**accept, "MCP-Protocol-Version": MODERN, "Mcp-Method": "tools/list"})
        print(f"-> the same body with a WRONG Mcp-Method header\n<- HTTP {r.status_code}: {r.text[:110]!r}")
        print("   flag: the header and the body must agree; the transport checks it before the method runs")
        call = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"_meta": META, "name": "negotiation", "arguments": {}}}
        show("->", call, "a tool call straight away: headers + _meta, no session, no initialized notification (Mcp-Name: negotiation)")
        r = http.post(url, json=call, headers=modern_headers("tools/call", "negotiation"))
        print(f"<- HTTP {r.status_code}")
        show("<-", messages(r)[-1]["result"]["structuredContent"], "what the server sees: the version and capabilities we put in _meta")

        print("\n-- B. legacy (2025-11-25): initialize creates a session; every later request must carry its id --")
        init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": MODERN, "capabilities": CLIENT_CAPS, "clientInfo": {"name": "wire-trace", "version": "1.0.0"}}}
        show("->", init, "no session header yet: this request creates the session")
        r = http.post(url, json=init, headers=accept)
        session = r.headers.get("mcp-session-id")
        print(f"<- HTTP {r.status_code} content-type={r.headers.get('content-type')} Mcp-Session-Id={session}")
        version = messages(r)[-1]["result"]["protocolVersion"]
        print(f"   negotiated protocolVersion = {version}")
        head = {**accept, "MCP-Protocol-Version": version, **({"Mcp-Session-Id": session} if session else {})}

        note = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        show("->", note, "flag: a notification -> 202 Accepted, empty body")
        r = http.post(url, json=note, headers=head)
        print(f"<- HTTP {r.status_code} (body {len(r.content)} bytes)")

        lst = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        show("->", lst, "same POST, now with Mcp-Session-Id and MCP-Protocol-Version headers")
        r = http.post(url, json=lst, headers=head)
        print(f"<- HTTP {r.status_code} content-type={r.headers.get('content-type')} tools={[t['name'] for t in messages(r)[-1]['result']['tools']]}")

        if session:
            r = http.post(url, json=lst, headers=accept)
            print(f"-> the same request WITHOUT the session header\n<- HTTP {r.status_code}: {r.text[:110]!r}")
            print("   flag: a stateful server rejects requests that do not carry the session id it issued")
            print("-> GET with Accept: text/event-stream opens the standalone stream for server-initiated messages")
            with http.stream("GET", url, headers={"Accept": "text/event-stream", "Mcp-Session-Id": session, "MCP-Protocol-Version": version}) as s:
                print(f"<- HTTP {s.status_code} content-type={s.headers.get('content-type')} (kept open; nothing to deliver, so we close it)")
            r = http.delete(url, headers={"Mcp-Session-Id": session, "MCP-Protocol-Version": version})
            print(f"-> DELETE with the session id\n<- HTTP {r.status_code}: the session is over; the id is now invalid")
        else:
            print("   (started with --stateless: no session id was issued, every request stands alone)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    if mode == "http":
        trace_http(sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8765/mcp")
    else:
        trace_stdio()
