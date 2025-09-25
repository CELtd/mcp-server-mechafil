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
    """Get historical data from mechafil-server with configurable averaging.
    
    Returns historical data averaged over configurable time windows (weekly by default).
    Includes smoothed metrics, averaged arrays, and processed offline data.
    
    Returns:
        str: JSON string containing historical data with smoothed metrics,
             averaged arrays (raw_byte_power, renewal_rate, filplus_rate), 
             averaging method info, and processed offline data
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


### TODO: change the output, not a string but a structured result. Use a dictionary for output, so that the key can change depending on the input
@mcp.tool()
def simulate(
    rbp: Optional[Union[float, List[float]]] = None,
    rr: Optional[Union[float, List[float]]] = None,
    fpr: Optional[Union[float, List[float]]] = None,
    lock_target: Optional[Union[float, List[float]]] = None,
    forecast_length_days: Optional[int] = None,
    sector_duration_days: Optional[int] = None,
    output: Optional[Union[str, List[str]]] = None
) -> str:
    """Run a Filecoin forecast simulation with weekly averaged results.
    
    All parameters are optional with the following DEFAULT VALUES:
    - rbp: derived from historical data (smoothed average ~2.37 PIB/day)
    - rr: derived from historical data (smoothed average ~0.82)
    - fpr: derived from historical data (smoothed average ~0.79)
    - lock_target: 0.3 (30%)
    - forecast_length_days: 3650 days (10 years) - VERY LONG, consider specifying shorter!
    - sector_duration_days: 540 days
    
    Results are averaged over 7-day windows for more manageable data sizes.
    
    IMPORTANT: Default forecast is 10 years (3650 days) which may be too long!
    Recommended values: 90 (3 months), 365 (1 year), 1825 (5 years).
    
    Args:
        rbp: Raw byte power onboarding (PIB/day), constant or array (default: ~2.37)
        rr: Renewal rate (0..1), constant or array (default: ~0.82)
        fpr: FIL+ rate (0..1), constant or array (default: ~0.79)
        lock_target: Target lock ratio (e.g., 0.3), float or array (default: 0.3)
        forecast_length_days: Forecast length in days (default: 3650 - consider shorter!)
                              Recommended values: 90, 365, 1825
        sector_duration_days: Average sector duration in days (default: 540)
        output: Specific output field(s) to return. Examples:
                - Single field: "available_supply"
                - Multiple fields: ["available_supply", "network_RBP_EIB"]
                - If not specified, returns all simulation fields
                
    Available output fields include:
        - available_supply: Available FIL token supply
        - network_RBP_EIB: Network Raw Byte Power (EiB)
        - network_QAP_EIB: Network Quality Adjusted Power (EiB)
        - circ_supply: Circulating FIL supply
        - day_network_reward: Daily network rewards
        - network_locked: Total locked FIL
        - 1y_return_per_sector: One-year return per sector
        - 1y_sector_roi: One-year sector ROI
        - And many more economic and network metrics
    
    Returns:
        str: JSON string containing simulation results with weekly averaged data.
             Response includes input parameters, smoothed metrics, averaging method,
             and filtered simulation output based on 'output' parameter.
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
    if output is not None:
        payload["output"] = output
    
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


@mcp.tool()
def simulate_full(
    rbp: Optional[Union[float, List[float]]] = None,
    rr: Optional[Union[float, List[float]]] = None,
    fpr: Optional[Union[float, List[float]]] = None,
    lock_target: Optional[Union[float, List[float]]] = None,
    forecast_length_days: Optional[int] = None,
    sector_duration_days: Optional[int] = None
) -> str:
    """Run a Filecoin forecast simulation with full detailed daily results.
    
    This function provides complete daily-resolution simulation data, unlike the
    regular simulate() function which returns weekly averaged results. Use this
    when you need precise daily values for detailed analysis.
    
    All parameters are optional with the following DEFAULT VALUES:
    - rbp: derived from historical data (smoothed average ~2.37 PIB/day)
    - rr: derived from historical data (smoothed average ~0.82)
    - fpr: derived from historical data (smoothed average ~0.79)
    - lock_target: 0.3 (30%)
    - forecast_length_days: 3650 days (10 years) - TOO LONG for full detail!
    - sector_duration_days: 540 days
    
    WARNING: Default forecast is 10 years which creates MASSIVE daily data!
    For full simulations, use shorter periods: 90, 180, 365 days maximum.
    
    Args:
        rbp: Raw byte power onboarding (PIB/day), constant or array (default: ~2.37)
        rr: Renewal rate (0..1), constant or array (default: ~0.82)
        fpr: FIL+ rate (0..1), constant or array (default: ~0.79)
        lock_target: Target lock ratio (e.g., 0.3), float or array (default: 0.3)
        forecast_length_days: Forecast length in days (default: 3650 - AVOID for full detail!)
                              Recommended for full detail: 90, 180, 365 MAX
        sector_duration_days: Average sector duration in days (default: 540)
    
    Returns:
        str: JSON string containing full detailed simulation results with daily resolution.
             For a 365-day forecast, this returns 365 data points per array instead of 
             ~52 weekly averages. Use with caution for long forecasts due to data size.
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
            f"{MECHAFIL_SERVER_URL}/simulate/full",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=payload,
            timeout=120  # Longer timeout for full simulations
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