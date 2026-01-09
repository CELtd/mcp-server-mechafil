#!/usr/bin/env bash
set -euo pipefail

: "${MECHAFIL_SERVER_URL:=http://localhost:8000}"
: "${MCP_TRANSPORT:=http}"
: "${PORT:=8081}"

export MECHAFIL_SERVER_URL
export MCP_TRANSPORT
export PORT

if command -v lsof >/dev/null 2>&1; then
  if lsof -iTCP:"${PORT}" -sTCP:LISTEN -n -P >/dev/null 2>&1; then
    echo "Port ${PORT} is already in use. Set PORT to a free port and retry." >&2
    exit 1
  fi
fi

uv run python server.py
