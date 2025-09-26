"""MCP server for mechafil-server API endpoints."""

import json
import os
from typing import Dict, List, Optional, Union, Any, Annotated
from pydantic import BaseModel, Field
import requests
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult

# Server configuration
MECHAFIL_SERVER_URL = os.getenv("MECHAFIL_SERVER_URL", "http://localhost:8000")

# Create MCP server
mcp = FastMCP("mechafil-server")

class SimulationInputs(BaseModel):
    """Parameters for Filecoin economic simulation. All fields are optional with intelligent defaults."""
    
    rbp: Annotated[
        Optional[Union[float, List[float]]],
        Field(
            description="""Raw Byte Power onboarding rate in EiB/day (Exbibytes per day).
            
            MEANING: Daily rate of new physical storage capacity added to the Filecoin network.
            DEFAULT: Derived from recent network data and its value is reported in the explaination of the results of the simulation.
            
            EXAMPLES:
            - 2.0 = Conservative growth scenario
            - 5.0 = Aggressive expansion scenario  
            - [3.0, 4.0, 5.0, 4.0] = Time-varying growth pattern (requires array length = forecast_length_days)
            
            CONTEXT: Higher onboarding = faster network growth, more competition for rewards, potentially lower per-sector returns.
            Lower onboarding = network stagnation risk, higher individual rewards."""
        )
    ] = None

    rr: Annotated[
        Optional[Union[float, List[float]]],
        Field(
            description="""Sector renewal rate as fraction 0.0-1.0 (0%=all sectors expire, 100%=all renewed).
            
            MEANING: When storage sectors reach end-of-life, what fraction get renewed vs. leaving network.
            DEFAULT: Derived from recent network data and its value is reported in the explaination of the results of the simulation. 
            
            EXAMPLES:
            - 0.9 = Very high retention, stable network
            - 0.7 = Moderate churn, opportunity for new providers
            - [0.8, 0.85, 0.9] = Improving retention over time
            
            IMPACT: High renewal = network stability, predictable capacity.
            Low renewal = more churn, network capacity volatility, opportunity for new onboarding."""
        )
    ] = None

    fpr: Annotated[
        Optional[Union[float, List[float]]],
        Field(
            description="""FIL+ verified deals rate as fraction 0.0-1.0 (0%=no FIL+, 100%=all verified).
            
            MEANING: Fraction of new storage deals that qualify for FIL+ verified data program.
            DEFAULT: Derived from recent network data and its value is reported in the explaination of the results of the simulation.
            
            EXAMPLES:
            - 0.95 = Very high verified data adoption
            - 0.5 = Mixed use cases (verified + regular storage)
            - [0.8, 0.85, 0.9] = Growing verified data adoption
            
            CRITICAL: FIL+ deals get 10x quality multiplier, dramatically increasing rewards.
            Higher FIL+ rate = higher total rewards but more competition for verified deals."""
        )
    ] = None

    lock_target: Annotated[
        Optional[Union[float, List[float]]],
        Field(
            description="""Target consensus pledge ratio as fraction 0.0-1.0 of circulating supply.
            
            MEANING: Target percentage of all circulating FIL tokens to be locked as consensus pledge collateral.
            DEFAULT: 0.3 (30% of supply locked as pledge)
            
            EXAMPLES:
            - 0.2 = Lower capital requirements (20% locked)
            - 0.4 = Higher capital requirements (40% locked) 
            - Typically kept constant, rarely time-varying
            
            IMPACT: Higher lock_target = more FIL locked away, potentially higher token scarcity and price pressure,
            but also higher capital requirements for storage providers."""
        )
    ] = None

    forecast_length_days: Annotated[
        Optional[int],
        Field(
            description="""CRITICAL: Forecast duration in days. MUST match user's time horizon request!
            
            🚨 IMPORTANT: ALWAYS extract time horizon from user request and set this parameter accordingly!
            
            DEFAULT: 3650 days (10 years) - USUALLY TOO LONG AND WRONG FOR USER REQUESTS
            
            USER REQUEST MAPPING (PAY CLOSE ATTENTION):
            - "next 3 months" / "quarterly" → forecast_length_days=90
            - "next 6 months" → forecast_length_days=180  
            - "next year" / "annually" / "over the year" → forecast_length_days=365
            - "next 2 years" → forecast_length_days=730
            - "next 5 years" / "medium-term" → forecast_length_days=1825
            - "next decade" / "long-term" → forecast_length_days=3650
            - "next 30 days" / "monthly" → forecast_length_days=30
            
            EXAMPLES OF USER REQUEST PARSING:
            - "What will storage provider ROI be next year?" → SET forecast_length_days=365
            - "How will FIL supply change over 2 years?" → SET forecast_length_days=730  
            - "Show me network growth for next 6 months" → SET forecast_length_days=180
            - "Long-term sustainability over a decade" → SET forecast_length_days=3650
            
            ⚠️  CRITICAL RULE: If user specifies ANY time horizon (even implicitly), you MUST set forecast_length_days.
            Do NOT rely on default values when user has expressed a time preference!
            
            GUIDANCE: Shorter forecasts are more reliable. Uncertainty compounds over time.
            Most business analysis needs 1-2 years maximum."""
        )
    ] = None

    sector_duration_days: Annotated[
        Optional[int],
        Field(
            description="""Average lifetime of storage sectors before natural expiration.
            
            MEANING: How long storage commitments last before they naturally expire (if not renewed).
            DEFAULT: 540 days (~18 months)
            
            EXAMPLES:
            - 360 days = 1-year commitments (shorter, more flexible)
            - 720 days = 2-year commitments (longer, more stable)
            
            IMPACT: Longer duration = less frequent renewal decisions, more predictable network capacity.
            Shorter duration = more flexibility but higher administrative overhead for providers."""
        )
    ] = None

    requested_metric: Annotated[
        Optional[str],
        Field(
            description="""Specific economic metric to return from simulation. RECOMMENDED to specify for focused analysis.
            
            DEFAULT: "1y_sector_roi" (annual return on investment for storage providers)
            
            INVESTMENT METRICS:
            - "1y_sector_roi": Annual ROI for 32GiB sectors (0.15 = 15% return)
            - "1y_return_per_sector": Annual FIL earnings per 32GiB sector
            - "day_rewards_per_sector": Daily FIL earnings per sector
            - "day_pledge_per_QAP": Collateral required per PiB of storage
            
            SUPPLY METRICS:
            - "available_supply": FIL tokens available for trading (excludes locked)
            - "circ_supply": Total circulating FIL supply (includes locked tokens)
            - "network_locked": Total FIL locked as collateral
            
            NETWORK METRICS:
            - "network_QAP_EIB": Total quality-adjusted storage power (EiB)
            - "network_RBP_EIB": Total raw storage capacity (EiB)
            - "day_network_reward": Daily block rewards to all providers (FIL/day)
            
            USAGE: Specify one metric for focused analysis. Leave None for default ROI analysis."""
        )
    ] = None


@mcp.tool(annotations={"title": "Run Filecoin Economic Forecast Simulation"})
def simulate(sim: SimulationInputs) -> dict:
    """Run sophisticated economic forecasts of the Filecoin network using the MechaFil digital twin.
    
    PURPOSE:
    This function provides access to MechaFil, a sophisticated economic simulation engine that models
    the complex dynamics of the Filecoin decentralized storage network. It acts as a "digital twin"
    of the Filecoin economy, enabling users to forecast future network states, analyze economic
    scenarios, and evaluate the impact of different growth trajectories.
    
    CONTEXT - What MechaFil Simulates:
    The simulation models the intricate relationships between:
    - Storage Power Dynamics: How raw storage and quality-adjusted power evolve
    - Token Economics: FIL minting, supply dynamics, and circulation patterns  
    - Consensus Mechanisms: Block rewards and storage power-based leader election
    - Pledge Economics: Collateral requirements and FIP-81 consensus pledge smoothing
    - Market Forces: Storage deals, sector renewals, and FIL+ program effects
    - Network Growth: Onboarding rates, sector lifetimes, and capacity expansion
    
    WHEN TO USE THIS TOOL:
    - Economic Forecasting: "What will FIL supply look like in 2 years?"
    - Investment Analysis: "What returns can storage providers expect?"
    - Policy Impact: "How would changing pledge requirements affect the network?"
    - Scenario Planning: "What if onboarding rates double next year?"
    - Network Health: "Is the current trajectory sustainable long-term?"
    - Comparative Analysis: "How do different growth scenarios compare?"
    
    INPUT PARAMETERS (all optional with intelligent defaults):
    
    rbp (Raw Byte Power): 
        - Units: EiB/day (Exbibytes per day)
        - Meaning: Rate of new storage capacity added to network daily
        - Default: Derived from recent network data and its value is reported in the explaination of the results of the simulation.
        - Example: 5.0 = aggressive growth, 2.0 = slower growth
        - Can be: Single value (constant) or array (time-varying scenario)
    
    rr (Renewal Rate):
        - Units: Ratio 0-1 (0=0%, 1=100%)  
        - Meaning: Fraction of expiring sectors that get renewed vs. leaving network
        - Default: Derived from recent network data and its value is reported in the explaination of the results of the simulation.
        - Example: 0.9 = very high retention, 0.7 = moderate churn
        - Impact: Higher renewal = more stable network, lower new onboarding needs
    
    fpr (FIL+ Rate):
        - Units: Ratio 0-1 (0=0%, 1=100%)
        - Meaning: Fraction of new storage that qualifies for FIL+ verified deals
        - Default: Derived from recent network data and its value is reported in the explaination of the results of the simulation.
        - Impact: FIL+ deals get 10x quality multiplier, boosting rewards significantly
        - Example: 0.95 = very high verified data, 0.5 = mixed use case
    
    lock_target:
        - Units: Ratio 0-1 (0=0%, 1=100%)
        - Meaning: Target fraction of circulating supply to lock as consensus pledge
        - Default: 0.3 (30% target locking ratio)
        - Impact: Higher = more capital requirements, potentially higher token scarcity
    
    forecast_length_days:
        - Units: Days
        - Default: 3650 days (10 years) - OFTEN TOO LONG!
        - Recommended: 90 (3 months), 365 (1 year), 1825 (5 years)
        - Note: Longer forecasts become less reliable due to compounding uncertainties
    
    sector_duration_days:
        - Units: Days  
        - Meaning: Average lifetime of storage sectors before expiration
        - Default: 540 days (~18 months)
        - Impact: Longer duration = less renewal churn, more predictable network
    
    requested_metric:
        - Specify which economic metrics to return (recommended to focus analysis)
        - Default: "1y_sector_roi" (one-year return on investment for storage providers)
        - Examples: "available_supply", "network_QAP_EIB", "day_network_reward"
        - Available metrics include 40+ economic and network indicators
    
    KEY OUTPUT METRICS EXPLAINED:
    
    Economic Indicators:
    - available_supply: FIL tokens available for market circulation (excludes locked)
    - circ_supply: Total circulating FIL supply (includes locked tokens)
    - day_network_reward: Daily block rewards paid to storage providers (FIL/day)
    - network_locked: Total FIL locked as collateral by storage providers
    - 1y_sector_roi: Annual return on investment for 32GiB storage sectors (ratio)
    - 1y_return_per_sector: Annual FIL earnings per 32GiB sector
    
    Network Power Metrics:
    - network_RBP_EIB: Total raw byte storage power on network (EiB)
    - network_QAP_EIB: Total quality-adjusted power including FIL+ multipliers (EiB)
    - capped_power_EIB: Network power used for baseline minting calculations (EiB)
    
    Investment Analytics:
    - day_pledge_per_QAP: Required collateral per unit of power (FIL/PiB)
    - day_rewards_per_sector: Daily earnings per 32GiB sector (FIL/day)
    
    OUTPUT FORMAT:
    Returns dictionary with structure:
    {
        "1y_sector_roi": [0.187, 0.189, 0.191, ...],  // Weekly sampled values
        "Explaination" : "Results of a Filecoin simulation with the following input values:  Raw byte power (rbp) onboarded: 2.36,  Renewal rate (rr): 0.82, Filplus deals rate (fpr): 0.74"
    }
    
    The output array represents time series data, with each value corresponding to a week
    in the forecast period. Values are sampled in intervals of 7-days.
    
    INTERPRETATION GUIDANCE:
    - ROI values: 0.15 = 15% annual return, 0.25 = 25% return
    - Supply trends: Increasing = inflationary, decreasing = deflationary pressure
    - Power growth: Exponential = unsustainable, linear = steady state
    - Reward patterns: Declining over time due to halvening-like economics
    
    
    LIMITATIONS:
    - Assumes rational economic behavior and stable protocol rules
    - Cannot predict external market shocks or major protocol changes
    - Longer forecasts have higher uncertainty due to compounding assumptions
    - Does not model competitor networks or regulatory changes
    
    Args:
        sim: SimulationInputs containing forecast parameters (all optional)
        
    Returns:
        dict: Simulation results with specified output metric and a detailed explaination of the parameters that are used during this simulation. IMPORTANT: read always the explaination
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

    input_variables = data.get("input variables", {})
    if not input_variables:
        raise ValueError("No input variables found in response")

    # Build explanation string with actual values
    output_explanation_text = (
        "Results of a Filecoin simulation with the following input values: " +
        f"Raw byte power (rbp) onboarded: {input_variables.get('raw_byte_power')}, " + 
        f"Renewal rate (rr): {input_variables.get('renewal_rate')}, " + 
        f"Filplus deals rate (fpr): {input_variables.get('filplus_rate')}"
    )

    return {
        output_name: output_values,
        "Explanation": output_explanation_text,
    }
    

@mcp.tool()
def get_historical_data() -> str:
    """Get historical Filecoin network data for analysis and simulation initialization.
    
    PURPOSE:
    This function retrieves real-world historical data from the Filecoin blockchain network,
    which serves as the foundation for understanding current network state and initializing
    economic simulations. The data spans from Filecoin mainnet launch (Oct 15, 2020) to
    the most recent available data (typically 3 days behind current date).
    
    CONTEXT - Why Use This:
    - Analyze historical trends in Filecoin network growth and economics
    - Understand current network state (power, supply, rewards, pledge requirements)
    - Get baseline parameters for running economic forecasts
    - Research storage provider economics and network health over time
    - Extract default parameters that reflect recent network behavior
    
    DATA INCLUDED:
    The response contains three main sections:
    
    1. SMOOTHED METRICS (30-day medians of recent data):
       - raw_byte_power: Recent network storage onboarding rate (EiB/day)
       - renewal_rate: Recent sector renewal rate (0-1, where 1=100% renewed)
       - filplus_rate: Recent FIL+ adoption rate (0-1, where 1=100% FIL+ deals)
    
    2. MONDAY ARRAYS (weekly time series data, Mondays only):
       - Historical values for key metrics downsampled to weekly intervals
       - Useful for trend analysis without overwhelming detail
       - Covers: power growth, renewal patterns, FIL+ adoption over time
    
    3. OFFLINE DATA (simulation initialization parameters):
       - rb_power_zero: Initial raw byte power when simulation starts
       - qa_power_zero: Initial quality-adjusted power 
       - circ_supply_zero: Initial circulating FIL token supply
       - locked_fil_zero: Initial amount of locked FIL tokens
       - Scheduled sector expirations and pledge releases
       - Vesting schedules and baseline parameters
    
    OUTPUT FORMAT:
    Returns JSON string with structure:
    {
        "message": "Historical data reduced to Mondays only (no averaging)",
        "smoothed_metrics": {
            "raw_byte_power": 3.38,    // EiB/day onboarding rate
            "renewal_rate": 0.83,      // 83% renewal rate  
            "filplus_rate": 0.86       // 86% FIL+ adoption
        },
        "monday_arrays": {
            "raw_byte_power": [2.1, 2.4, 2.8, ...],  // Weekly historical values
            "renewal_rate": [0.75, 0.78, 0.81, ...],
            "filplus_rate": [0.82, 0.84, 0.85, ...]
        },
        "offline_data_mondays": {
            "rb_power_zero": 1234.56,          // PiB initial power
            "qa_power_zero": 2345.67,          // PiB initial QA power
            "circ_supply_zero": 123456789.12,  // FIL initial supply
            // ... extensive initialization data for simulations
        }
    }
    
    TYPICAL USE CASES:
    - "What's the current state of the Filecoin network?"
    - "How has storage onboarding changed over time?"
    - "What are typical renewal rates for storage providers?"
    - "Get baseline parameters for running a forecast simulation"
    - "Analyze historical FIL+ program adoption"
    
    PERFORMANCE:
    - Response time: ~1-2 seconds (cached data)
    - Data size: ~50KB (weekly downsampling reduces size)
    - Updates: Daily refresh at 02:00 UTC
    
    Returns:
        str: JSON string containing comprehensive historical network data
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


if __name__ == "__main__":
    mcp.run(transport="stdio")