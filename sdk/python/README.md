# Econolens MCP Client (Python)

Thin Python client for the Econolens MCP server tools: `fetch_context`, `get_historical_data`, `simulate`, `provide_plot`.

## Quickstart

```bash
cd sdk/python
python3 -m pip install --user .
```

## Usage

```python
from econolens_client import EconolensClient
import os

client = EconolensClient(
    base_url=os.environ.get("MCP_BASE_URL", "https://mechafil-mcp-server.fly.dev/mcp"),
    token_provider=None,  # optional callable returning a bearer token
)

context = client.fetch_context()
hist = client.get_historical_data(fields=["raw_byte_power"])
sim = client.simulate(forecast_length_days=180, requested_metric="available_supply")
plot = client.provide_plot(
    series="historical_raw_power_eib",
    start_date_key="data_start_date",
    title="Network Power",
)
```

## Testing (contract)
```bash
cd sdk/python
MCP_BASE_URL=https://mechafil-mcp-server.fly.dev/mcp PYTHONPATH=. pytest tests/contract_test.py
```
