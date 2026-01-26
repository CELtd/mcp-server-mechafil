from __future__ import annotations
from typing import Any, Callable, Dict, Optional, Union, List
import os
import json
import requests

TokenProvider = Callable[[], Optional[str]]

HistoricalDataRequest = Dict[str, Any]
SimulationParams = Dict[str, Any]
ProvidePlotRequest = Dict[str, Any]


class EconolensClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        token_provider: Optional[TokenProvider] = None,
        session: Optional[requests.Session] = None,
        timeout: int = 45,
    ) -> None:
        default_base = os.environ.get("MCP_BASE_URL", "https://mechafil-mcp-server.fly.dev/mcp")
        self.base_url = (base_url or default_base).rstrip("/")
        self.token_provider = token_provider
        self.session = session or requests.Session()
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self.request_id = 0

    def fetch_context(self) -> str:
        result = self._call_tool("fetch_context")
        if not isinstance(result, str):
            raise RuntimeError("Unexpected response type for fetch_context")
        return result

    def get_historical_data(self, fields: Optional[Union[str, List[str]]] = None) -> Any:
        payload: HistoricalDataRequest = {}
        if fields is not None:
            payload["fields"] = fields
        return self._call_tool("get_historical_data", payload)

    def simulate(self, **params: Any) -> Any:
        return self._call_tool("simulate", params)

    def provide_plot(self, **params: Any) -> Any:
        return self._call_tool("provide_plot", params)

    def _ensure_session(self) -> None:
        if self.session_id:
            return

        self.request_id += 1
        req = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "econolens-sdk-py", "version": "0.1.0"},
            },
            "id": self.request_id,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        token = self.token_provider() if self.token_provider else None
        if token:
            headers["Authorization"] = f"Bearer {token}"

        resp = self.session.post(self.base_url, json=req, headers=headers, timeout=self.timeout)
        if not resp.ok:
            raise RuntimeError(f"MCP initialization failed: {resp.status_code} {resp.reason}")

        session_id = resp.headers.get("mcp-session-id")
        if not session_id:
            raise RuntimeError("No mcp-session-id header in initialization response")
        self.session_id = session_id

        # Optionally parse SSE data for errors
        text = resp.text
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                data = json.loads(line[6:])
                if data.get("error"):
                    raise RuntimeError(f"MCP initialization error: {data['error'].get('message')}")

        # Send notifications/initialized
        self.request_id += 1
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
            "id": self.request_id,
        }
        init_headers = dict(headers)
        init_headers["mcp-session-id"] = self.session_id
        self.session.post(self.base_url, json=notif, headers=init_headers, timeout=5)

    def _call_tool(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> Any:
        self._ensure_session()
        self.request_id += 1
        req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": args or {}},
            "id": self.request_id,
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": self.session_id or "",
        }
        token = self.token_provider() if self.token_provider else None
        if token:
            headers["Authorization"] = f"Bearer {token}"

        resp = self.session.post(self.base_url, json=req, headers=headers, timeout=self.timeout)
        if not resp.ok:
            raise RuntimeError(f"Tool call failed: {resp.status_code} {resp.reason} - {resp.text.strip()}")

        # MCP responses come as SSE lines; parse data lines
        text = resp.text
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("data: "):
                continue
            data = json.loads(line[6:])
            if "error" in data:
                msg = data["error"].get("message", "Unknown tool error")
                raise RuntimeError(f"Tool error: {msg}")
            result = data.get("result")
            if not result:
                continue
            # Prefer content text if present
            content = result.get("content")
            if isinstance(content, list) and content:
                first = content[0]
                if isinstance(first, dict) and "text" in first:
                    return first["text"]
            # Otherwise return result or data
            if "data" in result:
                return result["data"]
            return result

        raise RuntimeError("No result returned from MCP server")
