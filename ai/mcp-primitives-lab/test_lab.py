"""
test_lab.py — every primitive, on three transports.

    pytest -q

In-memory: the Client talks to the MCPServer object directly (no process, no socket): fastest, for logic.
stdio:     the Client launches server.py as a subprocess, as Claude Desktop or Claude Code would.
HTTP:      server.py --transport streamable-http runs in a subprocess; the Client connects by URL.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from mcp import types
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import server as lab  # noqa: E402  (the module under test; importing it does not start a transport)

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ---------------------------------------------------------------- the host side, recorded
class Host:
    """The callbacks a real host implements, with counters so tests can assert they were used."""

    def __init__(self) -> None:
        self.sampling = 0
        self.roots = 0
        self.elicit = 0
        self.progress: list[tuple[float, float | None, str | None]] = []
        self.say_yes = True

    async def on_sampling(self, context, params: types.CreateMessageRequestParams):
        self.sampling += 1
        return types.CreateMessageResult(role="assistant", model="stub", stop_reason="endTurn",
                                         content=types.TextContent(type="text", text="a one-sentence summary"))

    async def on_roots(self, context):
        self.roots += 1
        return types.ListRootsResult(roots=[types.Root(uri=HERE.as_uri(), name="lab")])

    async def on_elicit(self, context, params):
        self.elicit += 1
        return types.ElicitResult(action="accept", content={"sure": self.say_yes})

    async def on_progress(self, progress, total, message):
        self.progress.append((progress, total, message))

    def client(self, target) -> Client:
        return Client(target, sampling_callback=self.on_sampling, list_roots_callback=self.on_roots,
                      elicitation_callback=self.on_elicit,
                      client_info=types.Implementation(name="test-host", version="0"))


async def exercise_everything(client: Client, host: Host) -> None:
    """The same assertions for every transport."""
    # negotiation flags
    assert str(client.protocol_version) == "2026-07-28"
    assert client.server_info.name == "primitives-lab"
    caps = client.server_capabilities
    assert caps.tools is not None and caps.resources is not None and caps.prompts is not None

    # tools/list: names and annotations
    tools = {t.name: t for t in (await client.list_tools()).tools}
    assert set(tools) == {"echo", "negotiation", "count", "summarize", "roots", "add_note", "delete_note"}
    assert tools["echo"].annotations.read_only_hint is True
    assert tools["delete_note"].annotations.destructive_hint is True

    # plain call, structured result
    assert (await client.call_tool("echo", {"text": "hi"})).content[0].text == "hi"
    neg = (await client.call_tool("negotiation", {})).structured_content
    assert neg["protocol_version"] == "2026-07-28"
    assert "sampling" in neg["client_capabilities"] and "roots" in neg["client_capabilities"]

    # progress notifications
    r = await client.call_tool("count", {"n": 3}, progress_callback=host.on_progress)
    assert r.content[0].text == "counted to 3"
    assert [p[0] for p in host.progress] == [1, 2, 3] and host.progress[-1][2] == "step 3 of 3"

    # sampling: the server used OUR model
    r = await client.call_tool("summarize", {"text": "MCP separates tools, resources and prompts."})
    assert host.sampling == 1 and r.content[0].text == "[stub] a one-sentence summary"

    # roots: the server asked where it may work
    r = await client.call_tool("roots", {})
    assert host.roots == 1 and r.structured_content["result"] == [f"lab -> {HERE.as_uri()}"]

    # resources: list, template, dynamic, and a change
    uris = {str(x.uri) for x in (await client.list_resources()).resources}
    assert {"lab://notes", "lab://clock"} <= uris
    assert [t.uri_template for t in (await client.list_resource_templates()).resource_templates] == ["lab://notes/{note_id}"]
    assert (await client.read_resource("lab://notes/welcome")).contents[0].text.startswith("Resources are")
    assert "T" in (await client.read_resource("lab://clock")).contents[0].text
    assert (await client.call_tool("add_note", {"note_id": "t1", "text": "x"})).content[0].text == "lab://notes/t1"
    assert (await client.read_resource("lab://notes/t1")).contents[0].text == "x"

    # prompts: user-controlled templates
    assert [p.name for p in (await client.list_prompts()).prompts] == ["explain"]
    got = await client.get_prompt("explain", {"concept": "roots", "level": "beginner"})
    assert "Explain 'roots' to a beginner" in got.messages[0].content.text

    # elicitation: the person is asked, and can say no
    host.say_yes = False
    assert (await client.call_tool("delete_note", {"note_id": "t1"})).content[0].text.startswith("kept t1")
    host.say_yes = True
    assert (await client.call_tool("delete_note", {"note_id": "t1"})).content[0].text == "deleted t1"
    assert host.elicit == 2

    # errors are results, not crashes
    r = await client.call_tool("count", {"n": 999})
    assert r.is_error and "between 1 and 50" in r.content[0].text
    r = await client.call_tool("delete_note", {"note_id": "nope"})
    assert r.is_error and "no note called nope" in r.content[0].text


# ---------------------------------------------------------------- three transports
async def test_in_memory():
    host = Host()
    async with host.client(lab.mcp) as client:
        await exercise_everything(client, host)


async def test_stdio_subprocess():
    host = Host()
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py"), "--transport", "stdio"])
    async with host.client(params) as client:
        await exercise_everything(client, host)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def http_server():
    port = _free_port()
    proc = subprocess.Popen([sys.executable, str(HERE / "server.py"), "--transport", "streamable-http", "--port", str(port)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            with socket.socket() as s:
                s.settimeout(0.2)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.2)
        else:
            raise RuntimeError("HTTP server did not start")
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


async def test_streamable_http(http_server):
    host = Host()
    async with host.client(http_server) as client:
        await exercise_everything(client, host)


# ---------------------------------------------------------------- the raw wire, no SDK
def test_wire_trace_stdio_runs():
    out = subprocess.run([sys.executable, str(HERE / "wire_trace.py"), "stdio"], capture_output=True, text=True,
                         encoding="utf-8", timeout=60)
    assert out.returncode == 0, out.stderr
    assert '"method": "server/discover"' in out.stdout and 'input_required' in out.stdout
    assert "negotiated protocolVersion = 2025-11-25" in out.stdout   # the legacy path, for comparison


def test_wire_trace_http_runs(http_server):
    out = subprocess.run([sys.executable, str(HERE / "wire_trace.py"), "http", http_server], capture_output=True,
                         text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0, out.stderr
    assert "Mcp-Session-Id=" in out.stdout and "HTTP 202" in out.stdout and "Missing session ID" in out.stdout
