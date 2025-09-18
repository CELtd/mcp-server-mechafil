"""MCP server for mechafil-server API endpoints."""

import json
import os
from typing import Dict, List, Optional, Union, Any
import requests
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

# Server configuration
MECHAFIL_SERVER_URL = os.getenv("MECHAFIL_SERVER_URL", "http://localhost:8000")

# Create MCP server
mcp = FastMCP("mechafil-server")


@mcp.tool()
def get_historical_data() -> str:
    """Get complete historical data from mechafil-server including smoothed metrics, 
    historical arrays, and offline data.
    
    Returns:
        str: JSON string containing complete historical data with smoothed metrics,
             historical arrays (raw_byte_power, renewal_rate, filplus_rate), and offline_data
    """
    try:
        response = requests.get(
            f"{MECHAFIL_SERVER_URL}/historical-data",
            headers={"Accept": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        return json.dumps(response.json())
    
    except requests.exceptions.ConnectionError:
        return json.dumps({
            "error": "Connection failed",
            "message": f"Could not connect to mechafil-server at {MECHAFIL_SERVER_URL}",
            "suggestion": "Make sure mechafil-server is running"
        })
    except requests.exceptions.HTTPError as e:
        return json.dumps({
            "error": f"HTTP {response.status_code}",
            "message": str(e),
            "response": response.text if response else None
        })
    except Exception as e:
        return json.dumps({
            "error": "Unexpected error",
            "message": str(e)
        })


@mcp.tool()
def simulate(
    rbp: Optional[Union[float, List[float]]] = None,
    rr: Optional[Union[float, List[float]]] = None,
    fpr: Optional[Union[float, List[float]]] = None,
    lock_target: Optional[Union[float, List[float]]] = None,
    forecast_length_days: Optional[int] = None,
    sector_duration_days: Optional[int] = None
) -> str:
    """Run a Filecoin forecast simulation using mechafil-server.
    
    All parameters are optional; defaults are derived from historical data.
    
    Args:
        rbp: Raw byte power onboarding (PIB/day), constant or array
        rr: Renewal rate (0..1), constant or array  
        fpr: FIL+ rate (0..1), constant or array
        lock_target: Target lock ratio (e.g., 0.3), float or array
        forecast_length_days: Forecast length in days
        sector_duration_days: Average sector duration in days
    
    Returns:
        str: JSON string containing simulation results with input parameters,
             smoothed metrics, and simulation output arrays
    """
    # Build request payload, excluding None values
    payload = {}
    if rbp is not None:
        payload["rbp"] = rbp
    if rr is not None:
        payload["rr"] = rr
    if fpr is not None:
        payload["fpr"] = fpr
    if lock_target is not None:
        payload["lock_target"] = lock_target
    if forecast_length_days is not None:
        payload["forecast_length_days"] = forecast_length_days
    if sector_duration_days is not None:
        payload["sector_duration_days"] = sector_duration_days
    
    try:
        response = requests.post(
            f"{MECHAFIL_SERVER_URL}/simulate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return json.dumps(response.json())
    
    except requests.exceptions.ConnectionError:
        return json.dumps({
            "error": "Connection failed", 
            "message": f"Could not connect to mechafil-server at {MECHAFIL_SERVER_URL}",
            "suggestion": "Make sure mechafil-server is running"
        })
    except requests.exceptions.HTTPError as e:
        return json.dumps({
            "error": f"HTTP {response.status_code}",
            "message": str(e),
            "response": response.text if response else None
        })
    except Exception as e:
        return json.dumps({
            "error": "Unexpected error",
            "message": str(e)
        })


if __name__ == "__main__":
    mcp.run(transport="stdio")