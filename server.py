"""MCP server for mechafil-server API endpoints."""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Annotated
from pydantic import BaseModel, Field
import requests
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult

# Server configuration
MECHAFIL_SERVER_URL = os.getenv("MECHAFIL_SERVER_URL", "https://mechafil-api.fly.dev")
SYSTEM_PROMPT_PATH = Path(__file__).with_name("system-prompt.txt")
SYSTEM_PROMPT_INCLUDE_PATTERN = re.compile(r"\{\{\s*include:(?P<path>[^}]+)\}\}")


def _render_system_prompt(template_path: Path) -> str:
    """Load the template prompt and replace include placeholders with file contents."""
    try:
        template_text = template_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"System prompt template not found at {template_path}. Ensure the repository is intact."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to load system prompt template: {exc}") from exc

    def _include(match: re.Match) -> str:
        relative_path = match.group("path").strip()
        include_path = (template_path.parent / relative_path).resolve()

        def _read(path: Path) -> str:
            try:
                return path.read_text(encoding="utf-8").strip()
            except Exception as exc:  # pragma: no cover - bubble up with context
                raise RuntimeError(
                    f"Failed to load included file '{relative_path}' for system prompt: {exc}"
                ) from exc

        if include_path.exists():
            content = _read(include_path)
            return f"{content}\n"

        # Fallback: auto-convert .md files to .txt when requested.
        relative_path_obj = Path(relative_path)
        fallback_tried = False
        if relative_path_obj.suffix.lower() == ".txt":
            md_candidate = (template_path.parent / relative_path_obj.with_suffix(".md")).resolve()
            fallback_tried = True
            if md_candidate.exists():
                content = _read(md_candidate)
                try:
                    include_path.write_text(content, encoding="utf-8")
                except Exception:
                    # If writing fails, we still return the content so the prompt renders.
                    pass
                return f"{content}\n"

        raise FileNotFoundError(
            f"Included file not found for system prompt: {relative_path} "
            f"(resolved to {include_path})"
            + (" and no .md fallback was available." if fallback_tried else ".")
        )

    rendered = SYSTEM_PROMPT_INCLUDE_PATTERN.sub(_include, template_text)
    if SYSTEM_PROMPT_INCLUDE_PATTERN.search(rendered):
        raise RuntimeError(
            "System prompt rendering incomplete: unresolved include placeholder detected."
        )
    return rendered


# Create MCP server
mcp = FastMCP("mechafil-server")


@mcp.tool(annotations={"title": "Fetch System Prompt Context"})
def fetch_context() -> str:
    """Return the authoritative system prompt text with dynamic documentation inserts.

    Call once at startup (per session) before any other tool.
    """
    # Wake the mechafil API so downstream calls don't pay the cold-start penalty.
    try:
        health_url = f"{MECHAFIL_SERVER_URL.rstrip('/')}/health"
        requests.get(health_url, timeout=5)
    except Exception:
        # Intentionally swallow errors; the caller only needs the prompt text.
        pass

    try:
        return _render_system_prompt(SYSTEM_PROMPT_PATH)
    except FileNotFoundError as exc:
        raise FileNotFoundError(str(exc)) from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to render system prompt: {exc}") from exc

class SimulationInputs(BaseModel):
    """Parameters for Filecoin economic simulation. All fields are optional with intelligent defaults."""
    
    rbp: Annotated[
        Optional[Union[float, List[float]]],
        Field(
            description="""Raw Byte Power onboarding in EiB/day. Float for constant or list for time-varying (len = forecast_length_days). Defaults to recent median if omitted."""
        )
    ] = None

    rr: Annotated[
        Optional[Union[float, List[float]]],
        Field(
            description="""Renewal rate (0..1). Float or list (len = forecast_length_days). Defaults to recent median if omitted."""
        )
    ] = None

    fpr: Annotated[
        Optional[Union[float, List[float]]],
        Field(
            description="""FIL+ rate (0..1). Float or list (len = forecast_length_days). Defaults to recent median if omitted."""
        )
    ] = None

    lock_target: Annotated[
        Optional[Union[float, List[float]]],
        Field(
            description="""Target lock ratio (0..1). Float or list (len = forecast_length_days). Default 0.3."""
        )
    ] = None

    forecast_length_days: Annotated[
        Optional[int],
        Field(
            description="""Forecast horizon in days. Always set explicitly from the user's time horizon; default is 3650 (10 years)."""
        )
    ] = None

    sector_duration_days: Annotated[
        Optional[int],
        Field(
            description="""Average sector duration in days (default 540)."""
        )
    ] = None

    requested_metric: Annotated[
        Optional[str],
        Field(
            description=(
                "Metric name to return (default '1y_sector_roi'). Use the exact API metric "
                "identifier; if unsure, ask the user to choose from a short list."
            )
        )
    ] = None


class HistoricalDataRequest(BaseModel):
    """Optional filters for historical data tool."""

    fields: Annotated[
        Optional[Union[str, List[str]]],
        Field(
            default=None,
            description=(
                "Optional field(s) to include in the response. For plot requests, "
                "always use this to return only the requested series (single string or list)."
            )
        )
    ] = None


class PlotSeries(BaseModel):
    """Single series configuration for chart output."""

    name: Annotated[
        str,
        Field(
            description=(
                "Series field name from get_historical_data or simulation output. "
                "Use historical_* for network totals and raw_byte_power for onboarding rate."
            )
        )
    ]
    label: Annotated[
        Optional[str],
        Field(default=None, description="Optional display label for the series.")
    ] = None
    unit: Annotated[
        Optional[str],
        Field(default=None, description="Optional unit label for the series.")
    ] = None


class ProvidePlotRequest(BaseModel):
    """Build a strict chart specification for the UI to render."""

    series: Annotated[
        Union[str, PlotSeries, List[Union[str, PlotSeries]]],
        Field(description="Series name(s) or series descriptors to plot.")
    ]
    start_date_key: Annotated[
        Optional[str],
        Field(default="data_start_date", description="Metadata key for the series start date.")
    ] = "data_start_date"
    title: Annotated[
        Optional[str],
        Field(default=None, description="Optional chart title.")
    ] = None
    description: Annotated[
        Optional[str],
        Field(default=None, description="Optional chart description.")
    ] = None


@mcp.tool(annotations={"title": "Run Filecoin Economic Forecast Simulation"})
def simulate(sim: SimulationInputs) -> dict:
    """Run a MechaFil simulation via `/simulate`.

    - Always align `forecast_length_days` with the user's horizon.
    - Use `requested_metric` to filter outputs (defaults to '1y_sector_roi').
    - Output is Monday-sampled. The response includes an `Explanation` reflecting
      the actual inputs used after defaults are applied.
    """
    # Build request payload, excluding None values
    payload = {}
    if sim.rbp is not None:
        payload["rbp"] = sim.rbp
    if sim.rr is not None:
        payload["rr"] = sim.rr
    if sim.fpr is not None:
        payload["fpr"] = sim.fpr
    if sim.lock_target is not None:
        payload["lock_target"] = sim.lock_target
    if sim.forecast_length_days is not None:
        payload["forecast_length_days"] = sim.forecast_length_days
    if sim.sector_duration_days is not None:
        payload["sector_duration_days"] = sim.sector_duration_days
    if sim.requested_metric is not None:
        payload["output"] = sim.requested_metric
    else:
        payload["output"] = "1y_sector_roi"
    
    response = requests.post(
        f"{MECHAFIL_SERVER_URL}/simulate",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=payload,
        timeout=60
    )
    response.raise_for_status()

    # Parse the JSON body into a dict
    data = response.json()
    
    sim_output = data.get("simulation_output", {})
    if not sim_output:
        raise ValueError("No simulation_output found in response")
    
    # Assume only one key/value pair in simulation_output
    output_name: str = next(iter(sim_output.keys()))
    output_values: List[float] = sim_output[output_name]

    input_data = data.get("input", {})
    if not input_data:
        raise ValueError("No input data found in response")

    # Build explanation string with actual values
    def _format_input(value: Any) -> str:
        if isinstance(value, dict) and value.get("type") == "array":
            length = value.get("length")
            first = value.get("first")
            last = value.get("last")
            return f"array(len={length}, first={first}, last={last})"
        return str(value)

    output_explanation_text = (
        "Results of a Filecoin simulation with the following input values: " +
        f"Raw byte power (rbp) onboarded: {_format_input(input_data.get('raw_byte_power'))}, " +
        f"Renewal rate (rr): {_format_input(input_data.get('renewal_rate'))}, " +
        f"Filplus deals rate (fpr): {_format_input(input_data.get('filplus_rate'))}"
    )

    return {
        output_name: output_values,
        "Explanation": output_explanation_text,
    }
    

@mcp.tool(annotations={"title": "Get Historical Filecoin Data"})
def get_historical_data(req: Optional[HistoricalDataRequest] = None) -> str:
    """Return the `/historical-data` payload as a JSON string.

    - Arrays are Monday-sampled.
    - The response includes explicit date metadata to anchor arrays.
    - For plot requests, always use `fields` to return only the requested series.
    """
    try:
        response = requests.get(
            f"{MECHAFIL_SERVER_URL}/historical-data",
            headers={"Accept": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if req and req.fields:
            fields = req.fields if isinstance(req.fields, list) else [req.fields]
            metadata_keys = {
                "data_start_date",
                "data_end_date",
                "hist_window_start_date",
                "hist_window_end_date",
                "hist_window_days",
                "field_meta",
            }
            if isinstance(data, dict) and isinstance(data.get("data"), dict):
                filtered = {k: v for k, v in data["data"].items() if k in metadata_keys or k in fields}
                data = {"data": filtered}

        return json.dumps(data)
    
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


@mcp.tool(annotations={"title": "Provide Plot Spec"})
def provide_plot(req: ProvidePlotRequest) -> dict:
    """Build a strict chart object for the UI to render.

    - Use when you are unsure about formatting chart JSON.
    - Use when the user requests separate charts (call once per chart).
    - If you can emit the chart JSON directly, skip this tool.
    - The UI expects the returned object to be used verbatim.
    """
    series = req.series
    normalized_series: Union[str, dict, List[dict]]

    if isinstance(series, PlotSeries):
        normalized_series = series.model_dump(exclude_none=True)
    elif isinstance(series, str):
        if req.title or req.description:
            normalized_series = {"name": series}
        else:
            normalized_series = series
    else:
        normalized_list = []
        for entry in series:
            if isinstance(entry, PlotSeries):
                normalized_list.append(entry.model_dump(exclude_none=True))
            elif isinstance(entry, str):
                normalized_list.append({"name": entry})
            else:
                normalized_list.append(entry)
        normalized_series = normalized_list

    chart = {
        "series": normalized_series,
        "start_date_key": req.start_date_key or "data_start_date",
    }

    if req.title:
        chart["title"] = req.title
    if req.description:
        chart["description"] = req.description

    return {"chart": chart}


if __name__ == "__main__":
    import os
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "http":
        from starlette.responses import Response
        from starlette.routing import Route

        port = int(os.getenv("PORT", "8080"))

        # Get the HTTP app
        app = mcp.http_app()

        # Add CORS preflight handler
        async def handle_cors_preflight(request):
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Expose-Headers": "mcp-session-id",
                    "Access-Control-Max-Age": "86400",
                }
            )

        # Insert CORS route at the beginning
        app.routes.insert(0, Route("/mcp", handle_cors_preflight, methods=["OPTIONS"]))

        # Add CORS headers to all responses via middleware
        from starlette.middleware.base import BaseHTTPMiddleware

        class CORSHeaderMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                response = await call_next(request)
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Expose-Headers"] = "mcp-session-id"
                return response

        app.add_middleware(CORSHeaderMiddleware)

        # Run with uvicorn
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")
