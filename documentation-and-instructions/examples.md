# MCP MechaFil Tool Usage Examples
When you see ... in the examples, it means ‘fill in the analysis based on the tool output and conversation context.
## Current State Queries

### Example 1: FIL+ Adoption Rate

```
PROMPT: "What is the current FIL+ adoption rate?"

TOOL: get_historical_data()

OUTPUT:
{
  "data": {
    "raw_byte_power_averaged_over_previous_30days": 3.38,
    "renewal_rate_averaged_over_previous_30days": 0.83,
    "filplus_rate_averaged_over_previous_30days": 0.86,
    "raw_byte_power": [2.1, 2.3, 2.5, ...],
    "renewal_rate": [0.75, 0.78, 0.82, ...],
    "filplus_rate": [0.80, 0.83, 0.85, ...],
    "rb_power_zero": 1234.56,
    "qa_power_zero": 2345.67,
    "circ_supply_zero": 123456789.12,
    "locked_fil_zero": 45678901.23,
    "historical_raw_power_eib": [12.5, 13.1, ...],
    "historical_qa_power_eib": [45.2, 46.1, ...],
    ...
  }
}

ACTION:
1. Parse the JSON response
2. Extract data["filplus_rate_averaged_over_previous_30days"]
3. Convert to percentage: 0.86 = 86%
4. Respond: "The current FIL+ adoption rate is 86% (30-day average)."
```

### Example 2: Current Locked FIL

```
PROMPT: "How much FIL is currently locked as pledge?"

TOOL: get_historical_data()

OUTPUT:
{
  "data": {
    "raw_byte_power_averaged_over_previous_30days": 3.38,
    "renewal_rate_averaged_over_previous_30days": 0.83,
    "filplus_rate_averaged_over_previous_30days": 0.86,
    "locked_fil_zero": 145678901.23,
    ...
  }
}

ACTION:
1. Parse the JSON response
2. Extract data["locked_fil_zero"]
3. Format the number: 145678901.23 ≈ 145.7M FIL
4. Respond: "Currently, approximately 145.7 million FIL is locked as pledge collateral."
```

### Example 3: Recent Onboarding Rate

```
PROMPT: "What's the recent onboarding rate been?"

TOOL: get_historical_data()

OUTPUT:
{
  "data": {
    "raw_byte_power_averaged_over_previous_30days": 3.38,
    "raw_byte_power": [2.8, 3.0, 3.2, 3.3, 3.4, 3.5, 3.4, 3.38],
    ...
  }
}

ACTION:
1. Parse the JSON response
2. Extract data["raw_byte_power_averaged_over_previous_30days"] = 3.38
3. Optionally extract data["raw_byte_power"] to show trend
4. Respond: "The recent onboarding rate is 3.38 EiB/day (30-day average). Looking at the weekly trend,
   it has been gradually increasing from 2.8 to 3.38 EiB/day over the past few weeks."
```

---

## Future Projection Queries

### Example 4: Next Year's ROI

```
PROMPT: "What will storage provider ROI be next year?"

TOOL: simulate({
  "forecast_length_days": 365,
  "requested_metric": "1y_sector_roi"
})

OUTPUT:
{
  "1y_sector_roi": [0.18, 0.177, 0.174, 0.171, ..., 0.15],
  "Explanation": "Results of a Filecoin simulation with the following input values: Raw byte power (rbp) onboarded: 3.38, Renewal rate (rr): 0.83, Filplus deals rate (fpr): 0.86"
}

ACTION:
1. Parse the response
2. Extract first value (current): 0.18 = 18%
3. Extract last value (end of year): 0.15 = 15%
4. Calculate trend: declining from 18% to 15%
5. Respond: "Under current network conditions (rbp=3.38, rr=0.83, fpr=0.86), storage provider ROI
   is projected to decline from 18% to 15% over the next year."
```

### Example 5: Network Capacity Growth

```
PROMPT: "How will network capacity grow over the next 6 months?"

TOOL: simulate({
  "forecast_length_days": 180,
  "requested_metric": "network_QAP_EIB"
})

OUTPUT:
{
  "network_QAP_EIB": [35.2, 35.8, 36.4, 37.0, ..., 42.1],
  "Explanation": "Results of a Filecoin simulation with the following input values: Raw byte power (rbp) onboarded: 3.38, Renewal rate (rr): 0.83, Filplus deals rate (fpr): 0.86"
}

ACTION:
1. Parse the response
2. Extract first value: 35.2 EiB (current)
3. Extract last value: 42.1 EiB (6 months)
4. Calculate growth: 42.1 - 35.2 = 6.9 EiB increase
5. Calculate percentage: (6.9 / 35.2) * 100 = 19.6% growth
6. Respond: "Network quality-adjusted power is projected to grow from 35.2 EiB to 42.1 EiB over the
   next 6 months, representing a 19.6% increase under current onboarding rates (3.38 EiB/day)."
```

### Example 6: Circulating Supply Projection

```
PROMPT: "Show me circulating supply projections for the next 2 years"

TOOL: simulate({
  "forecast_length_days": 730,
  "requested_metric": "circ_supply"
})

OUTPUT:
{
  "circ_supply": [580250000.12, 582100000.45, 584000000.78, ..., 650000000.00],
  "Explanation": "Results of a Filecoin simulation with the following input values: Raw byte power (rbp) onboarded: 3.38, Renewal rate (rr): 0.83, Filplus deals rate (fpr): 0.86"
}

ACTION:
1. Parse the response
2. Extract first value: 580.25M FIL (current)
3. Extract last value: 650M FIL (2 years)
4. Calculate increase: 650 - 580.25 = 69.75M FIL
5. Calculate annual rate: (69.75 / 580.25) / 2 * 100 = 6.0% per year
6. Respond: "Circulating FIL supply is projected to increase from 580.25M to 650M FIL over the next
   2 years, representing an average annual growth rate of approximately 6%. "
```

---

## Scenario Analysis Queries

### Example 7: High Onboarding Impact

```
PROMPT: "What if onboarding increases to 8 EiB/day - how would that affect ROI?"

STEP 1 - Get baseline:
TOOL: get_historical_data()
OUTPUT: { "data": { "raw_byte_power_averaged_over_previous_30days": 3.38, ... } }
ACTION: Note current onboarding is 3.38 EiB/day

STEP 2 - Run baseline scenario:
TOOL: simulate({
  "forecast_length_days": 365,
  "requested_metric": "1y_sector_roi"
})
OUTPUT: { "1y_sector_roi": [0.18, 0.177, ..., 0.15], "Explanation": "..." }
ACTION: Store baseline projection (18% → 15%)

STEP 3 - Run high onboarding scenario:
TOOL: simulate({
  "rbp": 8.0,
  "forecast_length_days": 365,
  "requested_metric": "1y_sector_roi"
})
OUTPUT: { "1y_sector_roi": [0.18, 0.165, ..., 0.10], "Explanation": "..." }
ACTION: Store high onboarding projection (18% → 10%)

RESPONSE:
"Increasing onboarding from 3.38 EiB/day (current) to 8 EiB/day would impact ROI: ..."
```

### Example 8: FIL+ Rate Reduction Impact

```
PROMPT: "How would reducing FIL+ rate to 50% impact network economics?"

STEP 1 - Get current state:
TOOL: get_historical_data()
OUTPUT: { "data": { "filplus_rate_averaged_over_previous_30days": 0.86, ... } }
ACTION: Note current FIL+ rate is 86%

STEP 2 - Run baseline (current FIL+):
TOOL: simulate({
  "forecast_length_days": 365,
  "requested_metric": "1y_sector_roi"
})
OUTPUT: { "1y_sector_roi": [0.18, ..., 0.15], "Explanation": "..." }

STEP 3 - Run low FIL+ scenario for ROI:
TOOL: simulate({
  "fpr": 0.5,
  "forecast_length_days": 365,
  "requested_metric": "1y_sector_roi"
})
OUTPUT: { "1y_sector_roi": [0.18, ..., 0.19], "Explanation": "..." }

STEP 4 - Run low FIL+ scenario for network power:
TOOL: simulate({
  "fpr": 0.5,
  "forecast_length_days": 365,
  "requested_metric": "network_QAP_EIB"
})
OUTPUT: { "network_QAP_EIB": [35.2, ..., 32.1], "Explanation": "..." }

STEP 5 - Run low FIL+ scenario for pledge requirements:
TOOL: simulate({
  "fpr": 0.5,
  "forecast_length_days": 365,
  "requested_metric": "day_pledge_per_QAP"
})
OUTPUT: { "day_pledge_per_QAP": [0.25, ..., 0.18], "Explanation": "..." }

RESPONSE:
"...

1. **Provider ROI**: ...

2. **Network Capacity**: ...

3. **Pledge Requirements**: ...

..."
```

### Example 9: Growth Scenario Comparison

```
PROMPT: "Compare high growth vs low growth  scenarios"

STEP 1 - Get context:
TOOL: get_historical_data()
OUTPUT: { "data": { "raw_byte_power_averaged_over_previous_30days": 3.38, ... } }
ACTION: Note baseline is 3.38 EiB/day
ACTION: Define high growth and low growth e.g. +50% than baseline = 5.07 and -50% than baseline = 1.69

STEP 2 - Run high growth scenario:
TOOL: simulate({
  "rbp": 5.07,
  "forecast_length_days": 365,
  "requested_metric": "1y_sector_roi"
})
OUTPUT: { "1y_sector_roi": [0.18, ..., 0.11], "Explanation": "..." }

STEP 3 - Run low growth scenario:
TOOL: simulate({
  "rbp": 1.69,
  "forecast_length_days": 365,
  "requested_metric": "1y_sector_roi"
})
OUTPUT: { "1y_sector_roi": [0.18, ..., 0.17], "Explanation": "..." }

STEP 4 - Get network capacity for high growth:
TOOL: simulate({
  "rbp": 5.07,
  "forecast_length_days": 365,
  "requested_metric": "network_QAP_EIB"
})
OUTPUT: { "network_QAP_EIB": [35.2, ..., 52.8], "Explanation": "..." }

STEP 5 - Get network capacity for low growth:
TOOL: simulate({
  "rbp": 1.69,
  "forecast_length_days": 365,
  "requested_metric": "network_QAP_EIB"
})
OUTPUT: { "network_QAP_EIB": [35.2, ..., 38.4], "Explanation": "..." }

RESPONSE:
"Comparison of high growth vs low growth scenarios (current: 3.38 EiB/day):

**High Growth (5.07 EiB/day), defined as 150% of the current raw byte power :**
- ROI: ...
- Network capacity: ...

**Low Growth (1.69 EiB/day), defined as 50% of the current raw byte power:**
- ROI: ...
- Network capacity: ...

..."
```

---

## Historical Trend Queries

### Example 10: Renewal Rate Evolution

```
PROMPT: "How has renewal rate evolved over the past year?"

TOOL: get_historical_data()

OUTPUT:
{
  "data": {
    "renewal_rate_averaged_over_previous_30days": 0.83,
    "renewal_rate": [0.75, 0.76, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.83, 0.83, ...],
    ...
  }
}

ACTION:
1. Parse the response
2. Extract data["renewal_rate"] array (Monday values over ~52 weeks)
3. Analyze trend: ...."
```

### Example 11: Network Power Trend

```
PROMPT: "Show me the network power trend over time"

TOOL: get_historical_data()

OUTPUT:
{
  "data": {
    "historical_raw_power_eib": [8.2, 9.5, 11.2, 13.4, 15.8, 18.3, 21.2, 24.5, 28.1, 32.0, 35.2],
    "historical_qa_power_eib": [18.5, 22.3, 26.8, 31.5, 36.8, 42.5, 48.9, 55.7, 62.8, 70.5, 78.9],
    ...
  }
}

ACTION:
1. Parse the response
2. Extract data["historical_raw_power_eib"] and data["historical_qa_power_eib"]
3. Calculate RBP growth: ...
4. Calculate QAP growth: ...
5. Calculate QAP/RBP ratio: ...
6. Respond: ...
"
```

---

## Mechanism Explanation Queries

### Example 12: FIL+ Economics Explanation

```
PROMPT: "How does FIL+ affect storage provider economics?"

TOOL: None initially

ACTION:
1. Provide conceptual explanation using formulas
2. Explain 10x multiplier mechanism
3. Offer to demonstrate with simulation

RESPONSE:
"FIL+ has a critical impact on storage provider economics through the quality multiplier:

**Quality Adjusted Power Formula:**
QAP = RBP × Multiplier

Where:
- Regular storage: Multiplier = 1x
- FIL+ verified deals: Multiplier = 10x

**Economic Impact:**

1. **Block Reward Probability**: Your chance of winning block rewards is proportional to:
   (Your QAP / Total Network QAP)

   Example: 32 GiB FIL+ sector = 320 GiB equivalent consensus power

2. **Competitive Advantage**: With 10x multiplier, you need 10x less physical storage to achieve
   the same election probability as regular storage.

3. **Pledge Requirements**: Scale with QAP - FIL+ sectors require 10x higher collateral, but this
   is typically justified by the 10x higher reward probability.

4. **Network-Level Effect**: As more providers adopt FIL+ (currently ~86%), the competitive advantage
   diminishes. You compete against other FIL+ providers, not just regular storage.

Would you like me to run a simulation comparing ROI with and without FIL+ deals to show the
numerical impact?"
```

### Example 13: Pledge Decrease Explanation

```
PROMPT: "Why do pledge requirements decrease over time?"

TOOL: None initially

ACTION:
1. Explain consensus pledge formula
2. Explain baseline growth mechanism
3. Optionally offer simulation demonstration

RESPONSE:
"Pledge requirements decrease over time due to the baseline function in the consensus pledge formula:

**Consensus Pledge Formula:**
ConsensusPledge = 30% × CirculatingSupply × (SectorQAP / max(Baseline, NetworkQAP))

**Why It Decreases:**

1. **Baseline Growth**: The baseline function grows exponentially (doubling annually):
   Baseline(t) = 2.5 EiB × e^(ln(2) × t/year)

2. **Denominator Effect**: As baseline grows faster than network QAP (when network is below baseline),
   the ratio (SectorQAP / Baseline) decreases over time.

3. **Capital Efficiency**: This design reduces capital barriers for new providers over time while
   maintaining network security through the 30% circulating supply target.

**Current State:**
- Network QAP: ~35 EiB
- Baseline: Growing exponentially
- Result: Pledge per unit of QAP gradually decreases

This is an intentional economic mechanism to balance network security with accessibility for
storage providers. Would you like me to show the projected pledge requirement trend over the
next year?"
```

---

## Complex Multi-Step Queries

### Example 14: Investment Decision Analysis

```
PROMPT: "I'm considering becoming a storage provider. What returns can I expect if I commit
100 TiB over the next 2 years, assuming I can get 80% FIL+ deals?"

STEP 1 - Get current network state:
TOOL: get_historical_data()
OUTPUT: { "data": { "filplus_rate_averaged_over_previous_30days": 0.86, ... } }
ACTION: Note current conditions

STEP 2 - Simulate ROI with user's FIL+ rate:
TOOL: simulate({
  "fpr": 0.80,
  "forecast_length_days": 730,
  "requested_metric": "1y_sector_roi"
})
OUTPUT: { "1y_sector_roi": [0.18, 0.177, ..., 0.16], "Explanation": "..." }

STEP 3 - Get pledge requirements:
TOOL: simulate({
  "fpr": 0.80,
  "forecast_length_days": 730,
  "requested_metric": "day_pledge_per_QAP"
})
OUTPUT: { "day_pledge_per_QAP": [0.25, 0.24, ..., 0.22], "Explanation": "..." }

STEP 4 - Get daily rewards:
TOOL: simulate({
  "fpr": 0.80,
  "forecast_length_days": 730,
  "requested_metric": "day_rewards_per_sector"
})
OUTPUT: { "day_rewards_per_sector": [0.0045, 0.0044, ..., 0.0041], "Explanation": "..." }

CALCULATIONS:
1. 100 TiB = 102,400 GiB = 3,200 sectors (32 GiB each)
2. With 80% FIL+ → 2,560 FIL+ sectors, 640 regular sectors
3. QAP = (2,560 × 320 GiB) + (640 × 32 GiB) = 819,200 + 20,480 = 839,680 GiB ≈ 820 TiB QAP
4. Initial pledge: 820 TiB × 0.25 FIL/TiB ≈ 205 FIL
5. Daily rewards: 3,200 sectors × 0.0045 FIL ≈ 14.4 FIL/day
6. Annual revenue (year 1): 14.4 × 365 ≈ 5,256 FIL
7. ROI (year 1): 5,256 / 205 ≈ 25.6% (but model shows 18% average)
8. Adjust for competition: ~18% ROI is more realistic

RESPONSE:
"Based on current network conditions and your parameters:

**Investment Setup:**
- Physical storage: 100 TiB (3,200 sectors of 32 GiB)
- FIL+ mix: 80% verified deals (you vs 86% network average)
- Quality-adjusted power: ~820 TiB QAP (with 10x multiplier on FIL+ portion)

**Capital Requirements:**
- Initial pledge: ~205 FIL (at current rates of 0.25 FIL/TiB QAP)
- Pledge decreases slightly over 2 years to ~0.22 FIL/TiB QAP

**Projected Returns (2-year horizon):**
- Year 1 ROI: ~18% (declining from 18% to 17% through the year)
- Year 2 ROI: ~16-17% (continued gradual decline)
- Daily rewards: ~14.4 FIL initially, declining to ~13.1 FIL by year 2

**Key Considerations:**
1. Your 80% FIL+ rate is slightly below network average (86%) - this may reduce competitive advantage
2. ROI assumes successful renewal of sectors at expiration
3. Pledge requirements decline over time, improving capital efficiency
4. Returns assume stable network onboarding (~3.38 EiB/day)

**Risks:**
- Increased network onboarding would dilute your reward share
- FIL price volatility affects FIL-denominated returns
- Operational costs (hardware, electricity) not included in ROI calculation

Overall, the economics show moderate returns (16-18% annually) under stable network conditions."
```

---

## Edge Cases and Clarifications

### Example 15: Ambiguous Time Horizon

```
PROMPT: "What will network rewards look like in the future?"

ACTION:
1. Identify missing time horizon
2. Ask for clarification before running simulation

RESPONSE:
"I can project network rewards for you. Could you specify your time horizon? For example:
- Short-term (next 3-6 months)
- Medium-term (next 1-2 years)
- Long-term (next 5-10 years)

Different timeframes have different levels of uncertainty - shorter forecasts are more reliable."
```


### Example 16: Multiple Metrics Request

```
PROMPT: "Show me how the network will evolve - power, supply, and rewards"

STEP 1 - Clarify time horizon (assume 1 year if not specified):
ACTION: Determine forecast_length_days = 365

STEP 2 - Run simulation for network power:
TOOL: simulate({
  "forecast_length_days": 365,
  "requested_metric": "network_QAP_EIB"
})

STEP 3 - Run simulation for circulating supply:
TOOL: simulate({
  "forecast_length_days": 365,
  "requested_metric": "circ_supply"
})

STEP 4 - Run simulation for daily rewards:
TOOL: simulate({
  "forecast_length_days": 365,
  "requested_metric": "day_network_reward"
})

ACTION: Present all three projections with interpretation

RESPONSE:
"Network evolution over the next year (under current conditions):

**Network Power (QAP):**
- Current: 35.2 EiB
- 1-year projection: 42.1 EiB
- Growth: +19.6%

**Circulating Supply:**
- Current: 580.25M FIL
- 1-year projection: 606.5M FIL
- Growth: +4.5% 

**Daily Network Rewards:**
- Current: 123,456 FIL/day
- 1-year projection: 118,900 FIL/day
- Change: -3.7% 

..."
```

---

## Summary

These examples demonstrate:
1. Proper tool selection based on query type
2. Correct parameter extraction and validation
3. Multi-step workflows for complex scenarios
4. Appropriate response construction with economic interpretation
5. Edge case handling and user clarification
6. Integration of multiple tool calls for comprehensive analysis
