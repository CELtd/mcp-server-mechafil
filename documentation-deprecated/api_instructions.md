# MechaFil Server API Instructions

This guide provides comprehensive instructions for using the MechaFil Server API to run Filecoin economic simulations and retrieve historical data.

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints Overview](#api-endpoints-overview)
3. [Historical Data Endpoints](#historical-data-endpoints)
4. [Simulation Endpoints](#simulation-endpoints)
5. [Parameter Reference](#parameter-reference)
6. [Output Fields Reference](#output-fields-reference)
7. [Advanced Usage Examples](#advanced-usage-examples)
8. [Error Handling](#error-handling)
9. [Best Practices](#best-practices)

---

## Quick Start

### Server Information
- **Base URL**: `http://localhost:8000` (default)
- **Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc`
- **Health Check**: `GET http://localhost:8000/health`

### Minimal Simulation Request
```bash
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{}'
```

This runs a simulation with all default parameters derived from recent historical data.

---

## API Endpoints Overview

| Endpoint | Method | Purpose | Response Format |
|----------|--------|---------|----------------|
| `/` | GET | Server documentation redirect | Redirect to /documentation or /docs |
| `/health` | GET | Health check and JAX backend info | JSON status |
| `/historical-data` | GET | Historical data (Monday-downsampled) | `{"data": {...}}` |
| `/simulate` | POST | Run simulation (Monday-downsampled) | `{"input": {...}, "simulation_output": {...}}` |

---

## Historical Data Endpoint

### `GET /historical-data`

**Purpose**: Get historical Filecoin network metrics downsampled to Monday values for efficient data transfer.

**Request**:
```bash
curl -X GET http://localhost:8000/historical-data
```

**Response Structure**:
Returns a `FetchDataResults` object with a single `data` dictionary containing:

```json
{
  "data": {
    // 30-day smoothed metrics (scalars)
    "raw_byte_power_averaged_over_previous_30days": 3.38,
    "renewal_rate_averaged_over_previous_30days": 0.83,
    "filplus_rate_averaged_over_previous_30days": 0.86,

    // Historical time series (Monday values only)
    "raw_byte_power": [2.1, 2.3, 2.5, ...],
    "renewal_rate": [0.75, 0.78, 0.82, ...],
    "filplus_rate": [0.80, 0.83, 0.85, ...],

    // Offline model data (scalars and Monday-downsampled arrays)
    "rb_power_zero": 1234.56,
    "qa_power_zero": 2345.67,
    "circ_supply_zero": 123456789.12,
    "locked_fil_zero": 45678901.23,
    "historical_raw_power_eib": [12.5, 13.1, ...],
    "historical_qa_power_eib": [45.2, 46.1, ...],
    "rb_known_scheduled_expire_vec": [...],
    "qa_known_scheduled_expire_vec": [...],
    "known_scheduled_pledge_release_full_vec": [...],
    // ... other historical data fields (see Historical Data Fields Reference below)
  }
}
```

**Key Points**:
- All arrays are downsampled to Monday values only (weekly sampling)
- Returns complete data in a single `data` object
- Scalars represent either initial values or 30-day smoothed metrics

### Historical Data Fields Reference

The `data` object contains all historical network data required for simulations:

#### Power Statistics
- **`rb_power_zero`**: Initial raw byte power (PiB)
- **`qa_power_zero`**: Initial quality-adjusted power (PiB)
- **`historical_raw_power_eib`**: Daily RBP history (EiB)
- **`historical_qa_power_eib`**: Daily QAP history (EiB)
- **`historical_onboarded_rb_power_pib`**: Daily RBP onboarding (PiB)
- **`historical_onboarded_qa_power_pib`**: Daily QAP onboarding (PiB)
- **`historical_renewed_rb_power_pib`**: Daily RBP renewals (PiB)
- **`historical_renewed_qa_power_pib`**: Daily QAP renewals (PiB)
- **`historical_renewal_rate`**: Historical renewal rates (0-1)

#### Scheduled Operations
- **`rb_known_scheduled_expire_vec`**: Known RBP expirations (PiB)
- **`qa_known_scheduled_expire_vec`**: Known QAP expirations (PiB)
- **`known_scheduled_pledge_release_full_vec`**: Scheduled pledge releases (FIL)

#### Economic Data
- **`circ_supply_zero`**: Initial circulating supply (FIL)
- **`locked_fil_zero`**: Initial locked FIL amount
- **`daily_burnt_fil`**: Average daily gas burn (FIL)
- **`burnt_fil_vec`**: Historical cumulative gas burn (FIL)

#### Vesting and Baseline
- **`start_vested_amt`**: Initial vested amount (attoFIL)
- **`zero_cum_capped_power_eib`**: Initial cumulative capped power (EiB)
- **`init_baseline_eib`**: Initial baseline power (EiB)

---

## Simulation Endpoint

### `POST /simulate`

**Purpose**: Run economic forecasts with results downsampled to Monday values for efficient data transfer.

**Request Structure**:
```json
{
  "rbp": 3.5,                    // Raw byte power onboarding (PIB/day) - optional
  "rr": 0.85,                    // Renewal rate (0-1) - optional
  "fpr": 0.90,                   // FIL+ rate (0-1) - optional
  "lock_target": 0.3,            // Target lock ratio - optional
  "forecast_length_days": 365,   // Forecast period in days - optional
  "sector_duration_days": 540,   // Average sector duration - optional
  "output": ["available_supply", "1y_sector_roi"]  // Specific fields only - optional
}
```

**Example Request**:
```bash
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "rbp": 4.0,
    "rr": 0.85,
    "fpr": 0.90,
    "lock_target": 0.25,
    "forecast_length_days": 365
  }'
```

**Response Structure**:
Returns a `SimulationResults` object with two main sections:

```json
{
  "input": {
    "current date": "2025-01-01",
    "forecast_length_days": 365,
    "raw_byte_power": 4.0,
    "renewal_rate": 0.85,
    "filplus_rate": 0.90
  },
  "simulation_output": {
    // Monday-downsampled time series for all metrics
    "available_supply": [580250000.12, 582100000.45, ...],
    "network_RBP_EIB": [15.2, 15.4, 15.6, ...],
    "1y_sector_roi": [0.18, 0.17, 0.16, ...],
    // ... other output fields (see Output Fields Reference)
  }
}
```

**Key Points**:
- `input`: Metadata about the simulation (dates and actual parameters used)
- `simulation_output`: All simulation metrics downsampled to Monday values (weekly sampling)
- Arrays contain time series data with values for each Monday in the forecast period
- Values are rounded to 2 decimal places for efficiency

---

## Parameter Reference

### Required vs Optional Parameters

**All parameters are optional** - the API provides intelligent defaults:

1. **Explicit values** (if provided in request)
2. **Historical defaults** (30-day median of recent data)
3. **Configuration defaults** (fallback values)

### Core Simulation Parameters

#### **`rbp` - Raw Byte Power Onboarding**
- **Type**: `float` or `array` of floats
- **Unit**: PIB/day (Pebibytes per day)
- **Range**: Positive values (typically 1-10 PIB/day)
- **Description**: Daily storage capacity additions to the network
- **Examples**:
  - Constant: `"rbp": 3.5`
  - Time-varying: `"rbp": [3.0, 3.2, 3.5, 3.8, 4.0]`
- **Default**: 30-day median of historical onboarding data

#### **`rr` - Renewal Rate**
- **Type**: `float` or `array` of floats
- **Unit**: Dimensionless fraction (0-1)
- **Range**: 0.0 to 1.0
- **Description**: Fraction of expiring sectors that get renewed each day
- **Examples**:
  - Constant: `"rr": 0.85` (85% renewal rate)
  - Declining: `"rr": [0.9, 0.88, 0.85, 0.82, 0.8]`
- **Default**: 30-day median of historical renewal rates

#### **`fpr` - FIL+ Rate**
- **Type**: `float` or `array` of floats
- **Unit**: Dimensionless fraction (0-1)
- **Range**: 0.0 to 1.0
- **Description**: Fraction of new storage that qualifies for FIL+ verified deals
- **Examples**:
  - Constant: `"fpr": 0.90` (90% FIL+ adoption)
  - Growing: `"fpr": [0.7, 0.75, 0.8, 0.85, 0.9]`
- **Default**: 30-day median of historical FIL+ rates
- **Note**: FIL+ sectors receive 10x quality multiplier for rewards

#### **`lock_target` - Target Lock Ratio**
- **Type**: `float` or `array` of floats
- **Unit**: Dimensionless fraction (0-1)
- **Range**: 0.1 to 0.5 (typically 0.2-0.4)
- **Description**: Target ratio of locked FIL to circulating supply
- **Examples**:
  - Constant: `"lock_target": 0.3` (30% target)
  - Decreasing: `"lock_target": [0.35, 0.32, 0.30, 0.28, 0.25]`
- **Default**: 0.3 (30%)
- **Impact**: Affects initial pledge calculations and network security

### Simulation Configuration

#### **`forecast_length_days` - Forecast Period**
- **Type**: `int`
- **Unit**: Days
- **Range**: 1 to 3650 (1 day to 10 years)
- **Description**: Number of days to forecast beyond current date
- **Examples**: 
  - 1 year: `"forecast_length_days": 365`
  - 5 years: `"forecast_length_days": 1825`
- **Default**: 3650 (10 years)
- **Note**: Longer forecasts require more computation time

#### **`sector_duration_days` - Average Sector Duration**
- **Type**: `int`
- **Unit**: Days
- **Range**: 180 to 1278 (6 months to 3.5 years)
- **Description**: Average commitment duration for storage sectors
- **Examples**:
  - 1 year: `"sector_duration_days": 365`
  - 18 months: `"sector_duration_days": 540` (default)
- **Default**: 540 days (~18 months)
- **Impact**: Affects sector expiration timing and power evolution

### Output Filtering

#### **`output` - Field Selection**
- **Type**: `string`, `array` of strings, or omitted
- **Description**: Specify which output fields to return
- **Options**:
  - Omit for all fields: `{}`
  - Single field: `"output": "available_supply"`
  - Multiple fields: `"output": ["available_supply", "1y_sector_roi", "day_network_reward"]`
  - All fields: `"output": "all"` (same as omitting)

**Available Output Fields** (see complete list in Output Fields Reference):
- `available_supply` - FIL tokens available for new pledges
- `network_RBP_EIB` - Total network raw byte power (EiB)
- `network_QAP_EIB` - Total network quality-adjusted power (EiB)
- `day_network_reward` - Daily FIL rewards minted
- `1y_sector_roi` - Annual return on investment per sector
- `day_pledge_per_QAP` - Daily pledge requirement per PiB QAP
- And 25+ additional fields covering all aspects of network economics

### Time-Varying Parameters

**All core parameters support time-varying values:**

```json
{
  "rbp": [3.0, 3.2, 3.5, 3.8, 4.0],           // Increasing onboarding
  "rr": [0.9, 0.88, 0.85, 0.82, 0.8],         // Declining renewals
  "fpr": [0.7, 0.75, 0.8, 0.85, 0.9],         // Growing FIL+ adoption
  "lock_target": [0.35, 0.32, 0.30, 0.28, 0.25], // Decreasing lock target
  "forecast_length_days": 5
}
```

**Requirements for Arrays**:
- Array length must match `forecast_length_days`
- All values must be within valid ranges
- Arrays enable modeling of changing network conditions

---

## Output Fields Reference

The simulation returns comprehensive economic data covering all aspects of the Filecoin network. Fields are organized by category:

### Storage Power Outputs

#### Raw Byte Power (RBP) Metrics
- **`rb_total_power_eib`**: Total raw byte power (EiB) over time
- **`rb_day_onboarded_power_pib`**: Daily new storage capacity (PiB)
- **`rb_day_renewed_power_pib`**: Daily renewed storage capacity (PiB)
- **`rb_sched_expire_power_pib`**: Daily scheduled storage expirations (PiB)

#### Quality Adjusted Power (QAP) Metrics
- **`qa_total_power_eib`**: Total quality-adjusted power (EiB) - used for rewards
- **`qa_day_onboarded_power_pib`**: Daily new QAP including FIL+ multipliers (PiB)
- **`qa_day_renewed_power_pib`**: Daily renewed QAP (PiB)
- **`qa_sched_expire_power_pib`**: Daily scheduled QAP expirations (PiB)

### Token Minting and Rewards

#### Daily Rewards
- **`day_network_reward`**: Daily FIL tokens minted and distributed

#### Cumulative Rewards
- **`cum_network_reward`**: Total FIL minted since network launch
- **`cum_simple_reward`**: Cumulative time-based minting (30% of allocation)
- **`cum_baseline_reward`**: Cumulative growth-based minting (70% of allocation)

#### Baseline Mechanics
- **`network_baseline_EIB`**: Target storage capacity for baseline rewards (EiB)
- **`capped_power_EIB`**: Power used for baseline calculations (EiB)
- **`cum_capped_power_EIB`**: Cumulative capped power since launch (EiB)
- **`network_time`**: Effective network age based on growth (days)

### Token Supply and Economics

#### Supply Metrics
- **`circ_supply`**: Total FIL tokens in circulation
- **`available_supply`**: FIL available for transactions (circulating - locked)

#### Locked Token Metrics
- **`network_locked`**: Total FIL locked as collateral
- **`network_locked_pledge`**: FIL locked as initial pledge
- **`network_locked_reward`**: FIL locked from block reward vesting
- **`day_locked_pledge`**: Daily pledge locking for new storage
- **`day_renewed_pledge`**: Daily pledge adjustments for renewals

#### Gas and Burning
- **`network_gas_burn`**: Cumulative FIL burned through gas fees

### Vesting Outputs
- **`total_day_vest`**: Daily FIL token vesting amounts
- **`total_vest`**: Cumulative vested FIL since network launch
- **`disbursed_reserve`**: Mining reserve disbursements (~17.07M FIL constant)

### Economic Derived Metrics

#### Storage Provider Economics
- **`day_pledge_per_QAP`**: Daily pledge requirement per PiB QAP (FIL/PiB)
- **`day_rewards_per_sector`**: Daily revenue per 32GiB sector (FIL/sector)
- **`1y_return_per_sector`**: Rolling 12-month returns per sector (FIL/sector)
- **`1y_sector_roi`**: Rolling 12-month ROI (returns/pledge ratio)

#### Network Operations
- **`full_renewal_rate`**: Complete renewal rate time series

### Additional Vesting Components
- **`six_year_vest_pl`**: Protocol Lab vesting (15% allocation)
- **`six_year_vest_foundation`**: Foundation vesting (5% allocation)
- **Various investor vesting schedules**: Multiple timeframes (0 days to 6 years)

### Data Dimensions and Types

**Time Series Fields**: Most fields have dimensions `[total_simulation_length]` where:
- `total_simulation_length = len(historical_data) + forecast_length_days`
- Contains both historical data and forecast results

**ROI Fields**: Have dimensions `[total_simulation_length - 364]` due to 365-day rolling calculations

**Data Types**: All numeric fields are float32 for JAX compatibility

---

## Advanced Usage Examples

### 1. Basic Economic Forecasting

**Scenario**: 1-year forecast with current network trends

```bash
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "forecast_length_days": 365,
    "output": ["available_supply", "1y_sector_roi", "day_network_reward"]
  }'
```

### 2. Storage Provider ROI Analysis

**Scenario**: Analyze mining profitability under different renewal scenarios

```bash
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "rr": [0.9, 0.85, 0.8, 0.75, 0.7],
    "forecast_length_days": 5,
    "output": ["1y_sector_roi", "day_pledge_per_QAP", "day_rewards_per_sector"]
  }'
```

### 3. Policy Impact Modeling

**Scenario**: Model impact of changing lock target policy

```bash
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "lock_target": [0.35, 0.32, 0.30, 0.28, 0.25, 0.22, 0.20],
    "forecast_length_days": 7,
    "output": ["network_locked", "available_supply", "day_pledge_per_QAP"]
  }'
```

### 4. Long-term Network Growth Analysis

**Scenario**: 5-year forecast with growing FIL+ adoption

```bash
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "rbp": 5.0,
    "fpr": 0.9,
    "forecast_length_days": 1825,
    "output": ["network_QAP_EIB", "cum_network_reward", "circ_supply"]
  }'
```

### 5. Sensitivity Analysis

**Scenario**: Test multiple parameter combinations

```bash
# High growth scenario
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "rbp": 6.0,
    "rr": 0.9,
    "fpr": 0.95,
    "forecast_length_days": 365
  }'

# Conservative scenario
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "rbp": 2.0,
    "rr": 0.7,
    "fpr": 0.6,
    "forecast_length_days": 365
  }'
```

### 6. Token Supply Analysis

**Scenario**: Focus on supply and economic metrics

```bash
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "forecast_length_days": 1825,
    "output": [
      "circ_supply",
      "available_supply", 
      "network_locked",
      "day_network_reward",
      "network_gas_burn"
    ]
  }'
```

### 7. Comparative Analysis with Historical Data

**Step 1**: Get historical data for baseline comparison
```bash
curl -X GET http://localhost:8000/historical-data
```

**Step 2**: Run projection with similar parameters
```bash
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "forecast_length_days": 365
  }'
```

### 8. Custom Baseline Scenarios

**Scenario**: Model different network growth trajectories

```bash
# Accelerated growth
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "rbp": [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0],
    "rr": 0.95,
    "fpr": 0.9,
    "forecast_length_days": 7,
    "output": ["network_RBP_EIB", "network_baseline_EIB", "cum_baseline_reward"]
  }'
```

---

## Error Handling

### HTTP Status Codes

- **200**: Success - Request processed successfully
- **422**: Validation Error - Invalid parameter values or types
- **500**: Internal Server Error - Simulation or data processing failed
- **503**: Service Unavailable - Historical data not loaded or server starting up

### Common Error Responses

#### Validation Errors (422)
```json
{
  "detail": [
    {
      "loc": ["body", "rbp"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": {"limit_value": 0}
    }
  ]
}
```

#### Invalid Output Fields (422)
```json
{
  "detail": [
    {
      "loc": ["body", "output"],
      "msg": "Invalid output field(s): ['invalid_field']. Valid fields: [...]",
      "type": "value_error"
    }
  ]
}
```

#### Server Errors (500)
```json
{
  "detail": "Simulation failed: Array length mismatch - forecast_length_days=5 but rbp array length=3"
}
```

#### Service Unavailable (503)
```json
{
  "detail": "Historical data not loaded yet; try again shortly"
}
```

### Error Prevention

1. **Parameter Validation**:
   - Ensure renewal rates and FIL+ rates are between 0 and 1
   - Use positive values for power onboarding
   - Match array lengths to forecast_length_days

2. **Field Name Validation**:
   - Use only valid output field names from the reference
   - Check field names against API documentation

3. **Resource Management**:
   - Avoid extremely long forecast periods (>3650 days) for performance
   - Use appropriate time-varying parameter lengths

### Debugging Tips

1. **Check Server Health**:
```bash
curl http://localhost:8000/health
```

2. **Validate Parameters First**:
   - Test with default parameters: `{}`
   - Add parameters incrementally
   - Check parameter ranges and types

3. **Use Appropriate Endpoint**:
   - Use `/simulate` for all forecasts (returns Monday-downsampled values for efficient data transfer)

---

## Best Practices

### 1. **Parameter Selection**

#### Realistic Parameter Ranges
- **RBP onboarding**: 1-10 PIB/day (historical range: 0.5-6 PIB/day)
- **Renewal rates**: 0.6-0.95 (historical range: 0.7-0.9)
- **FIL+ rates**: 0.3-0.95 (historical range: 0.5-0.9)
- **Lock targets**: 0.15-0.4 (typical range for stability)

#### Historical Context
- Always check `/historical-data` first to understand current trends
- Use smoothed historical values as sensible baselines
- Consider recent network conditions when setting parameters

### 2. **Forecast Planning**

#### Appropriate Forecast Lengths
- **Short-term analysis (1-90 days)**: High accuracy, use for operational planning
- **Medium-term analysis (3-12 months)**: Good for strategic planning
- **Long-term analysis (1-5+ years)**: Scenario analysis and policy research

#### Time-Varying Parameters
- Use arrays for parameters expected to change over time
- Model gradual transitions rather than sudden jumps
- Consider economic and technological trends

### 3. **Output Selection**

#### Field Selection Strategy
- Use `output` parameter to reduce response size and processing time
- Select fields relevant to your analysis focus:
  - **Storage providers**: `1y_sector_roi`, `day_pledge_per_QAP`, `day_rewards_per_sector`
  - **Token economics**: `available_supply`, `circ_supply`, `network_locked`
  - **Network growth**: `network_RBP_EIB`, `network_QAP_EIB`, `day_network_reward`

#### Result Processing
- All simulations return Monday-downsampled values for efficient data transfer
- Use `output` parameter to request only specific fields
- Consider data volume for long forecasts (default 10 years = ~520 Monday values per metric)

### 4. **Performance Optimization**

#### Request Efficiency
- Cache historical data locally when making multiple requests
- Use appropriate forecast lengths for your use case
- Batch similar requests rather than making many small requests

#### Result Handling
- Parse only needed fields from responses
- Consider data storage for large forecast results
- Use appropriate precision for your calculations

### 5. **Validation and Testing**

#### Parameter Validation
- Test edge cases and boundary values
- Validate time-varying parameter arrays
- Verify parameter economic reasonableness

#### Result Validation
- Cross-check key economic relationships:
  - `circ_supply = available_supply + network_locked`
  - `qa_total_power_eib ≤ 10 × rb_total_power_eib` (FIL+ multiplier)
  - Renewal rates should affect power retention

#### Comparative Analysis
- Compare results with historical data for validation
- Test multiple scenarios for robustness
- Validate economic intuitions against results

### 6. **Integration Patterns**

#### API Integration
- Implement proper error handling and retry logic
- Use health checks before critical operations
- Handle service unavailability gracefully

#### Data Processing
- Store and version your simulation parameters
- Document assumptions and parameter choices
- Implement result comparison and difference analysis

#### Monitoring
- Track API response times and success rates
- Monitor result quality and consistency
- Set up alerts for simulation failures

---

## Integration Examples

### Python Integration

```python
import requests
import json
import pandas as pd

class MechaFilClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_historical_data(self):
        response = requests.get(f"{self.base_url}/historical-data")
        return response.json()

    def run_simulation(self, params=None):
        if params is None:
            params = {}

        response = requests.post(
            f"{self.base_url}/simulate",
            json=params,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

        return response.json()
    
    def scenario_analysis(self, scenarios):
        results = {}
        for name, params in scenarios.items():
            try:
                results[name] = self.run_simulation(params)
            except Exception as e:
                print(f"Scenario {name} failed: {e}")
                results[name] = None
        return results

# Usage example
client = MechaFilClient()

# Check server health
print("Server status:", client.health_check())

# Get historical context
hist_data = client.get_historical_data()
print("Recent 30-day averages:")
print("  RBP:", hist_data["data"]["raw_byte_power_averaged_over_previous_30days"])
print("  Renewal rate:", hist_data["data"]["renewal_rate_averaged_over_previous_30days"])
print("  FIL+ rate:", hist_data["data"]["filplus_rate_averaged_over_previous_30days"])

# Run scenarios
scenarios = {
    "baseline": {"forecast_length_days": 365},
    "high_growth": {"rbp": 6.0, "fpr": 0.9, "forecast_length_days": 365},
    "low_renewal": {"rr": 0.7, "forecast_length_days": 365}
}

results = client.scenario_analysis(scenarios)

# Process results (note the new response structure with 'simulation_output')
for scenario_name, result in results.items():
    if result:
        roi_data = result["simulation_output"]["1y_sector_roi"]
        avg_roi = sum(roi_data) / len(roi_data)
        print(f"{scenario_name} average ROI: {avg_roi:.3f}")
```

### JavaScript/Node.js Integration

```javascript
const axios = require('axios');

class MechaFilClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async healthCheck() {
        const response = await axios.get(`${this.baseUrl}/health`);
        return response.data;
    }

    async getHistoricalData() {
        const response = await axios.get(`${this.baseUrl}/historical-data`);
        return response.data;
    }

    async runSimulation(params = {}) {
        try {
            const response = await axios.post(`${this.baseUrl}/simulate`, params, {
                headers: { 'Content-Type': 'application/json' }
            });
            return response.data;
        } catch (error) {
            throw new Error(`API Error: ${error.response?.status} - ${error.response?.data}`);
        }
    }

    async scenarioAnalysis(scenarios) {
        const results = {};

        for (const [name, params] of Object.entries(scenarios)) {
            try {
                results[name] = await this.runSimulation(params);
            } catch (error) {
                console.error(`Scenario ${name} failed:`, error.message);
                results[name] = null;
            }
        }

        return results;
    }
}

// Usage example
async function main() {
    const client = new MechaFilClient();
    
    // Check server health
    const health = await client.healthCheck();
    console.log('Server status:', health);
    
    // Run baseline simulation
    const baselineResult = await client.runSimulation({
        forecast_length_days: 365,
        output: ['available_supply', '1y_sector_roi']
    });

    console.log('Baseline simulation completed');
    console.log('Input parameters:', baselineResult.input);

    // Analyze ROI trends (note the new response structure)
    const roiData = baselineResult.simulation_output['1y_sector_roi'];
    const avgRoi = roiData.reduce((a, b) => a + b, 0) / roiData.length;
    console.log(`Average sector ROI: ${avgRoi.toFixed(3)}`);
}

main().catch(console.error);
```

This comprehensive API instruction guide provides everything needed to effectively use the MechaFil Server API for Filecoin economic simulations and historical data analysis. The combination of detailed parameter references, practical examples, and best practices ensures users can leverage the full power of the simulation engine through the convenient web API interface.