from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from llm import DummyLLM, OpenAIHTTP
from mcp_client import MCPClient
from types_ import ServerConfig


SYSTEM_PROMPT = """You are an MCP-enabled assistant.
Use tools when user asks for external actions/data. Keep answers concise and practical.
"""


def load_servers(path: str) -> list[ServerConfig]:
    data = json.loads(Path(path).read_text())
    servers = data.get("servers", [])
    return [
        ServerConfig(
            name=s["name"],
            command=s["command"],
            args=s.get("args", []),
            env=s.get("env", {}),
        )
        for s in servers
    ]


def tool_selection_policy(user_input: str) -> dict[str, Any] | None:
    """Simple placeholder policy.

    Supports explicit command format:
      run <server> <tool> <json_arguments>

    Examples:
      run filesystem read_file {"path":"/tmp/a.txt"}
    """
    if not user_input.startswith("run "):
        return None

    parts = user_input.split(" ", 3)
    if len(parts) < 4:
        raise ValueError("Expected: run <server> <tool> <json_arguments>")

    _, server, tool, raw_args = parts
    arguments = json.loads(raw_args)
    return {"server": server, "tool": tool, "arguments": arguments}


def interactive_loop(client: MCPClient, model_backend: str) -> None:
    llm = OpenAIHTTP() if model_backend == "openai" else DummyLLM()

    tools_by_server: dict[str, list[str]] = {}
    for server in list(client._processes.keys()):
        tools = client.list_tools(server)
        tools_by_server[server] = [t.name for t in tools]

    print("MCP Agent ready. Commands: 'list tools', 'run <server> <tool> <json>', 'exit'")

    while True:
        user_input = input("\nYou> ").strip()

        if user_input in {"exit", "quit"}:
            print("Goodbye.")
            return

        if user_input == "list tools":
            print(json.dumps(tools_by_server, indent=2))
            continue

        maybe_action = tool_selection_policy(user_input)
        if maybe_action:
            result = client.call_tool(
                server_name=maybe_action["server"],
                tool_name=maybe_action["tool"],
                arguments=maybe_action["arguments"],
            )
            print("Tool result>")
            print(json.dumps(result, indent=2))
            continue

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
        reply = llm.complete(messages)
        print(f"Agent> {reply}")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="MCP-enabled agent skeleton")
    parser.add_argument("--servers", default="config/servers.json", help="Path to server config JSON")
    parser.add_argument("--mode", default="interactive", choices=["interactive"], help="Runtime mode")
    parser.add_argument("--llm", default="dummy", choices=["dummy", "openai"], help="Model backend")

    args = parser.parse_args()

    server_configs = load_servers(args.servers)
    client = MCPClient()

    try:
        for cfg in server_configs:
            client.start_server(cfg)

        if args.mode == "interactive":
            interactive_loop(client, args.llm)
    finally:
        client.stop_all()


if __name__ == "__main__":
    main()
