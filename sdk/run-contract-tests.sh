#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${MCP_BASE_URL:-}" ]]; then
  echo "MCP_BASE_URL is required to run contract tests." >&2
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pushd "$SCRIPT_DIR/js/econolens-client" >/dev/null
pnpm test:contract
popd >/dev/null

pushd "$SCRIPT_DIR/python" >/dev/null
PYTHONPATH=. pytest tests/contract_test.py
popd >/dev/null
