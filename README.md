# MCP Mechafil Server

MCP server providing tools to interact with the mechafil-server API endpoints.

## Tools

### `get_historical_data()`
Get historical data from mechafil-server with configurable averaging (weekly by default).
Returns smoothed metrics, averaged arrays, and offline data.

### `simulate(...)`
Run Filecoin forecast simulations with weekly averaged results for manageable data sizes.

**Parameters:**
- `rbp`: Raw byte power onboarding (PIB/day)
- `rr`: Renewal rate (0..1)
- `fpr`: FIL+ rate (0..1)
- `lock_target`: Target lock ratio (e.g., 0.3)
- `forecast_length_days`: Forecast length in days
- `sector_duration_days`: Average sector duration in days
- `output`: Filter results to specific field(s) - single string or list of strings

**Output filtering examples:**
- `output="available_supply"` - Returns only available supply data
- `output=["available_supply", "network_RBP_EIB"]` - Returns multiple specific fields
- `output=None` (default) - Returns all simulation fields

### `simulate_full(...)`
Run Filecoin forecast simulations with full detailed daily results.
Same parameters as `simulate()` but returns daily resolution data instead of weekly averages.
Use for detailed analysis when precise daily values are needed.

**Available output fields:**
- `available_supply`: Available FIL token supply
- `network_RBP_EIB`: Network Raw Byte Power (EiB)
- `network_QAP_EIB`: Network Quality Adjusted Power (EiB)
- `circ_supply`: Circulating FIL supply
- `day_network_reward`: Daily network rewards
- `network_locked`: Total locked FIL
- `1y_return_per_sector`: One-year return per sector
- `1y_sector_roi`: One-year sector ROI
- And 40+ more economic and network metrics

## Installation

### Using uv (recommended)

```bash
# Install dependencies
uv sync

# Run the server
uv run python server.py
```

## TEsting the server
```bash
uv run mcp dev server.py 
```
Open the inspector with the token pre-filled


## Configuration

Set the `MECHAFIL_SERVER_URL` environment variable to specify the mechafil-server URL (defaults to `http://localhost:8000`).