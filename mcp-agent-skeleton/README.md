# MCP-Enabled Agent Skeleton (Reusable Template)

This is a **ready-to-clone skeleton** for building an MCP-enabled AI agent quickly.

You can reuse it fast by replacing placeholders in:

- `mcp-agent-skeleton/.env.example`
- `mcp-agent-skeleton/config/servers.example.json`
- `mcp-agent-skeleton/src/llm.py`
- `mcp-agent-skeleton/src/agent.py`

---

## What you get

- ✅ MCP stdio client implementation with JSON-RPC framing.
- ✅ Multi-server startup and graceful shutdown.
- ✅ Tool discovery (`tools/list`) from each server.
- ✅ Tool execution (`tools/call`) from agent runtime.
- ✅ Simple agent loop you can run now.
- ✅ Playbook docs for MCP concepts + implementation checklist.

---

## Quick start

```bash
cd mcp-agent-skeleton
cp .env.example .env
cp config/servers.example.json config/servers.json
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/agent.py --servers config/servers.json --mode interactive
```

### 1) Fill placeholders

- Set model API key in `.env`.
- Set MCP server commands in `config/servers.json`.

### 2) Start one MCP server first (recommended)

Keep it small first: one server + one tool.

### 3) Ask agent in interactive mode

Try:
- `list tools`
- `run <server> <tool> {"arg":"value"}`

---

## Architecture

```text
User
  ↓
Agent Loop (agent.py)
  ↓
Tool Router (routes to server + tool)
  ↓
MCP Client (mcp_client.py)
  ↓
MCP Server(s) via stdio subprocess
```

---

## Project layout

```text
mcp-agent-skeleton/
  README.md
  requirements.txt
  .env.example
  config/
    servers.example.json
  docs/
    MCP_PLAYBOOK.md
  src/
    agent.py
    llm.py
    mcp_client.py
    types_.py
```

---

## How to adapt quickly

1. Replace `DummyLLM` in `src/llm.py` with your preferred model provider.
2. Update `tool_selection_policy` in `src/agent.py` if you want auto tool use.
3. Add your MCP server config entries in `config/servers.json`.
4. Add guardrails, memory, and observability in the marked sections.

---

## Notes

- This skeleton is intentionally practical, lightweight, and easy to modify.
- For production, add auth, sandboxing, retries, structured logging, and policy checks.
