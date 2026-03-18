# Fix: `raw_byte_power` unit is PiB/day, not EiB/day

## The Issue

The onboarding rate (`raw_byte_power` / `rbp`) is documented everywhere as **EiB/day**.
The actual unit flowing through the entire stack is **PiB/day**.

## Root Cause — Code References

| File | Line | Content |
|------|------|---------|
| `pystarboard/data_spacescope.py` | 170 | `df['day_onboarded_rb_power_pib'] = (...) / PIB` — source data is bytes ÷ 2^50 = **PiB** |
| `mechafil-jax/mechafil_jax/data.py` | 75 | `"historical_onboarded_rb_power_pib": fil_stats_df["day_onboarded_rb_power_pib"].values` — PiB passed through |
| `mechafil-jax/mechafil_jax/sim.py` | 107 | concatenates historical PiB values with forecast PiB values; divides total power by 1024 **only for the EiB output stock** |
| `mechafil-server/services/cache_updater/data.py` | 339 | `hist_rbp = df["day_onboarded_rb_power_pib"].values` — stored as PiB/day |
| `mechafil-server/services/cache_updater/data.py` | 63 | `smoothed_rbp = float(np.median(hist_rbp[-30:]))` — 30-day median in PiB/day |

## Where the Wrong Label Is Introduced

| File | Line(s) | Wrong text |
|------|---------|------------|
| `mechafil-server/services/api/results.py` | 312 | alias name: `raw_byte_power_onboarded_eib_per_day` |
| `mechafil-server/services/api/results.py` | 320–321, 328 | `field_meta` units: `"unit": "EiB/day"` for `raw_byte_power`, alias, and 30-day median |
| `mcp-server-mechafil/server.py` | 106 | `SimulationInputs.rbp` description: `"Raw Byte Power onboarding in EiB/day"` |
| `mcp-server-mechafil/documentation-and-instructions/mcp-tools-context.txt` | 31, 36, 74 | field dict and simulate args: `EiB/day` |
| `mcp-server-mechafil/documentation-and-instructions/examples.txt` | 83, 104, 180 | narrative text: `"3.38 EiB/day"` |

## Actions

### 1. `mechafil-server/services/api/results.py`
- Change `field_meta` unit strings from `"EiB/day"` → `"PiB/day"` for `raw_byte_power`, `raw_byte_power_onboarded_eib_per_day`, and `raw_byte_power_averaged_over_previous_30days`.
- Add a new alias `raw_byte_power_onboarded_pib_per_day` pointing to the same value; keep `raw_byte_power_onboarded_eib_per_day` to avoid breaking existing callers.
- Update `field_meta` entry for the old alias to also say `"PiB/day"` with a deprecation note.

### 2. `mcp-server-mechafil/server.py`
- Change `rbp` field description from `"EiB/day"` → `"PiB/day"`.

### 3. `mcp-server-mechafil/documentation-and-instructions/mcp-tools-context.txt`
- Replace all `EiB/day` occurrences that refer to the onboarding *rate* with `PiB/day`.
- Leave `EiB` references for total power stocks (`historical_raw_power_eib`, `historical_qa_power_eib`) unchanged — those are correct.

### 4. `mcp-server-mechafil/documentation-and-instructions/examples.txt`
- Replace narrative "3.38 EiB/day" → "3.38 PiB/day" in all examples.

## What Does NOT Change
- The simulation logic — no code changes, only labels.
- `historical_raw_power_eib` / `historical_qa_power_eib` units — these are total network power stocks in EiB and are correct.
- API response field names (except adding the new `_pib_per_day` alias).
