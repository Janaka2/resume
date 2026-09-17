"""
client.py — an MCP client that exercises every primitive of server.py and prints the flags as it goes.

It is the HOST side of the protocol: it owns the model (sampling), the filesystem policy (roots),
the person (elicitation) and the log. Every server-to-client request lands in one of the callbacks below.

Run:   python client.py                                      launches server.py over stdio
       python client.py --transport http                     connects to http://127.0.0.1:8765/mcp
       python client.py --transport http --url http://127.0.0.1:8765/mcp
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import types
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters
from mcp.shared.exceptions import MCPError

HERE = Path(__file__).resolve().parent

# The flags a host keeps track of for one connection. Printed at the end.
FLAGS: dict[str, object] = {
    "initialized": False,            # true once initialize + notifications/initialized are done
    "protocol_version": None,        # the version both sides agreed on
    "server_info": None,             # name/version the server announced
    "server_capabilities": None,     # tools, resources (subscribe? listChanged?), prompts, logging, completions
    "client_capabilities_sent": ["sampling", "roots", "elicitation"],   # implied by the callbacks we register
    "sampling_requests": 0,          # times the server asked our model for a completion
    "roots_requests": 0,             # times the server asked which directories it may touch
    "elicitations": 0,               # times the server asked the person a question
    "progress_notifications": 0,
    "log_messages": 0,
    "other_notifications": [],
}


def step(n: int, title: str) -> None:
    print(f"\n[{n:02d}] {title}")


# ------------------------------------------------------------------ server -> client callbacks
async def on_sampling(context, params: types.CreateMessageRequestParams):
    """sampling/createMessage: the server wants a completion from OUR model.
    A real host would show or filter this, then call its LLM. This stub answers deterministically
    so the lab runs offline; swap the body for an Anthropic or OpenAI call to make it real."""
    FLAGS["sampling_requests"] = int(FLAGS["sampling_requests"]) + 1
    last = params.messages[-1].content
    asked = last.text if isinstance(last, types.TextContent) else str(last)
    prefs = params.model_preferences
    hint = prefs.hints[0].name if prefs and prefs.hints else "any"
    print(f"     ↳ server asked my model (hint: {hint}, max_tokens={params.max_tokens}): {asked[:70]!r}…")
    body = asked.split("\n\n", 1)[-1]
    summary = " ".join(body.split()[:12]) + "…"
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(type="text", text=f"In short: {summary}"),
        model="stub-model-1",
        stop_reason="endTurn",
    )


async def on_list_roots(context):
    """roots/list: the server asks where it may work. We allow exactly this folder."""
    FLAGS["roots_requests"] = int(FLAGS["roots_requests"]) + 1
    print("     ↳ server asked for my roots")
    return types.ListRootsResult(roots=[types.Root(uri=HERE.as_uri(), name="primitives-lab folder")])


async def on_elicit(context, params):
    """elicitation/create: the server needs the PERSON. We auto-accept so the lab runs unattended;
    a real host renders params.message and the requested schema as a form."""
    FLAGS["elicitations"] = int(FLAGS["elicitations"]) + 1
    print(f"     ↳ server asked the person: {getattr(params, 'message', params)!r}")
    return types.ElicitResult(action="accept", content={"sure": True})


async def on_log(params: types.LoggingMessageNotificationParams) -> None:
    FLAGS["log_messages"] = int(FLAGS["log_messages"]) + 1
    print(f"     log/{params.level}: {params.data}")


async def on_progress(progress: float, total: float | None, message: str | None) -> None:
    FLAGS["progress_notifications"] = int(FLAGS["progress_notifications"]) + 1
    print(f"     progress {progress:g}/{total:g}  {message or ''}")


async def on_message(message) -> None:
    """Everything else the server sends that is not a request we handle above (e.g. list-changed)."""
    method = getattr(getattr(message, "root", message), "method", None)
    if method and method not in ("notifications/progress", "notifications/message"):
        FLAGS["other_notifications"].append(method)  # type: ignore[union-attr]
        print(f"     notification: {method}")


# ------------------------------------------------------------------ the walk-through
async def run(client: Client) -> None:
    step(1, "initialize: the handshake fixed the flags for this connection")
    FLAGS["initialized"] = True
    FLAGS["protocol_version"] = str(client.protocol_version)
    FLAGS["server_info"] = f"{client.server_info.name} {client.server_info.version}"
    caps = client.server_capabilities
    FLAGS["server_capabilities"] = caps.model_dump(exclude_none=True) if caps else {}
    print(f"     protocol {FLAGS['protocol_version']} | server {FLAGS['server_info']}")
    print(f"     server capabilities: {json.dumps(FLAGS['server_capabilities'])}")
    print(f"     instructions: {(client.instructions or '')[:90]}…")

    step(2, "tools/list: names, schemas and annotations are the contract")
    tools = await client.list_tools()
    for t in tools.tools:
        a = t.annotations
        flags = "read-only" if a and a.read_only_hint else ("destructive" if a and a.destructive_hint else "writes")
        print(f"     {t.name:12} {flags:11} args={list((t.input_schema or {}).get('properties', {}))}")

    step(3, "tools/call echo: the plain case")
    r = await client.call_tool("echo", {"text": "hello, protocol"})
    print("     ->", r.content[0].text)

    step(4, "tools/call negotiation: the flags as the SERVER sees them")
    r = await client.call_tool("negotiation", {})
    print("     ->", json.dumps(r.structured_content, indent=2).replace("\n", "\n        "))

    step(5, "tools/call count: progress and log notifications while a tool runs")
    r = await client.call_tool("count", {"n": 3}, progress_callback=on_progress)
    print("     ->", r.content[0].text)

    step(6, "tools/call summarize: the server asks OUR model (sampling)")
    r = await client.call_tool("summarize", {"text": NOTE_TEXT})
    print("     ->", r.content[0].text)

    step(7, "tools/call roots: the server asks where it may work (roots)")
    r = await client.call_tool("roots", {})
    print("     ->", r.structured_content)

    step(8, "resources: list, read a template, read a dynamic one, then change the list")
    res = await client.list_resources()
    print("     resources:", [str(x.uri) for x in res.resources])
    tpl = await client.list_resource_templates()
    print("     templates:", [x.uri_template for x in tpl.resource_templates])
    note = await client.read_resource("lab://notes/welcome")
    print("     lab://notes/welcome ->", note.contents[0].text)
    clock = await client.read_resource("lab://clock")
    print("     lab://clock ->", clock.contents[0].text)
    r = await client.call_tool("add_note", {"note_id": "todo", "text": "Read the spec's lifecycle section."})
    print("     add_note ->", r.content[0].text)
    print("     lab://notes ->", (await client.read_resource("lab://notes")).contents[0].text)

    step(9, "prompts: list and get a user-controlled template")
    prompts = await client.list_prompts()
    print("     prompts:", [(p.name, [a.name for a in (p.arguments or [])]) for p in prompts.prompts])
    got = await client.get_prompt("explain", {"concept": "sampling", "level": "senior Java engineer"})
    print("     explain ->", got.messages[0].content.text[:96], "…")

    step(10, "tools/call delete_note: the server asks the PERSON first (elicitation)")
    r = await client.call_tool("delete_note", {"note_id": "todo"})
    print("     ->", r.content[0].text)

    step(11, "ping: a liveness check that 2026-07-28 no longer answers")
    try:
        await client.send_ping()
        print("     -> pong (the server negotiated an older protocol, where ping exists)")
    except MCPError as e:
        print(f"     -> server said {e.message!r}: on 2026-07-28 liveness belongs to the transport, not the protocol")

    step(12, "tools/call with a bad argument: an error result, not a crashed connection")
    r = await client.call_tool("count", {"n": 999})
    print(f"     -> is_error={r.is_error}: {r.content[0].text}")

    print("\nFLAGS after the session:")
    print(json.dumps(FLAGS, indent=2, default=str))


NOTE_TEXT = (
    "The Model Context Protocol separates the three things a model needs: tools it can call, "
    "resources the host can show it, and prompts a person can pick. Sampling, roots and elicitation "
    "run the other way: the server asks the client for a completion, for permitted directories, or for a human answer."
)


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    p.add_argument("--url", default="http://127.0.0.1:8765/mcp")
    a = p.parse_args()
    if a.transport == "stdio":
        target = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py"), "--transport", "stdio"])
        print(f"connecting over stdio: {sys.executable} server.py")
    else:
        target = a.url
        print(f"connecting over Streamable HTTP: {a.url}")
    async with Client(
        target,
        sampling_callback=on_sampling,
        list_roots_callback=on_list_roots,
        elicitation_callback=on_elicit,
        logging_callback=on_log,
        message_handler=on_message,
        client_info=types.Implementation(name="primitives-lab-client", version="1.0.0"),
    ) as client:
        await run(client)


if __name__ == "__main__":
    asyncio.run(main())
