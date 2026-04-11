# MCP Playbook (What to know, what is necessary)

## 1) What MCP is

**MCP (Model Context Protocol)** is a standard way for AI agents/LLMs to connect to tools and data providers.

Think of MCP as:
- USB-C for AI tool integration.
- A common protocol so your agent can talk to many servers the same way.

Core ideas:
- **Client**: your agent app (this skeleton).
- **Server**: a tool/data provider exposing capabilities.
- **Transport**: often stdio for local process communication.
- **Protocol**: JSON-RPC messages with structured methods.

---

## 2) Minimal methods you should understand first

- `initialize`: handshake + capability negotiation.
- `tools/list`: discover available tools.
- `tools/call`: execute one tool with JSON arguments.

That is enough for a practical first implementation.

---

## 3) Implementation checklist (must-have)

1. **Transport framing**
   - Parse/write `Content-Length` headers correctly.
2. **Request IDs**
   - Match each response to the right request.
3. **Lifecycle**
   - Start server process, initialize, stop cleanly.
4. **Tool schema handling**
   - Validate user input against each tool's expected arguments.
5. **Error handling**
   - Handle protocol errors and subprocess crashes.
6. **Security controls**
   - Restrict allowed server commands and sensitive env vars.

---

## 4) Production hardening priorities

- Authentication between client and remote servers (if not local stdio).
- Authorization policies (which tools user/session may call).
- Timeouts and retries for flaky tools.
- Structured logs + tracing (request IDs, tool latency).
- Circuit breaker for unstable servers.
- Data governance (redaction, PII handling, audit logs).

---

## 5) Tool-calling strategies

### A) Explicit mode (best for reliability)
User writes explicit command (`run <server> <tool> {}`), agent executes directly.

### B) LLM planned mode
LLM chooses tool from tool list, generates arguments, executes, then summarizes.

Recommendation:
- Start with **Explicit mode**.
- Add **LLM planned mode** once observability and guardrails are in place.

---

## 6) Common mistakes to avoid

- Treating MCP as "just function calling" without robust transport handling.
- Not validating tool input (causes unsafe/unexpected operations).
- No timeout/cancellation path.
- Running too many servers from day one.
- Missing fallback when server is unavailable.

---

## 7) How to implement an MCP server (high-level)

An MCP server should:
1. Expose its tools metadata via `tools/list`.
2. Implement deterministic input parsing for each tool.
3. Return structured output for machine-readability.
4. Fail with clear error objects.
5. Keep side effects intentional and logged.

Best practice:
- Keep tools narrow and composable.
- Use JSON Schema for input rigor.
- Version tool names or arguments when breaking changes happen.

---

## 8) Reuse plan for new projects (very fast)

1. Copy `mcp-agent-skeleton/` into new repo.
2. Update `.env` and server config placeholders.
3. Start one MCP server.
4. Verify `list tools` works.
5. Verify one `run ...` call works.
6. Replace `DummyLLM` with your preferred model backend.
7. Add policy + observability before scaling.

This gives a repeatable launch path in minutes.
