"""
server.py — the MCP primitives lab: every server-side feature of the protocol in one small server.

    Tools        echo, negotiation, count, summarize, roots, add_note, delete_note
    Resources    lab://notes (list), lab://notes/{note_id} (template), lab://clock (changes every call)
    Prompts      explain
    Sampling     summarize asks the CLIENT's model to write the summary (sampling/createMessage)
    Roots        roots asks the client which directories it is allowed to touch (roots/list)
    Elicitation  delete_note asks the person to confirm before it deletes (elicitation/create)
    Progress     count streams notifications/progress and log messages while it works
    Transports   --transport stdio | streamable-http  (plus --stateless and --json-response for HTTP)

The `negotiation` tool returns the flags the server sees for the current connection: the protocol
version that was negotiated, the client's declared capabilities, and, over HTTP, the session id.

Run:   python server.py                                   stdio (a host launches this as a subprocess)
       python server.py --transport streamable-http       http://127.0.0.1:8765/mcp
Needs: pip install "mcp>=2.2"
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import logging
import os
from typing import Annotated, Any

from pydantic import BaseModel, Field

from mcp.server.mcpserver import Context, Elicit, ListRoots, MCPServer, Resolve, Sample
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import (
    CreateMessageResult,
    ListRootsResult,
    ModelHint,
    ModelPreferences,
    SamplingMessage,
    TextContent,
    ToolAnnotations,
)

log = logging.getLogger("primitives-lab")  # stderr only: on stdio, stdout is the protocol channel

mcp = MCPServer(
    "primitives-lab",
    version="1.0.0",
    instructions=(
        "A teaching server. Call `negotiation` first to see the flags for this connection, "
        "then try every tool once. `summarize` uses your own model through sampling, "
        "`roots` asks which directories you allow, `delete_note` asks you to confirm."
    ),
)

NOTES: dict[str, str] = {
    "welcome": "Resources are application-controlled context: the host decides what the model sees.",
    "flags": "Track: protocolVersion, capabilities on both sides, initialized, and the HTTP session id.",
}

READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)


# ------------------------------------------------------------------ tools
@mcp.tool(title="Echo", annotations=READ_ONLY)
def echo(text: str) -> str:
    """Return the text unchanged. The simplest possible tool: one argument, one result."""
    return text


class Negotiation(BaseModel):
    protocol_version: str = Field(description="The version both sides agreed on during initialize")
    client_capabilities: dict[str, Any] = Field(description="What the client declared it can do (sampling, roots, elicitation...)")
    transport: str = Field(description="How this server was started")
    http_session_id: str | None = Field(description="Mcp-Session-Id header, present on stateful Streamable HTTP only")
    request_id: str = Field(description="JSON-RPC id of this very tools/call request")


@mcp.tool(title="Show the negotiation", annotations=READ_ONLY)
def negotiation(ctx: Context) -> Negotiation:
    """The flags the server sees for this connection: negotiated protocol version, the client's
    declared capabilities, the transport, the HTTP session id if any, and this request's id."""
    caps = ctx.client_capabilities
    try:
        session_id = ctx.headers.get("mcp-session-id")
    except Exception:  # no HTTP request behind this call (stdio)
        session_id = None
    return Negotiation(
        protocol_version=str(ctx.protocol_version),
        client_capabilities=caps.model_dump(exclude_none=True) if caps is not None else {},
        transport=os.environ.get("LAB_TRANSPORT", "stdio"),
        http_session_id=session_id,
        request_id=str(ctx.request_id),
    )


@mcp.tool(title="Count slowly", annotations=READ_ONLY)
async def count(n: int, ctx: Context) -> str:
    """Count to n, sending a notifications/progress message for every step.
    (The separate logging channel, notifications/message, is deprecated as of 2026-07-28: put a
    human-readable `message` on the progress notification instead, and log to stderr for operators.)"""
    if n < 1 or n > 50:
        raise ToolError("n must be between 1 and 50")
    for i in range(1, n + 1):
        await ctx.report_progress(progress=i, total=n, message=f"step {i} of {n}")
        log.info("counted %d", i)  # stderr: never stdout on stdio
        await asyncio.sleep(0.05)
    return f"counted to {n}"


# --- Server-to-client asks: sampling, roots and elicitation ------------------------------------
# Up to spec 2025-11-25 the server sent these as JSON-RPC requests BACK over the connection, which
# needs a back-channel (stdio, or the SSE stream). Since 2026-07-28 they are "input required" rounds:
# the tool result says what it needs, the client supplies it, and the call is retried with the answer
# riding along in request_state. That is what lets them work over stateless HTTP. In this SDK you
# declare the need with a RESOLVER: a function that returns Sample(...), ListRoots() or Elicit(...);
# the framework runs the round trip and injects the answer as a tool argument the model never sees.


def ask_client_model(text: str) -> Sample:
    """Resolver for `summarize`: what to ask the client's model. Must render identically on every retry round."""
    return Sample(
        [SamplingMessage(role="user", content=TextContent(type="text", text=f"Summarise in one sentence:\n\n{text}"))],
        max_tokens=120,
        system_prompt="You summarise plainly. One sentence, no preamble.",
        model_preferences=ModelPreferences(hints=[ModelHint(name="claude")], intelligencePriority=0.3, speedPriority=0.8),
    )


@mcp.tool(title="Summarise with the client's model", annotations=READ_ONLY)
def summarize(text: str, answer: Annotated[CreateMessageResult, Resolve(ask_client_model)]) -> str:
    """Ask the CLIENT's language model to summarise the text in one sentence (sampling/createMessage).
    The server has no model and no API key: the client owns the model, and can review the request."""
    content = answer.content
    reply = content.text if isinstance(content, TextContent) else str(content)
    return f"[{answer.model}] {reply}"


def ask_roots() -> ListRoots:
    """Resolver for `roots`: request the client's roots/list."""
    return ListRoots()


@mcp.tool(title="Which roots may I touch?", annotations=READ_ONLY)
def roots(allowed: Annotated[ListRootsResult, Resolve(ask_roots)]) -> list[str]:
    """Ask the client for its roots (roots/list): the directories or URIs this server is allowed to work in."""
    return [f"{r.name or '(unnamed)'} -> {r.uri}" for r in allowed.roots]


@mcp.tool(title="Add a note", annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False))
async def add_note(note_id: str, text: str, ctx: Context) -> str:
    """Create or replace a note, then tell subscribed clients the resource list changed."""
    if not note_id.isidentifier():
        raise ToolError("note_id must be a simple identifier, e.g. meeting_notes")
    NOTES[note_id] = text
    await ctx.notify_resources_changed()
    return f"lab://notes/{note_id}"


class ConfirmDelete(BaseModel):
    sure: bool = Field(description="Really delete this note?")


def confirm_delete(note_id: str) -> ConfirmDelete | Elicit[ConfirmDelete]:
    """Resolver for `delete_note`: ask the PERSON (elicitation/create) unless there is nothing to delete."""
    if note_id not in NOTES:
        return ConfirmDelete(sure=False)  # nothing to ask; the tool will report the missing note
    return Elicit(f"Delete the note '{note_id}'? This cannot be undone.", ConfirmDelete)


@mcp.tool(title="Delete a note", annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=False))
async def delete_note(note_id: str, confirm: Annotated[ConfirmDelete, Resolve(confirm_delete)], ctx: Context) -> str:
    """Delete a note, but only after the person confirms (elicitation/create). The model cannot answer
    this question: the client shows it to the human and sends back the human's answer."""
    if note_id not in NOTES:
        raise ToolError(f"no note called {note_id}")
    if not confirm.sure:
        return f"kept {note_id}: the person said no"
    del NOTES[note_id]
    await ctx.notify_resources_changed()
    return f"deleted {note_id}"


# ------------------------------------------------------------------ resources
@mcp.resource("lab://notes", title="All notes", mime_type="application/json")
def list_notes() -> str:
    """Every note id with its length. A plain, static-looking resource."""
    import json
    return json.dumps({k: len(v) for k, v in NOTES.items()})


@mcp.resource("lab://notes/{note_id}", title="One note", mime_type="text/plain")
def read_note(note_id: str) -> str:
    """A resource template: the client fills in {note_id}. Unknown ids are an error, not empty text."""
    if note_id not in NOTES:
        raise ToolError(f"no note called {note_id}")
    return NOTES[note_id]


@mcp.resource("lab://clock", title="Server clock", mime_type="text/plain")
def clock() -> str:
    """Changes on every read: shows that a resource can be dynamic."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------ prompts
@mcp.prompt(title="Explain a concept")
def explain(concept: str, level: str = "beginner") -> str:
    """A reusable prompt template the USER picks (user-controlled), unlike tools the model picks."""
    return (
        f"Explain '{concept}' to a {level}. Start with a one-sentence definition, give one concrete "
        "example, then name the most common mistake people make with it."
    )


# ------------------------------------------------------------------ entry point
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--transport", choices=["stdio", "streamable-http"], default=os.environ.get("MCP_TRANSPORT", "stdio"))
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--stateless", action="store_true", help="HTTP: no session id, every request stands alone")
    p.add_argument("--json-response", action="store_true", help="HTTP: answer with application/json instead of an SSE stream")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, stream=__import__("sys").stderr, format="%(name)s %(levelname)s %(message)s")
    os.environ["LAB_TRANSPORT"] = a.transport + (" stateless" if a.stateless else "") + (" json" if a.json_response else "")
    if a.transport == "streamable-http":
        log.info("Streamable HTTP on http://%s:%d/mcp  stateless=%s json=%s", a.host, a.port, a.stateless, a.json_response)
        mcp.run(transport="streamable-http", host=a.host, port=a.port, stateless_http=a.stateless, json_response=a.json_response)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
