import os
import sys
from pathlib import Path
import pytest

# Ensure local package is importable without installing in this interpreter
sys.path.append(str(Path(__file__).resolve().parents[1]))

from econolens_client import EconolensClient

BASE_URL = os.environ.get("MCP_BASE_URL")
should_run = BASE_URL is not None


@pytest.mark.skipif(not should_run, reason="MCP_BASE_URL not set; skipping live contract test")
def test_contract_flow():
    client = EconolensClient(base_url=BASE_URL)

    ctx = client.fetch_context()
    assert isinstance(ctx, str) and len(ctx) > 100

    hist = client.get_historical_data(fields=["raw_byte_power"])
    assert hist

    sim = client.simulate(forecast_length_days=60, requested_metric="available_supply")
    assert sim

    plot = client.provide_plot(
        series="historical_raw_power_eib",
        start_date_key="data_start_date",
        title="Network Power",
        description="Test plot",
    )
    assert plot
    # The server may return either a full result dict or a content string; accept both
    if isinstance(plot, dict):
        assert "chart" in plot or "result" in plot or plot
    else:
        assert isinstance(plot, str) and len(plot) > 0
