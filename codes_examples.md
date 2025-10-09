# MechaFil MCP Prompt Examples

Each scenario pairs a user-facing prompt with the MCP tool invocation and the follow-up work the assistant should handle after the call.

## 1. Current Network Snapshot
- **Prompt:** "Give me the latest Filecoin network fundamentals before we plan anything."
- **Tool call:**
  ```json
  {"tool_name": "get_historical_data", "arguments": {}}
  ```
- **LLM action:** Parse the returned JSON, extract the 30-day averaged `raw_byte_power`, `renewal_rate`, and `filplus_rate`, plus any other salient metrics, then write a concise status summary highlighting recent trends and default values users can reuse.

## 2. One-Year ROI Forecast
- **Prompt:** "What annual ROI should storage providers expect over the next year?"
- **Tool call:**
  ```json
  {
    "tool_name": "simulate",
    "arguments": {
      "forecast_length_days": 365,
      "requested_metric": "1y_sector_roi"
    }
  }
  ```
- **LLM action:** Describe how ROI moves across the forecast, call out starting/ending values, and interpret the implications (e.g., rising vs. declining profitability).

## 3. Available Supply Outlook (2 Years)
- **Prompt:** "Project Filecoin available supply over the next two years."
- **Tool call:**
  ```json
  {
    "tool_name": "simulate",
    "arguments": {
      "forecast_length_days": 730,
      "requested_metric": "available_supply"
    }
  }
  ```
- **LLM action:** Summarize the supply trajectory, note the magnitude of change, and mention any inflection points or steady trends that emerge.

## 4. Aggressive Onboarding Scenario
- **Prompt:** "Assume onboarding jumps to 5 EiB/day—how does network power evolve over the next year?"
- **Tool call:**
  ```json
  {
    "tool_name": "simulate",
    "arguments": {
      "forecast_length_days": 365,
      "rbp": 5.0,
      "requested_metric": "network_RBP_EIB"
    }
  }
  ```
- **LLM action:** Compare the projected raw byte power path against the baseline explanation in the response, highlighting acceleration and any capacity milestones.

## 5. Collateral Planning for the Next Six Months
- **Prompt:** "Estimate pledge collateral requirements providers should plan for over the next six months."
- **Tool call:**
  ```json
  {
    "tool_name": "simulate",
    "arguments": {
      "forecast_length_days": 180,
      "requested_metric": "day_pledge_per_QAP"
    }
  }
  ```
- **LLM action:** Report the pledge-per-QAP trend, emphasizing peak and trough requirements and suggesting operational considerations for providers.

## 6. Improving Renewal Strategy
- **Prompt:** "Model a scenario where renewal rates climb from 75% to 90% over the next year and tell me the impact on ROI."
- **Tool call:**
  ```json
  {
    "tool_name": "simulate",
    "arguments": {
      "forecast_length_days": 365,
      "rr": [0.75, 0.8, 0.85, 0.9],
      "requested_metric": "1y_sector_roi"
    }
  }
  ```
- **LLM action:** Interpret how the staged renewal improvements affect ROI, connect the explanation string to the custom inputs, and advise on what the changes mean for provider strategy.

## 7. Short-Term Reward Outlook
- **Prompt:** "Show me expected daily network rewards for the next quarter."
- **Tool call:**
  ```json
  {
    "tool_name": "simulate",
    "arguments": {
      "forecast_length_days": 90,
      "requested_metric": "day_network_reward"
    }
  }
  ```
- **LLM action:** Summarize the reward timeline, identify any notable short-term shifts, and translate values into actionable guidance for revenue planning.
