# Econolens MCP Client (JS/TS)

Thin JS/TS client for the Econolens MCP server tools (via MCP JSON-RPC over HTTP/SSE): `fetch_context`, `get_historical_data`, `simulate`, `provide_plot`.

## Install

```bash
pnpm add econolens-client
# or npm/yarn
```

## Usage

```ts
import { EconolensClient } from 'econolens-client';

const client = new EconolensClient({
  baseUrl: process.env.MCP_BASE_URL || 'https://mechafil-mcp-server.fly.dev/mcp',
  // optional auth
  tokenProvider: async () => null, // return a bearer token if needed
});

const context = await client.fetchContext();
const hist = await client.getHistoricalData({ fields: ['raw_byte_power'] });
const sim = await client.simulate({ forecast_length_days: 180, requested_metric: 'available_supply' });
const plot = await client.providePlot({
  series: 'historical_raw_power_eib',
  start_date_key: 'data_start_date',
  title: 'Network Power',
});
```

## API
- `fetchContext(): Promise<string>`
- `getHistoricalData({ fields? })`
- `simulate(params)`
- `providePlot(spec)`

Options:
- `baseUrl` (default `https://mechafil-api.fly.dev`)
- `tokenProvider?: () => Promise<string | null>`
- `fetchImpl?: typeof fetch` (pass a polyfill for Node <18)

## Testing

Contract test (hits live MCP):
```bash
MCP_BASE_URL=https://mechafil-api.fly.dev pnpm test:contract
```
Skips if `MCP_BASE_URL` is unset. Requires network access to the MCP server.
