# Momentum Planner — an MCP server that validates before it saves

The worked example from the Academy guide **[MCP end to end](https://janaka.me/academy/modules/2026/FSE/mcp-end-to-end.html)**.
It is the pattern behind the AI planning feature in [Daily Momentum](https://daily-momentum.com/): any AI drafts a
plan, this server owns the contract, a deterministic validator and the store.

Three implementations of the same server, all built and run before publishing:

| Folder | Stack | Transport | Verified with |
|---|---|---|---|
| `python/` | Python 3.12+, `mcp` 2.2 (official SDK) | stdio and Streamable HTTP | `test_client.py`, `pytest` |
| `java/` | Java 21, MCP Java SDK 2.0 | stdio | the same `test_client.py` |
| `spring/` | Spring Boot 4, Spring AI 2.0, `@McpTool` | Streamable HTTP | an MCP client over HTTP |

Tools: `get_plan_contract` (read-only), `validate_plan` (read-only, deterministic, calls no model),
`save_plan` (refuses an invalid plan; asks before overwriting). Resource: `plan://{planId}`. Prompt: `draft-plan`.

## Python

```bash
cd python
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python momentum_planner.py                      # stdio
MCP_TRANSPORT=http python momentum_planner.py   # http://127.0.0.1:8765/mcp

python test_client.py                           # drives every feature over stdio
python -m pytest -q                             # validator unit tests + in-process end-to-end test
npx @modelcontextprotocol/inspector python momentum_planner.py   # browser UI
```

## Java (MCP Java SDK 2.0)

```bash
cd java && mvn -q package
java -jar target/momentum-planner.jar           # stdio; logs on stderr
cd ../python && PLANNER_CMD="java -jar ../java/target/momentum-planner.jar" python test_client.py
```

## Spring Boot + Spring AI 2.0

```bash
cd spring && mvn -q package -DskipTests
java -jar target/momentum-planner-spring-1.0.0.jar   # http://localhost:8766/mcp
```

## Use it from a host

```bash
# Claude Code
claude mcp add --transport stdio momentum-planner -- python3 "$PWD/python/momentum_planner.py"
```

```json
// Claude Desktop: claude_desktop_config.json
{ "mcpServers": { "momentum-planner": { "command": "python3", "args": ["/absolute/path/python/momentum_planner.py"] } } }
```

Saved plans land in `plans/` next to the server (override with `PLAN_STORE` for Python, `-Dplan.store=` for Java,
`planner.store` for Spring). Licensed like the rest of this repository.
