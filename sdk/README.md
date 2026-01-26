# Econolens MCP SDKs

Two thin clients for the Econolens MCP server (JSON-RPC over HTTP/SSE):
- **JS/TS**: `sdk/js/econolens-client`
- **Python**: `sdk/python/econolens_client`

Default MCP endpoint: `https://mechafil-mcp-server.fly.dev/mcp` (override with `MCP_BASE_URL`). Optional `tokenProvider`/`token_provider` lets you add `Authorization: Bearer <token>` when auth is enabled.

## JavaScript / TypeScript

Install (from package dir):
```bash
cd sdk/js/econolens-client
pnpm install
pnpm build
```

Use:
```ts
import { EconolensClient } from 'econolens-client';

const client = new EconolensClient({
  baseUrl: process.env.MCP_BASE_URL || 'https://mechafil-mcp-server.fly.dev/mcp',
  tokenProvider: async () => null, // optional bearer
});

const ctx  = await client.fetchContext();
const hist = await client.getHistoricalData({ fields: ['raw_byte_power'] });
const sim  = await client.simulate({ forecast_length_days: 180, requested_metric: 'available_supply' });
const plot = await client.providePlot({ series: 'historical_raw_power_eib', start_date_key: 'data_start_date' });
```

Contract test (hits live MCP):
```bash
cd sdk/js/econolens-client
MCP_BASE_URL=https://mechafil-mcp-server.fly.dev/mcp pnpm test:contract
```

Example:
```bash
cd sdk/js/econolens-client
pnpm build
node examples/simple.js
```

## Python

Install locally:
```bash
cd sdk/python
python3 -m pip install --user .
```

Use:
```py
from econolens_client import EconolensClient
import os

client = EconolensClient(
    base_url=os.environ.get("MCP_BASE_URL", "https://mechafil-mcp-server.fly.dev/mcp"),
    token_provider=None,  # optional callable returning bearer
)

ctx  = client.fetch_context()
hist = client.get_historical_data(fields=["raw_byte_power"])
sim  = client.simulate(forecast_length_days=180, requested_metric="available_supply")
plot = client.provide_plot(series="historical_raw_power_eib", start_date_key="data_start_date")
```

Contract test:
```bash
cd sdk/python
MCP_BASE_URL=https://mechafil-mcp-server.fly.dev/mcp PYTHONPATH=. pytest tests/contract_test.py
```

Example:
```bash
cd sdk/python
python3 examples/simple.py
```

## Notes
- Protocol: MCP JSON-RPC with session init (`initialize` + `notifications/initialized`) and `tools/call` for `fetch_context`, `get_historical_data`, `simulate`, `provide_plot`.
- Defaults are MCP-only (no direct REST calls to mechafil API). Adjust `baseUrl` if the deployment changes.
- Auth: pass a token provider to add a bearer header when the server enforces auth.

## Run all contract tests (helper script)
```bash
cd sdk
MCP_BASE_URL=https://mechafil-mcp-server.fly.dev/mcp ./run-contract-tests.sh
```
Requires MCP server access; skips with a message if `MCP_BASE_URL` is unset.

## CI
- Workflow: `.github/workflows/sdk-contract-tests.yml`
- Requires repo secret `MCP_BASE_URL` pointing to the MCP server (e.g., `https://mechafil-mcp-server.fly.dev/mcp`).
- Runs JS (pnpm) and Python (pytest) contract suites; skips gracefully if the secret is absent.
