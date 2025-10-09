# MechaFil-JAX Simulation Outputs

This document provides a comprehensive reference for all output variables returned by the MechaFil-JAX simulation via the `run_sim` function.

## Output Structure

The simulation returns a dictionary containing time series data and computed metrics. All time series have dimensions `[total_simulation_length]` where `total_simulation_length = len(historical_data) + forecast_length`.

## Storage Power Outputs

### Raw Byte Power (RBP) Metrics

#### **`rb_total_power_eib`**
- **Type**: `jnp.array`
- **Unit**: EiB (Exbibytes)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Total raw byte power committed to the network over time
- **Notes**: Represents actual storage capacity without quality adjustments

#### **`rb_day_onboarded_power_pib`**
- **Type**: `jnp.array`
- **Unit**: PiB (Pebibytes)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Daily raw byte power onboarded to the network
- **Notes**: New storage capacity added each day

#### **`rb_day_renewed_power_pib`**
- **Type**: `jnp.array`
- **Unit**: PiB (Pebibytes)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Daily raw byte power renewed (extended commitments)
- **Notes**: Storage capacity extended beyond original commitment period

#### **`rb_sched_expire_power_pib`**
- **Type**: `jnp.array`
- **Unit**: PiB (Pebibytes)
- **Dimensions**: `[forecast_length]`
- **Description**: Scheduled raw byte power expirations during forecast period
- **Notes**: Storage commitments naturally expiring based on sector duration

### Quality Adjusted Power (QAP) Metrics

#### **`qa_total_power_eib`**
- **Type**: `jnp.array`
- **Unit**: EiB (Exbibytes)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Total quality-adjusted power on the network
- **Notes**: RBP adjusted for deal quality and FIL+ multipliers; used for reward calculations

#### **`qa_day_onboarded_power_pib`**
- **Type**: `jnp.array`
- **Unit**: PiB (Pebibytes)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Daily quality-adjusted power onboarded
- **Notes**: New QAP added, including FIL+ multipliers

#### **`qa_day_renewed_power_pib`**
- **Type**: `jnp.array`
- **Unit**: PiB (Pebibytes)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Daily quality-adjusted power renewed
- **Notes**: QAP from renewed storage commitments

#### **`qa_sched_expire_power_pib`**
- **Type**: `jnp.array`
- **Unit**: PiB (Pebibytes)
- **Dimensions**: `[forecast_length]`
- **Description**: Scheduled quality-adjusted power expirations
- **Notes**: QAP lost due to natural sector expiration

## Token Minting and Rewards

### Daily Rewards

#### **`day_network_reward`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Daily FIL tokens minted and distributed to storage providers
- **Notes**: Combined simple and baseline minting rewards

### Cumulative Rewards

#### **`cum_network_reward`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Cumulative network rewards minted since network launch
- **Notes**: Total FIL minted for storage mining

#### **`cum_simple_reward`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Cumulative simple minting rewards (time-based)
- **Notes**: 30% of storage mining allocation, follows exponential decay

#### **`cum_baseline_reward`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Cumulative baseline minting rewards (storage growth-based)
- **Notes**: 70% of storage mining allocation, tied to network growth

### Baseline and Power Metrics

#### **`network_baseline_EIB`**
- **Type**: `jnp.array`
- **Unit**: EiB (Exbibytes)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Network storage baseline power trajectory
- **Notes**: Target storage capacity for baseline reward release

#### **`capped_power_EIB`**
- **Type**: `jnp.array`
- **Unit**: EiB (Exbibytes)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Power used for baseline minting calculations
- **Notes**: Minimum of network power and baseline power

#### **`cum_capped_power_EIB`**
- **Type**: `jnp.array`
- **Unit**: EiB (Exbibytes)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Cumulative capped power since network launch
- **Notes**: Used to determine network time for baseline rewards

#### **`network_time`**
- **Type**: `jnp.array`
- **Unit**: Days (effective network age)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Effective network time based on cumulative capped power
- **Notes**: Used in baseline reward calculations

## Token Supply and Economics

### Supply Metrics

#### **`circ_supply`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Total FIL tokens in circulation
- **Notes**: Includes vested, minted, and unlocked tokens

#### **`available_supply`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: FIL tokens available for transactions and new pledges
- **Notes**: Circulating supply minus locked tokens

### Locked Token Metrics

#### **`network_locked`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Total FIL tokens locked as collateral
- **Notes**: Sum of locked pledge and locked rewards

#### **`network_locked_pledge`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: FIL locked as initial pledge collateral
- **Notes**: Collateral posted when onboarding storage

#### **`network_locked_reward`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: FIL locked from block reward vesting
- **Notes**: Portion of mining rewards locked as additional collateral

#### **`day_locked_pledge`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Daily pledge locking for new storage
- **Notes**: Initial pledge required for new sectors

#### **`day_renewed_pledge`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Daily pledge adjustments for renewed sectors
- **Notes**: Pledge changes when extending sector commitments

### Gas and Burning

#### **`network_gas_burn`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Cumulative FIL tokens burned through gas fees
- **Notes**: Permanently removed from token supply

## Vesting Outputs

#### **`total_day_vest`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Daily FIL token vesting amounts
- **Notes**: Tokens released from various vesting schedules

#### **`total_vest`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Cumulative vested FIL tokens since network launch
- **Notes**: Total tokens released from all vesting schedules

#### **`disbursed_reserve`**
- **Type**: `jnp.array`
- **Unit**: FIL tokens
- **Dimensions**: `[total_simulation_length]`
- **Description**: Mining reserve disbursements
- **Notes**: Currently constant at ~17.07M FIL

## Economic Derived Metrics

### Storage Provider Economics

#### **`day_pledge_per_QAP`**
- **Type**: `jnp.array`
- **Unit**: FIL per PiB
- **Dimensions**: `[total_simulation_length]`
- **Description**: Daily pledge requirement per PiB of quality-adjusted power
- **Notes**: Key metric for storage provider capital requirements

#### **`day_rewards_per_sector`**
- **Type**: `jnp.array`
- **Unit**: FIL per sector
- **Dimensions**: `[total_simulation_length]`
- **Description**: Daily rewards per 32GiB sector
- **Notes**: Revenue per sector for storage providers

#### **`1y_return_per_sector`**
- **Type**: `jnp.array`
- **Unit**: FIL per sector
- **Dimensions**: `[total_simulation_length - 364]`
- **Description**: Rolling 12-month returns per sector
- **Notes**: Annual revenue per sector (365-day moving sum)

#### **`1y_sector_roi`**
- **Type**: `jnp.array`
- **Unit**: Dimensionless ratio
- **Dimensions**: `[total_simulation_length - 364]`
- **Description**: Rolling 12-month return on investment per sector
- **Notes**: Annual returns divided by pledge requirement; key profitability metric

### Network Operations

#### **`full_renewal_rate`**
- **Type**: `jnp.array`
- **Unit**: Dimensionless (fraction)
- **Dimensions**: `[total_simulation_length]`
- **Description**: Complete renewal rate time series (historical + forecast)
- **Notes**: Concatenation of historical data and forecast parameters

## Data Access Example

```python
import matplotlib.pyplot as plt
import mechafil_jax.constants as C

# Run simulation
results = sim.run_sim(...)

# Access power metrics
total_rbp_eib = results['rb_total_power_eib']
total_qap_eib = results['qa_total_power_eib']

# Access economic metrics
daily_rewards = results['day_network_reward']
circ_supply = results['circ_supply']
locked_tokens = results['network_locked']

# Access derived metrics
sector_roi = results['1y_sector_roi']
pledge_per_qap = results['day_pledge_per_QAP']

# Create time axis for plotting
from datetime import timedelta
total_sim_len = len(total_rbp_eib)
dates = [start_date + timedelta(days=i) for i in range(total_sim_len)]

# Plot key metrics
plt.figure(figsize=(12, 8))

plt.subplot(2, 2, 1)
plt.plot(dates, total_rbp_eib)
plt.title('Network Raw Byte Power')
plt.ylabel('EiB')

plt.subplot(2, 2, 2)
plt.plot(dates, daily_rewards)
plt.title('Daily Network Rewards')
plt.ylabel('FIL/day')

plt.subplot(2, 2, 3)
plt.plot(dates, circ_supply / 1e6)
plt.title('Circulating Supply')
plt.ylabel('M-FIL')

plt.subplot(2, 2, 4)
plt.plot(dates[:-364], sector_roi)
plt.title('Annual Sector ROI')
plt.ylabel('Return Ratio')

plt.tight_layout()
plt.show()
```

## Output Validation

Key relationships to verify simulation accuracy:

1. **Power Conservation**: `qa_total_power_eib ≤ fil_plus_m × rb_total_power_eib`
2. **Supply Balance**: `circ_supply = available_supply + network_locked`
3. **Reward Consistency**: `day_network_reward = diff(cum_network_reward)`
4. **Lock Target**: `network_locked / circ_supply ≈ lock_target` (over time)
5. **Pledge Calculation**: `day_pledge_per_QAP = day_locked_pledge / qa_day_onboarded_power_pib`

All arrays use float32 precision for JAX compatibility and performance optimization.