# MechaFil-JAX Simulation Inputs

This document provides a comprehensive reference for all input parameters required to run a MechaFil-JAX simulation using the `run_sim` function.

## Required Parameters

### 1. **`rb_onboard_power`**
- **Type**: `jnp.array`
- **Unit**: EiB (Exbibytes)
- **Dimensions**: `[forecast_length]`
- **Description**: The raw byte power onboarded to the network per day during the forecast period
- **Example**: `jnp.ones(365) * 6.0` (6 EiB per day for 365 days)
- **Notes**: This represents the daily storage capacity additions from new sectors

### 2. **`renewal_rate`**
- **Type**: `jnp.array`
- **Unit**: Dimensionless (fraction between 0 and 1)
- **Dimensions**: `[forecast_length]`
- **Description**: The fraction of expiring sectors that get renewed each day
- **Example**: `jnp.ones(365) * 0.6` (60% renewal rate)
- **Notes**: Higher values indicate more sector renewals, affecting power retention

### 3. **`fil_plus_rate`**
- **Type**: `jnp.array`
- **Unit**: Dimensionless (fraction between 0 and 1)
- **Dimensions**: `[forecast_length]`
- **Description**: The fraction of new storage that qualifies for FIL+ verified deals
- **Example**: `jnp.ones(365) * 0.3` (30% of new storage gets FIL+ multiplier)
- **Notes**: FIL+ sectors receive higher quality-adjusted power and rewards

### 4. **`lock_target`**
- **Type**: `float` or `jnp.array`
- **Unit**: Dimensionless (fraction between 0 and 1)
- **Dimensions**: Scalar or `[forecast_length]`
- **Description**: Target ratio of locked FIL to circulating supply
- **Default**: `0.3` (30% lock target)
- **Example**: `0.25` or `jnp.linspace(0.3, 0.25, 365)` (decreasing from 30% to 25%)
- **Notes**: Affects initial pledge calculations; can be time-varying

### 5. **`start_date`**
- **Type**: `datetime.date`
- **Description**: The start date of the simulation period
- **Example**: `date(2023, 6, 1)`
- **Notes**: Must align with available historical data

### 6. **`current_date`**
- **Type**: `datetime.date`
- **Description**: The boundary date separating historical data from forecasts
- **Example**: `date.today() - timedelta(days=3)`
- **Notes**: Should be recent but allow for data lag

### 7. **`forecast_length`**
- **Type**: `int`
- **Unit**: Days
- **Description**: Number of days to forecast beyond current_date
- **Example**: `365` (one year forecast)
- **Notes**: Determines the length of all forecast arrays

### 8. **`duration`**
- **Type**: `int`
- **Unit**: Days
- **Description**: Average sector commitment duration
- **Example**: `360` (approximately 1 year)
- **Notes**: Affects sector expiration timing and power evolution

### 9. **`data`**
- **Type**: `Dict`
- **Description**: Historical network data dictionary containing multiple time series and initial values
- **Source**: Retrieved via `mechafil_jax.data.get_simulation_data()`

#### Required Data Dictionary Keys:

##### Power Statistics (Initial Values)
- **`rb_power_zero`** (float): Initial raw byte power in PiB
- **`qa_power_zero`** (float): Initial quality-adjusted power in PiB

##### Historical Power Time Series
- **`historical_raw_power_eib`** (array): Daily RBP history in EiB
- **`historical_qa_power_eib`** (array): Daily QAP history in EiB
- **`historical_onboarded_rb_power_pib`** (array): Daily RBP onboarding in PiB
- **`historical_onboarded_qa_power_pib`** (array): Daily QAP onboarding in PiB
- **`historical_renewed_qa_power_pib`** (array): Daily QAP renewals in PiB
- **`historical_renewed_rb_power_pib`** (array): Daily RBP renewals in PiB
- **`historical_renewal_rate`** (array): Historical renewal rates

##### Scheduled Expirations
- **`rb_known_scheduled_expire_vec`** (array): Known RBP expirations in PiB
- **`qa_known_scheduled_expire_vec`** (array): Known QAP expirations in PiB
- **`known_scheduled_pledge_release_full_vec`** (array): Scheduled pledge releases in FIL

##### Vesting and Minting
- **`start_vested_amt`** (int): Initial vested amount in attoFIL
- **`zero_cum_capped_power_eib`** (float): Initial cumulative capped power in EiB
- **`init_baseline_eib`** (float): Initial baseline power in EiB

##### Supply and Economics
- **`circ_supply_zero`** (float): Initial circulating supply in FIL
- **`locked_fil_zero`** (float): Initial locked FIL amount
- **`daily_burnt_fil`** (float): Average daily gas burn in FIL
- **`burnt_fil_vec`** (array): Historical cumulative gas burn in FIL

## Optional Parameters

### 10. **`baseline_function_EIB`**
- **Type**: `jnp.array`
- **Unit**: EiB
- **Dimensions**: `[total_simulation_length]`
- **Default**: `None` (computed automatically using exponential growth)
- **Description**: Custom baseline power trajectory for the entire simulation period
- **Notes**: If provided, overrides default baseline calculation

### 11. **`fil_plus_m`**
- **Type**: `float` or `jnp.array`
- **Unit**: Dimensionless multiplier
- **Dimensions**: Scalar or `[forecast_length]`
- **Default**: `10.0`
- **Description**: Quality multiplier for FIL+ verified deals
- **Example**: `9.0` or `jnp.linspace(10.0, 9.0, 365)` (decreasing multiplier)
- **Notes**: Standard FIL+ provides 10x quality boost

### 12. **`qa_renew_relative_multiplier_vec`**
- **Type**: `jnp.array`
- **Unit**: Dimensionless multiplier
- **Dimensions**: `[forecast_length]`
- **Default**: `1.0`
- **Description**: Relative multiplier for QA power during renewals
- **Example**: `jnp.ones(365) * 1.1` (10% boost for renewals)
- **Notes**: Affects quality-adjusted power calculations for renewed sectors

### 13. **`burn_boost`**
- **Type**: `float` or `jnp.array`
- **Unit**: Dimensionless multiplier
- **Dimensions**: Scalar or `[forecast_length]`
- **Default**: `1.0`
- **Description**: Multiplier for gas burning rates
- **Example**: `1.2` (20% increase in burn rate)
- **Notes**: Used for scenario analysis of gas fee impacts

### 14. **`use_available_supply`**
- **Type**: `bool`
- **Default**: `False`
- **Description**: Whether to use available supply instead of circulating supply for pledge calculations
- **Notes**: Affects initial pledge requirements and network economics

## Data Retrieval

The historical data dictionary is typically obtained using:

```python
import mechafil_jax.data as data
from datetime import date, timedelta

# Authentication token for Spacescope API
token = '/path/to/spacescope_auth.json'

# Date range
start_date = date(2023, 6, 1)
current_date = date.today() - timedelta(days=3)
end_date = current_date + timedelta(days=forecast_length)

# Retrieve data
offline_data = data.get_simulation_data(token, start_date, current_date, end_date)
```

## Parameter Validation

- **Array Dimensions**: All forecast arrays (`rb_onboard_power`, `renewal_rate`, `fil_plus_rate`) must have length `forecast_length`
- **Date Consistency**: `current_date` must be after `start_date`
- **Rate Bounds**: Renewal and FIL+ rates should be between 0 and 1
- **Power Values**: Power values should be positive
- **Data Alignment**: Historical data must cover the period from `start_date` to `current_date`

## Example Parameter Setup

```python
import jax.numpy as jnp
from datetime import date, timedelta

# Simulation configuration
forecast_length = 365
start_date = date(2023, 6, 1)
current_date = date.today() - timedelta(days=3)

# Core parameters
rb_onboard_power = jnp.ones(forecast_length) * 6.0  # 6 EiB/day
renewal_rate = jnp.ones(forecast_length) * 0.6      # 60% renewal rate
fil_plus_rate = jnp.ones(forecast_length) * 0.3     # 30% FIL+ rate
lock_target = 0.3                                   # 30% lock target
duration = 360                                      # ~1 year sectors

# Run simulation
results = sim.run_sim(
    rb_onboard_power=rb_onboard_power,
    renewal_rate=renewal_rate,
    fil_plus_rate=fil_plus_rate,
    lock_target=lock_target,
    start_date=start_date,
    current_date=current_date,
    forecast_length=forecast_length,
    duration=duration,
    data=offline_data
)
```