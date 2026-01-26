import os
from econolens_client import EconolensClient

client = EconolensClient(
    base_url=os.environ.get("MCP_BASE_URL", "https://mechafil-mcp-server.fly.dev/mcp"),
    token_provider=None,
)

ctx = client.fetch_context()
print("Context length:", len(ctx))

hist = client.get_historical_data(fields=["raw_byte_power"])
print("Hist keys:", list(hist.keys()) if isinstance(hist, dict) else type(hist))

sim = client.simulate(forecast_length_days=90, requested_metric="available_supply")
print("Sim keys:", list(sim.keys()) if isinstance(sim, dict) else type(sim))

plot = client.provide_plot(
    series="historical_raw_power_eib",
    start_date_key="data_start_date",
    title="Network Power",
)
print("Plot response type:", type(plot))
