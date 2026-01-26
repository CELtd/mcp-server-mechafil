# Econolens MCP SDK Plan (Month 4)

## Scope
- Client name: `EconolensClient`.
- Target interface: MCP server tools only — `fetch_context`, `get_historical_data`, `simulate`, `provide_plot` (no `simulate_full`).
- Purpose: typed, lightweight clients for non-LLM integrations that use the same contract LLMs see.

## Auth & Config
- `baseUrl`: default `https://mechafil-api.fly.dev`; override via env (e.g., `MCP_BASE_URL`).
- Optional `tokenProvider` hook; when provided, send `Authorization: Bearer <token>`. No token → no auth header.

## Repo Layout (here)
- `sdk/js/econolens-client/` — TypeScript client, types, README, examples.
- `sdk/python/econolens_client/` — Python client, README, examples.
- Contract tests colocated in each SDK folder; gated on env (skip if `MCP_BASE_URL` absent).

## Deliverables
1) JS/TS SDK
   - `EconolensClient` with methods: `fetchContext()`, `getHistoricalData({ fields? })`, `simulate(params)`, `providePlot(spec)`.
   - Typed params/results, normalized errors; optional `fetchImpl` for Node polyfill.
   - README + Node/browser examples; package entrypoints wired.
   - Contract test harness hitting live MCP (env-gated).
2) Python SDK
   - Matching `EconolensClient` API with `requests/httpx` session reuse.
   - README + minimal scripts.
   - Pytest contract tests (env-gated).
3) Scripts
   - JS: `pnpm test:contract` (or similar) in SDK folder.
   - Python: `pytest tests/contract` with marker/env guard.

## Testing Strategy
- Requires `MCP_BASE_URL` (and optional token env if auth is enabled later).
- Tests assert: context returns text; historical returns date keys + arrays; simulate returns `Explanation` + requested metric; provide_plot returns a `chart` object.
- Skip gracefully when env is missing to keep CI optional.

## Sequencing
1) Implement JS SDK + docs + contract tests.
2) Mirror in Python + docs + contract tests.
3) Wire npm/pytest scripts; optionally add CI job later (env-dependent).
