# MCP MechaFil Server Documentation

## Table of Contents
1. [What is Filecoin](#what-is-filecoin)
2. [Tools Exposed](#tools-exposed)
3. [Tool Usage Instructions](#tool-usage-instructions)

---

## What is Filecoin

Filecoin is a decentralized storage network that transforms cloud storage into an algorithmic market. It creates a competitive marketplace where storage providers earn rewards by providing reliable storage capacity to the network, while clients pay to store and retrieve their data.

### Core Components of the Filecoin Network

#### **Storage Power System**
Filecoin operates on a **storage power consensus** mechanism where the probability of mining a block is proportional to the amount of storage a miner contributes to the network:

- **Raw Byte Power (RBP)**: The actual physical storage capacity committed to the network, measured in Exbibytes (EiB)
- **Quality Adjusted Power (QAP)**: RBP adjusted for deal quality, with FIL+ verified deals receiving a 10x multiplier
- **Block Rewards**: Storage providers earn FIL tokens proportional to their power share in the network

#### **Token Economics & Minting**
Filecoin has a sophisticated token minting system designed to incentivize network growth:

- **Simple Minting**: 30% of storage mining rewards released based on time (exponential decay with 6-year half-life)
- **Baseline Minting**: 70% of storage mining rewards tied to network storage growth relative to an exponentially growing baseline
- **Total Supply**: 2 billion FIL maximum, with different allocations for mining rewards, investors, team, and foundation
- **Vesting Schedules**: Various linear vesting periods (6 months to 6 years) for different token allocations

#### **Pledge & Collateral System**
Storage providers must lock FIL tokens as collateral to participate in the network:

- **Initial Pledge**: Collateral required when onboarding new storage sectors, calculated based on sector quality, expected rewards, and network conditions
- **Block Reward Locking**: A portion of earned rewards are locked for additional security (20-day unvesting)
- **Consensus Pledge**: Dynamic pledge requirements that adjust based on network conditions and protocol parameters like FIP-81

#### **FIL+ Program**
A program to incentivize useful data storage by providing quality multipliers:

- **Verified Deals**: Storage deals approved by notaries receive 10x quality-adjusted power
- **DataCap Allocation**: Limited verified deal capacity distributed through a governance process
- **Network Impact**: Higher FIL+ adoption significantly increases total network rewards and storage provider competition

#### **Economic Mechanisms**
The network employs several mechanisms to maintain economic security and sustainability:

- **Gas Burning**: Transaction fees permanently remove FIL from circulation, creating deflationary pressure
- **Pledge Smoothing (FIP-81)**: Gradual adjustment mechanism to prevent sudden pledge requirement shocks
- **Sector Renewal**: Storage providers can extend sector lifetimes to maintain network capacity and earn continued rewards

### Network Dynamics

#### **Storage Provider Economics**
- **Revenue Sources**: Block rewards, storage deal payments, and retrieval fees
- **Capital Requirements**: Initial pledge, hardware investment, and operational costs
- **Profitability Factors**: Quality-adjusted power ratio, renewal rates, FIL+ deal acquisition, and network competition levels

#### **Market Forces**
- **Supply & Demand**: Balance between storage supply (provider capacity) and demand (client data storage needs)
- **Competition**: More storage providers joining reduces individual reward shares but increases network security
- **Economic Cycles**: Network growth phases, reward halvening effects, and market-driven adoption patterns

---

## Tools Exposed

The MCP MechaFil server exposes 2 primary tools that provide access to the sophisticated MechaFil economic simulation engine:

### **1. `simulate` - Economic Forecast Simulation**
- **Purpose**: Run sophisticated Filecoin network economic forecasts
- **Output Format**: Weekly-sampled simulation results optimized for analysis and visualization
- **Use Cases**: Investment analysis, policy modeling, scenario planning, network health assessment

### **2. `get_historical_data` - Historical Network Data**
- **Purpose**: Retrieve real-world Filecoin blockchain data from network launch to present
- **Output Format**: JSON containing smoothed metrics, time series arrays, and simulation parameters
- **Use Cases**: Historical analysis, baseline parameter extraction, trend identification, simulation initialization

---

## Tool Usage Instructions

### Tool 1: `simulate` - Economic Forecast Simulation

#### **Function Overview**
The `simulate` tool provides access to MechaFil, a sophisticated economic simulation engine that models the complex dynamics of the Filecoin network. It acts as a "digital twin" of the Filecoin economy, enabling forecasts of future network states under various scenarios.

#### **Input Parameters**

All parameters are **optional** with intelligent defaults derived from recent network data. The system uses a three-tier default strategy:
1. **Explicit values** (if provided)
2. **Historical defaults** (30-day median of recent network data) 
3. **Configuration defaults** (system fallbacks)

##### **Core Economic Parameters**

**`rbp` - Raw Byte Power Onboarding Rate**
- **Type**: `float`, `List[float]`, or `None`
- **Units**: EiB/day (Exbibytes per day)
- **Range**: Typically 1.0 to 10.0 EiB/day
- **Default**: <span style="color: red;">**[NEEDS RESEARCH]** - Derived from recent network data, exact calculation method unknown</span>
- **Meaning**: Daily rate of new physical storage capacity added to the Filecoin network
- **Structure**:
  - **Single value**: `rbp: 5.0` (constant 5 EiB/day throughout forecast)
  - **Array**: `rbp: [3.0, 4.0, 5.0, 4.0]` (time-varying, must match `forecast_length_days`)
- **Economic Impact**: 
  - Higher onboarding = faster network growth, more competition for rewards, potentially lower per-sector returns
  - Lower onboarding = network stagnation risk, higher individual rewards but reduced network security
- **Examples**:
  - `rbp: 2.0` - Conservative growth scenario
  - `rbp: 5.0` - Aggressive expansion scenario
  - `rbp: [3.0, 4.0, 5.0, 4.0]` - Growth spike followed by normalization

**`rr` - Sector Renewal Rate**
- **Type**: `float`, `List[float]`, or `None`
- **Units**: Fraction (0.0 to 1.0, where 1.0 = 100%)
- **Range**: Typically 0.6 to 0.95 
- **Default**: <span style="color: red;">**[NEEDS RESEARCH]** - Derived from recent network data, exact calculation method unknown</span>
- **Meaning**: When storage sectors reach end-of-life, what fraction get renewed vs. leaving the network
- **Structure**:
  - **Single value**: `rr: 0.85` (85% renewal rate throughout forecast)
  - **Array**: `rr: [0.8, 0.85, 0.9]` (improving retention over time)
- **Economic Impact**:
  - High renewal (0.9+) = network stability, predictable capacity, less opportunity for new providers
  - Low renewal (<0.7) = more churn, network capacity volatility, opportunity for new onboarding
- **Examples**:
  - `rr: 0.9` - Very high retention, stable network
  - `rr: 0.7` - Moderate churn, opportunity for new providers
  - `rr: [0.8, 0.85, 0.9]` - Improving retention over time

**`fpr` - FIL+ Verified Deals Rate**
- **Type**: `float`, `List[float]`, or `None`
- **Units**: Fraction (0.0 to 1.0, where 1.0 = 100%)
- **Range**: Typically 0.3 to 0.95
- **Default**: <span style="color: red;">**[NEEDS RESEARCH]** - Derived from recent network data, exact calculation method unknown</span>
- **Meaning**: Fraction of new storage deals that qualify for FIL+ verified data program
- **Structure**:
  - **Single value**: `fpr: 0.90` (90% FIL+ adoption throughout forecast)
  - **Array**: `fpr: [0.8, 0.85, 0.9]` (growing verified data adoption)
- **Economic Impact**: **CRITICAL** - FIL+ deals get 10x quality multiplier, dramatically increasing rewards
  - Higher FIL+ rate = higher total rewards but more competition for verified deals
  - Lower FIL+ rate = reduced network rewards but easier access to deals for regular storage
- **Examples**:
  - `fpr: 0.95` - Very high verified data adoption
  - `fpr: 0.5` - Mixed use cases (verified + regular storage)
  - `fpr: [0.8, 0.85, 0.9]` - Growing verified data adoption

**`lock_target` - Target Consensus Pledge Ratio**
- **Type**: `float`, `List[float]`, or `None`
- **Units**: Fraction (0.0 to 1.0, where 1.0 = 100%)
- **Range**: Typically 0.15 to 0.4
- **Default**: `0.3` (30% of circulating supply locked as pledge)
- **Meaning**: Target percentage of all circulating FIL tokens to be locked as consensus pledge collateral
- **Structure**:
  - **Single value**: `lock_target: 0.25` (25% target throughout forecast)
  - **Array**: `lock_target: [0.35, 0.32, 0.30, 0.28, 0.25]` (decreasing requirements over time)
- **Economic Impact**:
  - Higher lock_target = more FIL locked away, potentially higher token scarcity and price pressure, but also higher capital requirements for storage providers
  - Lower lock_target = easier entry for new storage providers, potentially lower token scarcity
- **Examples**:
  - `lock_target: 0.2` - Lower capital requirements (20% locked)
  - `lock_target: 0.4` - Higher capital requirements (40% locked)
  - <span style="color: red;">**[NEEDS RESEARCH]** - Typical usage patterns and time-varying scenarios</span>

##### **Simulation Configuration Parameters**

**`forecast_length_days` - Forecast Duration** ⚠️ **CRITICAL PARAMETER**
- **Type**: `int` or `None`
- **Units**: Days
- **Range**: 1 to 3650 (1 day to 10 years)
- **Default**: `3650` (10 years) - **USUALLY TOO LONG FOR USER REQUESTS**
- **Meaning**: Number of days to forecast beyond current date
- **Structure**: Single integer only (not an array)
- **⚠️ CRITICAL RULE**: **ALWAYS extract time horizon from user request and set this parameter accordingly!**

**User Request Mapping (PAY CLOSE ATTENTION)**:
- "next 3 months" / "quarterly" → `forecast_length_days: 90`
- "next 6 months" → `forecast_length_days: 180`  
- "next year" / "annually" / "over the year" → `forecast_length_days: 365`
- "next 2 years" → `forecast_length_days: 730`
- "next 5 years" / "medium-term" → `forecast_length_days: 1825`
- "next decade" / "long-term" → `forecast_length_days: 3650`
- "next 30 days" / "monthly" → `forecast_length_days: 30`

**Examples of User Request Parsing**:
- "What will storage provider ROI be next year?" → SET `forecast_length_days: 365`
- "How will FIL supply change over 2 years?" → SET `forecast_length_days: 730`  
- "Show me network growth for next 6 months" → SET `forecast_length_days: 180`

**`sector_duration_days` - Average Sector Lifetime**
- **Type**: `int` or `None`
- **Units**: Days
- **Range**: 180 to 1278 (6 months to 3.5 years, Filecoin protocol limits)
- **Default**: `540` (~18 months)
- **Meaning**: Average commitment duration for storage sectors before natural expiration
- **Structure**: Single integer only
- **Economic Impact**: 
  - Longer duration = less frequent renewal decisions, more predictable network capacity
  - Shorter duration = more flexibility but higher administrative overhead for providers
- **Examples**:
  - `sector_duration_days: 360` - 1-year commitments (shorter, more flexible)
  - `sector_duration_days: 720` - 2-year commitments (longer, more stable)

**`requested_metric` - Output Field Selection**
- **Type**: `str` or `None`
- **Default**: `"1y_sector_roi"` (annual return on investment for storage providers)
- **Meaning**: Specific economic metric to return from simulation (recommended for focused analysis)
- **Structure**: Single string specifying one metric name

**Available Metrics Categories**:

*Investment Metrics*:
- `"1y_sector_roi"`: Annual ROI for 32GiB sectors (0.15 = 15% return)
- `"1y_return_per_sector"`: Annual FIL earnings per 32GiB sector
- `"day_rewards_per_sector"`: Daily FIL earnings per sector
- `"day_pledge_per_QAP"`: Collateral required per PiB of storage

*Supply Metrics*:
- `"available_supply"`: FIL tokens available for trading (excludes locked)
- `"circ_supply"`: Total circulating FIL supply (includes locked tokens)
- `"network_locked"`: Total FIL locked as collateral

*Network Metrics*:
- `"network_QAP_EIB"`: Total quality-adjusted storage power (EiB)
- `"network_RBP_EIB"`: Total raw storage capacity (EiB)
- `"day_network_reward"`: Daily block rewards to all providers (FIL/day)

<span style="color: red;">**[NEEDS RESEARCH]** - Complete list of all 40+ available metrics with descriptions and typical value ranges</span>

#### **Output Structure**

**Return Type**: `dict`

**Structure**:
```python
{
    "metric_name": [value1, value2, value3, ...],  # Weekly-sampled time series
    "Explanation": "Results of a Filecoin simulation with the following input values: Raw byte power (rbp) onboarded: X.XX, Renewal rate (rr): X.XX, Filplus deals rate (fpr): X.XX"
}
```

**Output Details**:
- **`metric_name`**: The key matches the `requested_metric` parameter (default: `"1y_sector_roi"`)
- **Time Series Array**: List of `float` values representing the metric over time
- **Sampling**: Values are sampled at weekly intervals (every 7 days)
- **Array Length**: `forecast_length_days / 7` (approximately, based on Monday sampling)
- **`"Explanation"`**: String describing the actual parameter values used in the simulation (derived from defaults if not specified)

**Value Interpretation Examples**:
- **ROI values**: `0.15` = 15% annual return, `0.25` = 25% annual return
- **Supply values**: Large numbers representing FIL tokens (e.g., `580250000.12` = ~580M FIL)
- **Power values**: Storage capacity in EiB (e.g., `15.2` = 15.2 Exbibytes)
- **Reward values**: Daily FIL rewards (e.g., `123456.78` = ~123K FIL per day)

<span style="color: red;">**[NEEDS RESEARCH]** - Typical value ranges for different metrics, interpretation guidelines for economic indicators</span>

#### **Usage Examples**

**Basic Usage (All Defaults)**:
```python
simulate(SimulationInputs())
# Returns 10-year ROI forecast with recent network parameters
```

**Focused 1-Year Analysis**:
```python
simulate(SimulationInputs(
    forecast_length_days=365,
    requested_metric="1y_sector_roi"
))
```

**Custom Growth Scenario**:
```python
simulate(SimulationInputs(
    rbp=6.0,                    # High onboarding
    fpr=0.95,                   # Very high FIL+ adoption
    forecast_length_days=730,   # 2-year forecast
    requested_metric="available_supply"
))
```

**Time-Varying Parameters**:
```python
simulate(SimulationInputs(
    rbp=[3.0, 4.0, 5.0, 4.0, 3.0],  # Growth spike then decline
    rr=[0.8, 0.82, 0.85, 0.87, 0.9], # Improving retention
    forecast_length_days=5,           # Must match array length
    requested_metric="network_QAP_EIB"
))
```

### Tool 2: `get_historical_data` - Historical Network Data

#### **Function Overview**
Retrieves real-world historical data from the Filecoin blockchain network, spanning from mainnet launch (October 15, 2020) to the most recent available data (typically 3 days behind current date due to data processing lag).

#### **Input Parameters**
**None** - This function takes no parameters and returns the complete historical dataset.

#### **Output Structure**

**Return Type**: `str` (JSON-formatted string)

**Structure**:
```json
{
    "message": "Historical data reduced to Mondays only (no averaging)",
    "smoothed_metrics": {
        "raw_byte_power": 3.38,      // EiB/day recent onboarding rate
        "renewal_rate": 0.83,        // Recent sector renewal rate (83%)
        "filplus_rate": 0.86         // Recent FIL+ adoption rate (86%)
    },
    "monday_arrays": {
        "raw_byte_power": [2.1, 2.4, 2.8, ...],     // Weekly historical values
        "renewal_rate": [0.75, 0.78, 0.81, ...],
        "filplus_rate": [0.82, 0.84, 0.85, ...]
    },
    "offline_data_mondays": {
        "rb_power_zero": 1234.56,                    // Initial RBP (PiB)
        "qa_power_zero": 2345.67,                    // Initial QAP (PiB)
        "circ_supply_zero": 123456789.12,            // Initial circulating supply (FIL)
        "locked_fil_zero": 98765432.10,              // Initial locked FIL
        // ... extensive initialization data for simulations
    }
}
```

#### **Output Sections Explained**

##### **1. Smoothed Metrics**
30-day median values of recent network data, useful as default parameters for simulations:

- **`raw_byte_power`**: Recent network storage onboarding rate (EiB/day)
- **`renewal_rate`**: Recent sector renewal rate (0-1, where 1=100% renewed)  
- **`filplus_rate`**: Recent FIL+ adoption rate (0-1, where 1=100% FIL+ deals)

<span style="color: red;">**[NEEDS RESEARCH]** - Exact calculation methodology for smoothed metrics, typical value ranges</span>

##### **2. Monday Arrays**
Historical time series data downsampled to weekly intervals (Mondays only) for efficient data transfer:

- **Array Length**: <span style="color: red;">**[NEEDS RESEARCH]** - Number of weeks since mainnet launch</span>
- **Sampling Method**: Values correspond to Monday dates only
- **Data Coverage**: From Filecoin mainnet launch (~October 2020) to most recent data
- **Use Cases**: Trend analysis, historical pattern identification, baseline comparison

##### **3. Offline Data**
Comprehensive simulation initialization parameters and historical context:

**Power Statistics**:
- **`rb_power_zero`**: Initial raw byte power when simulation starts (PiB)
- **`qa_power_zero`**: Initial quality-adjusted power (PiB)
- **Historical power time series**: Complete daily/weekly power evolution data

**Economic Data**:
- **`circ_supply_zero`**: Initial circulating FIL token supply
- **`locked_fil_zero`**: Initial amount of locked FIL tokens
- **`daily_burnt_fil`**: Average daily gas burn rate (FIL/day)
- **`burnt_fil_vec`**: Historical cumulative gas burn time series

**Scheduled Operations**:
- **`rb_known_scheduled_expire_vec`**: Known RBP expirations (PiB)
- **`qa_known_scheduled_expire_vec`**: Known QAP expirations (PiB)
- **`known_scheduled_pledge_release_full_vec`**: Scheduled pledge releases (FIL)

**Vesting and Protocol Parameters**:
- **`start_vested_amt`**: Initial vested amount (attoFIL)
- **`zero_cum_capped_power_eib`**: Initial cumulative capped power (EiB)
- **`init_baseline_eib`**: Initial baseline power for minting calculations (EiB)

<span style="color: red;">**[NEEDS RESEARCH]** - Complete field definitions for all offline_data parameters, typical value ranges, data update frequency</span>

#### **Usage Examples**

**Basic Usage**:
```python
historical_data = get_historical_data()
import json
data = json.loads(historical_data)

# Access recent network parameters
recent_onboarding = data["smoothed_metrics"]["raw_byte_power"]  # e.g., 3.38 EiB/day
recent_renewals = data["smoothed_metrics"]["renewal_rate"]      # e.g., 0.83 (83%)

# Access historical trends
rbp_history = data["monday_arrays"]["raw_byte_power"]  # Weekly time series
```

**Error Handling**:
The function returns error information in JSON format if issues occur:

```json
{
    "error": "Connection failed",
    "message": "Could not connect to mechafil-server at http://localhost:8000", 
    "suggestion": "Make sure mechafil-server is running"
}
```

**Common Error Scenarios**:
- **Connection Failed**: MechaFil server not running or wrong URL
- **HTTP Errors**: Server returning error status codes
- **Data Processing**: <span style="color: red;">**[NEEDS RESEARCH]** - Other potential error scenarios and handling</span>

#### **Performance Characteristics**

- **Response Time**: ~1-2 seconds (data is cached)
- **Data Size**: ~50KB (weekly downsampling reduces transfer size)
- **Update Frequency**: Daily refresh at 02:00 UTC
- **Data Lag**: ~3 days behind current date for data processing

<span style="color: red;">**[NEEDS RESEARCH]** - Exact caching strategy, data freshness guarantees, maximum historical data range</span>

---

## Integration Notes

### Environment Configuration
- **`MECHAFIL_SERVER_URL`**: Environment variable to specify the MechaFil server URL (default: `http://localhost:8000`)
- **Dependencies**: Requires running MechaFil server instance for all functionality

### Tool Relationship
- **`get_historical_data`**: Provides baseline parameters and context for simulation setup
- **`simulate`**: Uses historical data as defaults when parameters not explicitly specified
- **Workflow**: Typically call `get_historical_data` first to understand current network state, then run `simulate` with appropriate parameters

### Best Practices
1. **Always set `forecast_length_days`** based on user's time horizon requirements
2. **Use `requested_metric`** to focus analysis on specific economic indicators  
3. **Call `get_historical_data`** to understand current network baseline before running forecasts
4. **Start with default parameters** for initial analysis, then modify based on scenario requirements
5. **Consider economic reasonableness** of parameter combinations (e.g., very high onboarding with very low renewals may be unrealistic)

<span style="color: red;">**[RESOURCES TO BE INTEGRATED]**</span>
<span style="color: red;">**[NEEDS RESEARCH]**</span>

**Missing Information Requiring Additional Research**:

1. **Default Parameter Calculation**: Exact methodology for deriving defaults from historical data
2. **Complete Metrics List**: All 40+ available output metrics with descriptions and typical ranges
3. **Value Interpretation Guidelines**: Ranges and meaning for different metric types  
4. **Historical Data Completeness**: Full field definitions for offline_data parameters
5. **Error Handling**: Complete list of potential error scenarios and responses
6. **Performance Specifications**: Exact caching behavior, data update processes
7. **Parameter Validation**: Acceptable ranges and validation rules for all input parameters
8. **Economic Context**: Typical parameter combinations and realistic scenarios
9. **Time-varying Usage**: Best practices for array-based parameter scenarios
10. **Data Quality**: Freshness guarantees, historical coverage limits, accuracy considerations