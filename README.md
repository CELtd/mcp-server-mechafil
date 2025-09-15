# MCP Mechafil Server

MCP server providing tools to interact with the mechafil-server API endpoints.

## Tools

- `get_historical_data_full`: Get complete historical data from mechafil-server
- `simulate`: Run Filecoin forecast simulations

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