#!/usr/bin/env python3
"""Generate academy/modules/2026/FSE/mcp-primitives-lab.html from ai/mcp-primitives-lab (code + verified output).

Run from anywhere:  python3 scripts/generators/gen-mcp-lab-page.py
Re-run after any change to the lab so the page never drifts from the code that was actually executed.
"""
import html, io, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EX = os.path.join(ROOT, "ai/mcp-primitives-lab")
OUT = os.path.join(ROOT, "academy/modules/2026/FSE/mcp-primitives-lab.html")
URL = "https://janaka.me/academy/modules/2026/FSE/mcp-primitives-lab.html"
GH = "https://github.com/Janaka2/resume/tree/main/ai/mcp-primitives-lab"
CERT_A = "/assets/certificates/anthropic-model-context-protocol-advanced-topics.pdf"
CERT_I = "/assets/certificates/anthropic-introduction-to-model-context-protocol.pdf"


def esc(s): return html.escape(s, quote=False)
def code(text, lang="python"):
    return f'<pre><code class="language-{lang}">{esc(text.strip("\n"))}</code></pre>'
def rd(rel): return io.open(os.path.join(EX, rel), encoding="utf-8").read()
def fold(rel, lang, label=None, text=None):
    text = text if text is not None else rd(rel); n = text.count("\n")
    return f'<details class="code-fold"><summary><span>{esc(label or rel)} · {n} lines</span></summary>{code(text, lang)}</details>'
def note(text, kind=""):
    return f'<div class="callout {kind}"><p>{text}</p></div>'
def key(label, text):
    return f'<div class="callout key"><span class="lbl">{esc(label)}</span><p>{text}</p></div>'
def flow(text):
    return f'<div class="msgflow">{esc(text.strip("\n"))}</div>'
def table(headers, rows):
    h = "".join(f"<th>{c}</th>" for c in headers)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'
def sec(id_, eyebrow, h2, body):
    return f'''
  <section class="sec" id="{id_}">
    <div class="wrap">
      <p class="eyebrow">{esc(eyebrow)}</p>
      <h2>{esc(h2)}</h2>
      <div class="prose rel-body">
{body}
      </div>
    </div>
  </section>
'''
def between(text, start, end=None):
    """A snippet of a source file: from the line containing `start` up to (not including) the line containing `end`."""
    i = text.index(start); i = text.rfind("\n", 0, i) + 1
    if end is None:
        return text[i:]
    j = text.index(end, i); j = text.rfind("\n", 0, j) + 1
    return text[i:j].rstrip("\n")
def part(text, marker_start, marker_end=None):
    """A slice of a verified output file between two lines that contain the markers."""
    lines = text.splitlines()
    s = next(k for k, l in enumerate(lines) if marker_start in l)
    e = next((k for k, l in enumerate(lines) if k > s and marker_end and marker_end in l), len(lines))
    return "\n".join(lines[s:e]).rstrip()


SERVER, CLIENT, WIRE, TESTS = rd("server.py"), rd("client.py"), rd("wire_trace.py"), rd("test_lab.py")
COUNT_MARK = '@mcp.tool(title="Count slowly"'
V_CLIENT, V_HTTP, V_WSTDIO, V_WHTTP, V_TEST = (rd("verified/client-stdio.txt"), rd("verified/client-http.txt"),
                                               rd("verified/wire-stdio.txt"), rd("verified/wire-http.txt"), rd("verified/pytest.txt"))

TITLE = "MCP primitives lab: one server, one client, every feature, both handshakes"
DESC = ("Learn the Model Context Protocol by watching it run: a verified Python server and client that exercise tools, "
        "resources, prompts, sampling, roots, elicitation and progress over stdio and Streamable HTTP, the raw bytes of the "
        "2026-07-28 and 2025-11-25 handshakes, and the flags a host must track.")

HEAD = f'''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(TITLE)} | Janaka Academy</title>
  <meta name="description" content="{esc(DESC)}">
  <link rel="canonical" href="{URL}">
  <link rel="alternate" type="application/atom+xml" title="Janaka Premathilaka" href="/feed.xml">
  <meta property="og:title" content="{esc(TITLE)} | Janaka Academy">
  <meta property="og:description" content="{esc(DESC)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{URL}">
  <meta property="og:image" content="https://janaka.me/assets/og/academy.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(TITLE)} | Janaka Academy">
  <meta name="twitter:description" content="{esc(DESC)}">
  <meta name="twitter:image" content="https://janaka.me/assets/og/academy.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png?v=1">
  <link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/favicon-16.png?v=1">
  <link rel="apple-touch-icon" sizes="180x180" href="/assets/icons/apple-touch-icon.png?v=1">

  <!-- Apply the stored theme before first paint to avoid a flash -->
  <script>
    (function(){{
      try {{
        var t = localStorage.getItem("jp-theme");
        if (t === "dark" || (!t && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches)) {{
          document.documentElement.setAttribute("data-theme", "dark");
        }}
      }} catch (e) {{}}
    }})();
  </script>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
  <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
  <noscript><link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet"></noscript>
  <link rel="stylesheet" href="/assets/css/theme.css?v=20260916">
  <link rel="stylesheet" href="/assets/css/subsite.css?v=20260916b">
  <link rel="stylesheet" href="/assets/css/study.css?v=20260921b">
  <link rel="manifest" href="/assets/site.webmanifest">
  <meta name="referrer" content="strict-origin-when-cross-origin">
</head>
<body class="study">
<a class="skip" href="#main">Skip to content</a>

<div data-include="/partials/site-nav.html"></div>

<main id="main">
  <section class="sec subhero">
    <div class="wrap">
      <p class="eyebrow"><a href="/academy/" style="color:inherit;text-decoration:none">&larr; Janaka Academy</a> &middot; <a href="/academy/modules/2026/FSE/mcp-end-to-end.html" style="color:inherit;text-decoration:none">MCP end to end</a></p>
      <h1>MCP primitives lab.</h1>
      <p class="lede">Learn the Model Context Protocol by watching it run. One small server exposes every feature: tools, resources, prompts, sampling, roots, elicitation, progress. One client exercises each of them and prints the flags it tracks. A raw trace shows the bytes of both handshakes, over stdio and over Streamable HTTP. Every output on this page was produced by the code on this page, on 17 September 2026.</p>
      <div class="badges">
        <span class="badge hot">Spec 2026-07-28 and 2025-11-25</span>
        <span class="badge">Python SDK 2.2</span>
        <span class="badge">stdio · Streamable HTTP · SSE</span>
        <span class="badge">5 tests, 3 transports</span>
        <a class="badge" href="{CERT_A}" target="_blank" rel="noopener" style="text-decoration:none" title="Certificate of completion, Anthropic, 17 September 2026">Anthropic: MCP Advanced Topics ✓</a>
        <a class="badge" href="{CERT_I}" target="_blank" rel="noopener" style="text-decoration:none" title="Certificate of completion, Anthropic, September 2026">Anthropic: Introduction to MCP ✓</a>
      </div>
      <div class="actions">
        <a class="btn primary" href="#map">Start with the map</a>
        <a class="btn" href="#flags">Jump to the flags</a>
        <a class="btn" href="{GH}" target="_blank" rel="noopener">Get the code ↗</a>
      </div>
    </div>
  </section>
'''

FOOT = '''</main>

<footer class="sitefoot">
  <div class="wrap">
    <span>&copy; <span id="year"></span> Janaka Academy &middot; Zug 🇨🇭</span>
    <span><a href="/academy/">Academy</a> &middot; <a href="/academy/modules/2026/FSE/mcp-end-to-end.html">MCP end to end</a> &middot; <a href="/">janaka.me</a></span>
  </div>
</footer>

<script src="/assets/js/includes.js?v=20260910"></script>
<script src="/assets/js/site-nav.js?v=20260910"></script>
<script src="/assets/js/study.js?v=20260916"></script>
</body>
</html>
'''

parts = [HEAD]

# ------------------------------------------------------------------ 1 map
parts.append(sec("map", "Part one · Orientation", "The map: seven primitives, who controls each, and where to look.", f'''
<p>MCP has three things a server <em>offers</em> and three things a server may <em>ask for</em>. The first group is controlled by a different party each time; the second always ends at the client, because the client owns the model, the filesystem policy and the person. Progress is the one notification channel that survived the 2026 revision.</p>
{table(["Primitive", "Who controls it", "In server.py", "In client.py"], [
  ["Tools", "the model", "<code>@mcp.tool</code> with <code>ToolAnnotations</code> (read-only, destructive)", "<code>list_tools</code>, <code>call_tool</code>"],
  ["Resources", "the application", "<code>lab://notes</code>, template <code>lab://notes/{{note_id}}</code>, dynamic <code>lab://clock</code>", "<code>list_resources</code>, <code>list_resource_templates</code>, <code>read_resource</code>"],
  ["Prompts", "the person", "<code>@mcp.prompt explain(concept, level)</code>", "<code>list_prompts</code>, <code>get_prompt</code>"],
  ["Sampling", "the client's model", "<code>Resolve(ask_client_model)</code> returning <code>Sample(...)</code>", "<code>sampling_callback</code>"],
  ["Roots", "the client's policy", "<code>Resolve(ask_roots)</code> returning <code>ListRoots()</code>", "<code>list_roots_callback</code>"],
  ["Elicitation", "the person", "<code>Resolve(confirm_delete)</code> returning <code>Elicit(...)</code>", "<code>elicitation_callback</code>"],
  ["Progress", "the server", "<code>ctx.report_progress(i, n, message)</code>", "<code>progress_callback=</code> on <code>call_tool</code>"],
])}
{key("Run it in five minutes", "<code>pip install -r requirements.txt</code>, then <code>python client.py</code>: the client launches the server over stdio and walks through twelve steps. Then <code>python server.py --transport streamable-http</code> in one terminal and <code>python client.py --transport http</code> in another. <code>python wire_trace.py stdio</code> and <code>... http</code> show the raw bytes. <code>pytest -q</code> proves all of it.")}
<p>The whole server is under 250 lines. Read it once now, then come back to each part below.</p>
{fold("server.py", "python", "ai/mcp-primitives-lab/server.py")}
'''))

# ------------------------------------------------------------------ 2 flags
parts.append(sec("flags", "Part one · Orientation", "The flags to keep track of.", f'''
<p>A host keeps a small amount of state per connection, and most bugs come from getting one of these wrong. The client in this lab keeps them in a dictionary called <code>FLAGS</code> and prints it when the session ends.</p>
{table(["Flag", "Where it is set", "Why it matters"], [
  ["<code>protocol_version</code>", "<code>server/discover</code> result (<code>supportedVersions</code>), or the <code>initialize</code> reply", "decides which of the rules below apply"],
  ["<code>server_capabilities</code>", "the same reply: <code>tools</code>, <code>resources</code> (<code>subscribe</code>, <code>listChanged</code>), <code>prompts</code>", "never call what was not offered"],
  ["client capabilities", "implied by the callbacks you register: <code>sampling</code>, <code>roots</code>, <code>elicitation</code>", "the server may only ask for what you declared"],
  ["<code>initialized</code>", "legacy only: after <code>notifications/initialized</code>", "before it, only <code>ping</code> and logging are allowed"],
  ["<code>_meta</code> on every request", "modern only: version, clientInfo, clientCapabilities", "replaces per-connection state; this is what makes stateless HTTP possible"],
  ["<code>Mcp-Session-Id</code>", "legacy HTTP: a header on the <code>initialize</code> reply", "echo it on every later request; <code>DELETE</code> ends the session"],
  ["<code>MCP-Protocol-Version</code>, <code>Mcp-Method</code>, <code>Mcp-Name</code>", "modern HTTP request headers", "the transport routes and validates before the body is parsed; header and body must agree"],
  ["<code>requestState</code>", "an <code>input_required</code> result", "opaque and encrypted; send it back unchanged on the retry, with <code>inputResponses</code>"],
])}
<p>This is the dictionary as the client printed it after a full run over stdio. Each ask counter is one, because the server asked for the model once, for the roots once and for the person once; the three progress notifications came from <code>count</code>.</p>
{flow(part(V_CLIENT, "FLAGS after the session"))}
'''))

# ------------------------------------------------------------------ 3 handshake modern
parts.append(sec("discover", "Part two · The wire", "Handshake A (2026-07-28): server/discover, then _meta on every request.", f'''
<p>These are the exact bytes <code>wire_trace.py stdio</code> wrote to the server's stdin and read from its stdout, one JSON-RPC message per line. No SDK is involved on the client side. Watch three things: the request id comes back on the reply; the client declares its version and capabilities inside <code>_meta</code>, and does so again on every later request; and there is no <code>notifications/initialized</code> at all.</p>
{flow(part(V_WSTDIO, "-- A. modern handshake", "-- B. legacy handshake"))}
{key("Why the version rides on every request", "Nothing about the connection is remembered between requests. A server can therefore run stateless behind a load balancer, and a client can cache the <code>server/discover</code> result for <code>ttlMs</code> and skip it next time. The same design is why sampling, roots and elicitation had to change: see <a href='#rounds'>input-required rounds</a>.")}
'''))

# ------------------------------------------------------------------ 4 handshake legacy
parts.append(sec("initialize", "Part two · The wire", "Handshake B (2025-11-25): initialize, reply, notifications/initialized.", f'''
<p>Send an <code>initialize</code> request to the same server and it answers on the older protocol, whatever version you proposed. This is the three-step handshake most hosts still speak in 2026: the client proposes a version and capabilities, the server confirms a version and offers its own, and the client closes the handshake with a notification. Only after that notification may normal requests flow; before it, only <code>ping</code> and logging are allowed.</p>
{flow(part(V_WSTDIO, "-- B. legacy handshake"))}
{note("<b>Both handshakes, one server.</b> The SDK's <code>MCPServer</code> answers <code>server/discover</code> and <code>initialize</code> alike, so a server you write today works with a host from last year. The client run below negotiated 2026-07-28; the trace's part B negotiated 2025-11-25 against the same server file.")}
'''))

# ------------------------------------------------------------------ 5 HTTP
parts.append(sec("http", "Part two · The wire", "Streamable HTTP: one endpoint, three headers, and when SSE appears.", f'''
<p>Over HTTP every client message is a <code>POST</code> to one URL. The server answers with plain JSON when there is nothing to stream, or with a <code>text/event-stream</code> body when it may need to send several messages before the result. The client must accept both. On the modern protocol three request headers carry the flags, so a proxy can route and validate without parsing the body: <code>MCP-Protocol-Version</code>, <code>Mcp-Method</code> (which must equal the JSON-RPC method) and <code>Mcp-Name</code> (the tool). The trace sends the first request without them, on purpose, to show what happens.</p>
{flow(part(V_WHTTP, "-- A. modern", "-- B. legacy"))}
<p>The legacy path over HTTP adds a session. The <code>initialize</code> reply carries <code>Mcp-Session-Id</code>; every later request must echo it or the server refuses with <code>400 Missing session ID</code>; a notification is acknowledged with <code>202 Accepted</code> and an empty body; a <code>GET</code> with <code>Accept: text/event-stream</code> opens the standalone stream the server uses for server-initiated messages; <code>DELETE</code> ends the session.</p>
{flow(part(V_WHTTP, "-- B. legacy"))}
{table(["Server flag", "Effect", "When to use it"], [
  ["default (stateful)", "issues <code>Mcp-Session-Id</code> on <code>initialize</code>; keeps a session per client; SSE responses", "one process, hosts that speak 2025-11-25, long tool calls with progress"],
  ["<code>--stateless</code>", "no session id; every request stands alone", "behind a load balancer or serverless, modern clients only"],
  ["<code>--json-response</code>", "answers <code>application/json</code> instead of an SSE stream", "simple clients, gateways that cannot read SSE; you lose progress mid-call"],
])}
{fold("wire_trace.py", "python", "ai/mcp-primitives-lab/wire_trace.py")}
'''))

# ------------------------------------------------------------------ 6 tools
parts.append(sec("tools", "Part three · The server", "Tools: the contract is the schema, the annotations and the description.", f'''
<p>A tool is a function whose signature becomes <code>inputSchema</code>, whose docstring becomes the description the model reads, and whose return type becomes <code>outputSchema</code> and <code>structuredContent</code>. Annotations are hints for the host, not permissions: a host may ask before a <code>destructiveHint</code> tool and skip the question for a <code>readOnlyHint</code> one.</p>
{code(between(SERVER, "READ_ONLY = ToolAnnotations", "class Negotiation"))}
<p><code>negotiation</code> is the tool that makes the flags visible from the server's side. <code>Context</code> gives a tool the negotiated version, the client's declared capabilities, the request id, and, over HTTP, the request headers.</p>
{code(between(SERVER, "class Negotiation(BaseModel)", COUNT_MARK))}
<p><code>count</code> shows the notification channel that remains in 2026-07-28. Progress carries a number, a total and a human-readable message; the separate logging channel is deprecated, so operators' logs go to stderr, never to stdout, which on stdio is the protocol channel.</p>
{code(between(SERVER, COUNT_MARK, "# --- Server-to-client asks"))}
{key("Errors are results", "A <code>ToolError</code> becomes <code>isError: true</code> with the message in <code>content</code>, and the connection stays up. The client run's step 12 shows it: the model can read the message and try again. Reserve JSON-RPC errors for protocol problems, not for a bad argument.")}
'''))

# ------------------------------------------------------------------ 7 rounds
parts.append(sec("rounds", "Part three · The server", "Sampling, roots and elicitation: input-required rounds.", f'''
<p>Up to 2025-11-25 a server that needed the client's model, roots or the person sent a JSON-RPC request <em>back</em> over the connection. That needs a back-channel: stdio, or the SSE stream of a stateful HTTP session. Since 2026-07-28 those asks are <b>input-required rounds</b>: the tool result says <code>resultType: "input_required"</code>, lists what it needs under <code>inputRequests</code>, and hands over an opaque <code>requestState</code>. The client answers by retrying the same call with <code>inputResponses</code>. No back-channel is needed, so it works over stateless HTTP.</p>
<p>In the Python SDK you declare the need with a <em>resolver</em>: a plain function that returns <code>Sample(...)</code>, <code>ListRoots()</code> or <code>Elicit(...)</code>. The framework runs the round trip and injects the answer as a tool argument that the model never sees and cannot fake.</p>
{code(between(SERVER, "# --- Server-to-client asks", "# ------------------------------------------------------------------ resources"))}
<p>On the wire, one such call is two round trips. This is the sampling round from the stdio trace, with the client's model answer built by hand:</p>
{flow(part(V_WSTDIO, "the server needs OUR model for this one", "server exited with code"))}
<p>The client side is three callbacks. A real host would show the sampling request to the person or filter it, then call its own model; this stub answers deterministically so the lab runs offline.</p>
{code(between(CLIENT, "# ------------------------------------------------------------------ server -> client callbacks", "async def on_log"))}
{note("<b>Why the model cannot fake a confirmation.</b> <code>delete_note</code> takes a <code>confirm</code> argument that is not in its input schema: the resolver fills it. The model sees <code>note_id</code> only. The person's answer travels in <code>inputResponses</code>, bound to the <code>requestState</code> the server issued, so a replayed or invented answer is rejected.", "warn")}
'''))

# ------------------------------------------------------------------ 8 resources
parts.append(sec("resources", "Part three · The server", "Resources and prompts.", f'''
<p>Resources are the application's context: the host decides what the model sees. A static URI, a template with a parameter, and a dynamic one that changes on every read cover the three shapes you meet. <code>add_note</code> changes the list and tells subscribed clients with <code>notify_resources_changed()</code>. Prompts are templates the <em>person</em> picks; here <code>explain</code> takes a concept and a level and returns the user message.</p>
{code(between(SERVER, "# ------------------------------------------------------------------ resources", "# ------------------------------------------------------------------ entry point"))}
<p>The client reads them like this, and the run shows the note list growing after <code>add_note</code>:</p>
{flow(part(V_CLIENT, "[08] resources", "[10] tools/call delete_note"))}
'''))

# ------------------------------------------------------------------ 9 client run
parts.append(sec("client", "Part four · The client", "The twelve-step walk-through, verified over stdio and over HTTP.", f'''
<p>The client is the host side: it owns the model, the roots policy, the person and the log. Its twelve steps go from the handshake to a deliberate error. Every line below was printed by <code>python client.py</code> on 17 September 2026 against the server above; the HTTP run is identical except for the connection line and the <code>transport</code> flag, and both are in the repository under <code>verified/</code>.</p>
{flow(V_CLIENT.split("FLAGS after the session")[0].rstrip())}
{fold("client.py", "python", "ai/mcp-primitives-lab/client.py")}
{key("Step 11 is not a bug", "<code>ping</code> answers <code>Method not found</code> on 2026-07-28. Liveness moved to the transport: a stdio child that is alive, an HTTP connection that answers. The client catches the error and says so, which is also how your host should treat any method the negotiated version does not have.")}
'''))

# ------------------------------------------------------------------ 10 tests
parts.append(sec("tests", "Part four · The client", "Tests: the same assertions on three transports.", f'''
<p>One function, <code>exercise_everything</code>, asserts every primitive. Three tests run it in memory (the client talks to the server object, no process), over a stdio subprocess (as Claude Desktop or Claude Code would launch it) and over Streamable HTTP (the server in a subprocess, the client by URL). Two more tests run both wire traces and check that the flags appear in their output.</p>
{flow(V_TEST)}
{fold("test_lab.py", "python", "ai/mcp-primitives-lab/test_lab.py")}
{note("<b>In-memory first.</b> <code>Client(server_object)</code> is the fastest way to test tool logic, and it still runs the real input-required rounds. Keep the subprocess and HTTP tests for the transport itself: framing, sessions, headers.")}
'''))

# ------------------------------------------------------------------ 11 check
parts.append(sec("check", "Reference", "Check yourself.", f'''
<p>Answer from memory, then open the trace to confirm.</p>
<details class="quiz"><summary>1. On 2026-07-28, where do the client's capabilities travel?</summary><p>In <code>_meta</code> on every request (<code>io.modelcontextprotocol/clientCapabilities</code>), not in a one-time <code>initialize</code>. That is what lets the server stay stateless.</p></details>
<details class="quiz"><summary>2. A tool result arrives with <code>resultType: "input_required"</code>. What does the client do?</summary><p>Answers each <code>inputRequests</code> entry with its own callback, then retries the same call with <code>inputResponses</code> and the unchanged <code>requestState</code>.</p></details>
<details class="quiz"><summary>3. Why does the raw HTTP trace get <code>400 Missing session ID</code> on its first request?</summary><p>It omitted the <code>MCP-Protocol-Version</code> header, so the server applied the older session rules, under which only <code>initialize</code> may arrive without a session id.</p></details>
<details class="quiz"><summary>4. Which three headers does a modern HTTP request carry, and what checks them?</summary><p><code>MCP-Protocol-Version</code>, <code>Mcp-Method</code> and, for tool calls, <code>Mcp-Name</code>. The transport validates them before the body is parsed; a mismatching <code>Mcp-Method</code> is refused.</p></details>
<details class="quiz"><summary>5. What answers a notification over HTTP?</summary><p><code>202 Accepted</code> with an empty body. Notifications have no id and get no JSON-RPC reply.</p></details>
<details class="quiz"><summary>6. Where must a stdio server write its logs?</summary><p>stderr. stdout is the protocol channel; one stray print corrupts the framing.</p></details>
<details class="quiz"><summary>7. What is the difference between a <code>readOnlyHint</code> and a permission?</summary><p>A hint is the server's claim, used by the host to decide whether to ask the person. Permissions are the host's decision. Never trust a hint from a server you do not control.</p></details>
<details class="quiz"><summary>8. What does <code>DELETE /mcp</code> with a session id do?</summary><p>Ends the legacy HTTP session; the id is invalid afterwards. Modern, session-less requests have nothing to delete.</p></details>
'''))

# ------------------------------------------------------------------ 12 next
parts.append(sec("next", "Reference", "Where to go next.", f'''
{key("Six lines to keep", "Three things a server offers, three it may ask for. The version and capabilities are flags, and on 2026-07-28 they travel with every request. Server asks are input-required rounds, not back-channel requests. Over HTTP: one endpoint, both media types accepted, three headers. stdout is sacred on stdio. Errors are results.")}
<ul>
  <li><a href="{GH}" target="_blank" rel="noopener">The lab on GitHub</a>: server, client, wire trace, tests and the verified outputs.</li>
  <li><a href="/academy/modules/2026/FSE/mcp-end-to-end.html">MCP end to end</a>: the full guide, the security model, and a planner server in Python, Java and Spring AI that validates before it saves.</li>
  <li><a href="https://modelcontextprotocol.io/specification/2026-07-28/changelog" target="_blank" rel="noopener">The 2026-07-28 changelog</a> and the <a href="https://modelcontextprotocol.io/specification/2025-11-25" target="_blank" rel="noopener">2025-11-25 specification</a>; the <a href="https://py.sdk.modelcontextprotocol.io/v2/" target="_blank" rel="noopener">Python SDK 2</a> reference.</li>
  <li>On this site: <a href="/blog/posts/mcp-agent-integration.html">MCP for agent integrations</a> and <a href="/ai/#blueprint">the agent blueprint</a>.</li>
</ul>
<div class="cta" style="margin-top:22px">
  <div>
    <h3>Make it yours in an hour.</h3>
    <p>Replace <code>NOTES</code> with something you own, keep <code>negotiation</code> as your first tool, and add one resolver-backed tool that asks the person before it changes anything. Run the tests on all three transports before you show it to a host.</p>
  </div>
  <div class="actions" style="margin-top:0">
    <a class="btn primary" href="{GH}" target="_blank" rel="noopener">Clone the lab ↗</a>
    <a class="btn" href="/academy/modules/2026/FSE/mcp-end-to-end.html">Read the full guide</a>
  </div>
</div>
'''))

parts.append(FOOT)
io.open(OUT, "w", encoding="utf-8").write("".join(parts))
print("wrote", OUT, len("".join(parts)) // 1000, "KB")
