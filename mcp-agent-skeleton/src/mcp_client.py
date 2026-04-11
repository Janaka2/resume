from __future__ import annotations

import json
import os
import subprocess
import threading
from dataclasses import dataclass
from itertools import count
from typing import Any

from types_ import ServerConfig, ToolSpec


@dataclass
class MCPProcess:
    config: ServerConfig
    proc: subprocess.Popen


class MCPClient:
    """Minimal MCP stdio client with JSON-RPC over Content-Length framing."""

    def __init__(self) -> None:
        self._processes: dict[str, MCPProcess] = {}
        self._request_counter = count(1)
        self._read_locks: dict[str, threading.Lock] = {}
        self._write_locks: dict[str, threading.Lock] = {}

    def start_server(self, config: ServerConfig) -> None:
        if config.name in self._processes:
            raise ValueError(f"Server already started: {config.name}")

        env = os.environ.copy()
        env.update(config.env or {})

        proc = subprocess.Popen(
            [config.command, *config.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            env=env,
        )

        self._processes[config.name] = MCPProcess(config=config, proc=proc)
        self._read_locks[config.name] = threading.Lock()
        self._write_locks[config.name] = threading.Lock()

        self.request(config.name, "initialize", {"protocolVersion": "2024-11-05", "clientInfo": {"name": "mcp-agent-skeleton", "version": "0.1.0"}, "capabilities": {}})

    def stop_all(self) -> None:
        for name, entry in list(self._processes.items()):
            proc = entry.proc
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
            self._processes.pop(name, None)

    def list_tools(self, server_name: str) -> list[ToolSpec]:
        payload = self.request(server_name, "tools/list", {})
        tools = payload.get("tools", []) if isinstance(payload, dict) else []
        return [
            ToolSpec(
                name=t.get("name", ""),
                description=t.get("description", ""),
                input_schema=t.get("inputSchema", {}),
            )
            for t in tools
            if t.get("name")
        ]

    def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.request(server_name, "tools/call", {"name": tool_name, "arguments": arguments})

    def request(self, server_name: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if server_name not in self._processes:
            raise ValueError(f"Unknown server: {server_name}")

        proc = self._processes[server_name].proc
        if proc.stdin is None or proc.stdout is None:
            raise RuntimeError(f"Broken stdio pipes for server {server_name}")

        request_id = next(self._request_counter)
        body = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        message = json.dumps(body).encode("utf-8")
        frame = f"Content-Length: {len(message)}\r\n\r\n".encode("utf-8") + message

        with self._write_locks[server_name]:
            proc.stdin.write(frame)
            proc.stdin.flush()

        with self._read_locks[server_name]:
            response = self._read_message(proc.stdout)

        if response.get("id") != request_id:
            raise RuntimeError(f"Request/response id mismatch for {server_name}: {response}")

        if "error" in response:
            raise RuntimeError(f"MCP error from {server_name}: {response['error']}")

        return response.get("result", {})

    @staticmethod
    def _read_message(stdout: Any) -> dict[str, Any]:
        headers: dict[str, str] = {}
        while True:
            line = stdout.readline()
            if not line:
                raise RuntimeError("Server closed stdout while waiting for headers")
            if line in (b"\r\n", b"\n"):
                break
            key, _, value = line.decode("utf-8").partition(":")
            headers[key.strip().lower()] = value.strip()

        content_length = int(headers.get("content-length", "0"))
        if content_length <= 0:
            raise RuntimeError(f"Invalid content-length header: {headers}")

        body = stdout.read(content_length)
        if not body:
            raise RuntimeError("Empty JSON-RPC body")

        return json.loads(body.decode("utf-8"))
