# MCP Knowledge & Access Gaps Assessment

This document catalogues quantities the MCP agent will likely misrepresent, cannot access, or can only approximate
through indirect means. Items are grouped by severity.

---

## Critical — likely to produce wrong answers silently

### 1. `raw_byte_power` / `rbp` unit is PiB/day, not EiB/day

**Location**: `server.py` `SimulationInputs.rbp` description, `mcp-tools-context.txt`, `examples.txt`.

**Problem**: Every mention of the onboarding rate in the MCP documentation says "EiB/day".
The actual unit flowing through the API is **PiB/day**.

Evidence: `cache_updater/data.py` line 339 — `hist_rbp` is read directly from `df["day_onboarded_rb_power_pib"].values`
and the 30-day median (`smoothed_rbp ≈ 3.38`) is passed as-is to `run_sim()` which internally expects PiB.
A value of 3.38 EiB/day would equal ~3460 PiB/day — physically impossible for the Filecoin network.

**Effect**: The narrative "current onboarding is 3.38 EiB/day" is factually wrong.
Users comparing MCP outputs to external Filecoin dashboards (which show PiB/day) will be confused.
Custom `rbp` inputs from users will be interpreted in PiB by the simulation regardless of the documented unit.

**Fix**: Change all "EiB/day" references for `raw_byte_power` / `rbp` to **"PiB/day"**.

---

### 2. No on-chain historical time series for locked FIL or circulating supply

**Problem**: `/historical-data` exposes historical arrays only for RBP onboarding, renewal rate, and FIL+ rate
(back to `STARTUP_DATE = 2022-10-10`). It does **not** expose `locked_fil` or `circ_supply` as time series.

Only `locked_fil_zero` and `circ_supply_zero` are available — both are **scalars** seeded from
`current_date − 1` (yesterday's on-chain state), not the full historical evolution.

**Effect**:
- Cannot answer "How has locked FIL evolved over the past year?"
- Cannot plot circulating supply vs. on-chain data.
- `simulate` produces a model trajectory for these quantities, but that is a *projection*, not historical observation.
- Example 2 in `examples.txt` directs the agent to report `locked_fil_zero` as "currently locked" — this is
  approximately correct for today's snapshot, but gives no trend context and is 1 day stale.

---

### 3. `locked_fil_zero` is total locked, not just pledge collateral

**Location**: `examples.txt` Example 2, `mcp-tools-context.txt` scalar field list.

**Problem**: Example 2 instructs the agent to answer "how much FIL is locked **as pledge**?" using `locked_fil_zero`.
But `locked_fil_zero` is the **total** network locked amount, which includes both:
- Pledge collateral (`network_locked_pledge`)
- Reward vesting locked (`network_locked_reward`, ~75% of block rewards vesting over 180 days)

In practice the reward component is roughly 40–60% of total locked FIL.

**Effect**: Answering "X M FIL is locked as pledge" when `locked_fil_zero` includes reward vesting overstates
pledge collateral substantially. The pledge/reward split is only available from `simulate` (model estimate),
not from `/historical-data`.

---

## Significant — degrades answer quality or creates silent truncation

### 4. `1y_sector_roi` is shorter than all other simulation arrays

**Problem**: In `sim.py` (lines 199-201), `1y_sector_roi` is computed via a 365-day rolling convolution:

```python
rps = jnp.convolve(results['day_rewards_per_sector'], jnp.ones(365), mode='full')
results['1y_sector_roi'] = rps[364:1-365] / results['day_pledge_per_QAP'][:1-365]
```

The resulting array has `forecast_length_days - 364` elements (approximately).

**Effect**:
- For `forecast_length_days = 365`, the ROI array contains only **1 element**.
- For any horizon ≤ 364 days, the ROI array is empty or errors.
- The MCP docs do not mention this truncation. If the agent reads "first value = current ROI, last value = end ROI",
  it will miss that the last meaningful ROI value is 364 days before the end of the forecast.
- After Monday downsampling, the array is further shortened (÷7 approximately).

**Mitigation**: Always set `forecast_length_days ≥ 730` when requesting `1y_sector_roi`.
The docs should explicitly state this.

---

### 5. Simulation arrays start at `current_date`, not `current_date − 1`

**Problem**: The 1-day simulation window means `start_date = current_date − 1`.
The first element of simulation output arrays (index 0) is seeded from yesterday's on-chain state,
and the second element (index 1) is the first *modelled* step at `current_date`.

**Effect**: When the MCP reports "current ROI is X" using `simulation_output[0]`, it is actually
reporting the value at `current_date − 1` (yesterday), not today. This 1-day lag is invisible to the agent.
For slowly-varying quantities (power, supply) this is negligible; for faster-moving rates it may matter.

---

### 6. No burnt FIL historical time series

**Problem**: The gas burn history is exposed as two opaque model seeds:
- `daily_burnt_fil`: a scalar (mean daily burn rate)
- `burnt_fil_vec`: a raw cumulative burn vector used to initialize the simulation, not labeled or dated

**Effect**: Cannot answer "How has daily gas burn evolved?" or "What is today's burn rate?"
without additional context. The MCP has no clear way to interpret `burnt_fil_vec` as a time series
(it lacks explicit date anchoring in the API response).

---

### 7. Monday downsampling loses daily resolution

**Problem**: Both `/simulate` and `/historical-data` responses are downsampled to Mondays.
Dates are not returned alongside array values — the agent must reconstruct them from `data_start_date` + 7-day steps.

**Effect**:
- "What is the value on [specific date]?" requires rounding to the nearest Monday.
- Weekly aggregation can obscure daily volatility in RBP onboarding or renewal rate.
- `1y_sector_roi` is already shorter than other arrays; after downsampling it may have far fewer points than expected
  (e.g., 52 values for a 1-year forecast, but only 1 or 2 after truncation for ROI).

---

## Minor — edge cases or cosmetic issues

### 8. No FIL/USD price data

The MCP has no access to FIL price. All simulation outputs are in FIL terms.
Users asking for returns in USD must supply the exchange rate themselves.
The `filecoin-context.txt` correctly flags price volatility as a risk but provides no data.

---

### 9. `sector_duration_days` default of 540 may not reflect common practice

The default sector duration is 540 days (≈18 months), but 360-day (≈12-month) contracts have become
increasingly common among storage providers. Pledge estimates and ROI projections can differ noticeably
between these durations. The MCP docs do not prompt the agent to ask the user whether to override the default.

---

### 10. Actual current lock ratio is not directly accessible

The consensus pledge formula targets `lock_target = 0.3` (30% of circulating supply locked).
Neither `/historical-data` nor `/simulate` returns the **current observed** lock ratio
(`locked_fil / circ_supply`). The agent cannot verify whether today's network is above or below target
without computing it from `locked_fil_zero / circ_supply_zero` — two scalars that are available,
but not documented as a ratio in the MCP tools context.

---

### 11. `simulate` cannot model custom gas burn scenarios

Gas burn rate is fixed at the historical daily average (`daily_burnt_fil`) for the entire forecast horizon.
There is no API parameter to specify a custom gas burn trajectory. Users interested in
"what if gas fees increase?" supply scenarios cannot model this with the current tools.

---

### 12. `/simulate/full-with-history` endpoint exists but MCP doesn't use it

The API exposes `/simulate/full-with-history` which returns both the historical model trajectory
and the forecast in a single response. This would allow the agent to compare model output against
on-chain data within a single call. The MCP currently only calls `/simulate` (forecast-only, no history)
and `/historical-data` (on-chain rates only, no supply/locked). This gap means model vs. on-chain
comparisons for `circ_supply` or `network_locked` are not straightforward for the MCP.

---

## Summary Table

| # | Quantity / Issue | Severity | Data Available? | Notes |
|---|-----------------|----------|-----------------|-------|
| 1 | `raw_byte_power` / `rbp` unit (PiB vs EiB) | Critical | Yes (wrong label) | Fix docs |
| 2 | Locked FIL time series | Critical | No | Scalar only |
| 3 | `locked_fil_zero` = total locked, not pledge | Critical | Partial | Misleading example |
| 4 | `1y_sector_roi` truncation | Significant | Implicit | Needs horizon ≥ 730d |
| 5 | Simulation starts from `current_date − 1` | Significant | Yes (undocumented) | 1-day lag |
| 6 | Burnt FIL historical series | Significant | No labeled series | Scalar only |
| 7 | Monday-only resolution | Significant | By design | Date reconstruction needed |
| 8 | FIL/USD price | Minor | No | User must supply |
| 9 | `sector_duration` default vs. market reality | Minor | Configurable | Prompt user to set |
| 10 | Current lock ratio | Minor | Computable from scalars | Not documented |
| 11 | Custom gas burn scenarios | Minor | No | Fixed in simulation |
| 12 | `/simulate/full-with-history` unused | Minor | Available in API | MCP doesn't call it |
