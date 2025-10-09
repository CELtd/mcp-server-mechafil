# MechaFil-JAX: Filecoin Economic Model Simulator

## Overview

MechaFil-JAX is a high-performance economic model simulator for the Filecoin network, implemented using JAX for accelerated numerical computations. The simulator models the complex economic dynamics of the Filecoin protocol, including storage power growth, token minting mechanisms, supply dynamics, and network incentives.

## What Does This Code Do?

The MechaFil-JAX simulator provides a comprehensive model of the Filecoin network's economic behavior by simulating key protocol components:

### 1. **Storage Power Dynamics** (`power.py`)
- **Raw Byte Power (RBP)**: The actual storage capacity committed to the network
- **Quality Adjusted Power (QAP)**: Storage power adjusted for deal quality and FIL+ multipliers
- **Power Onboarding**: Daily addition of new storage capacity
- **Power Renewals**: Extension of existing storage commitments
- **Power Expirations**: Natural expiry of storage commitments based on sector duration

### 2. **Token Minting System** (`minting.py`)
- **Simple Minting**: Time-based token release following exponential decay (30% of storage mining allocation)
- **Baseline Minting**: Storage growth-based rewards tied to network baseline power (70% of storage mining allocation)
- **Network Baseline**: Exponentially growing storage target that determines baseline reward release
- **Reward Calculations**: Daily FIL token rewards distributed to storage providers

### 3. **Token Supply Management** (`supply.py`)
- **Circulating Supply**: FIL tokens available in the market
- **Available Supply**: Circulating supply minus locked tokens
- **Locked Tokens**: FIL locked as initial pledge collateral and block rewards
- **Gas Burning**: FIL tokens permanently removed through network fees
- **Pledge Mechanics**: Dynamic collateral requirements based on network conditions

### 4. **Vesting Schedules** (`vesting.py`)
- **Protocol Lab Allocation**: 15% linear vesting over 6 years
- **Foundation Allocation**: 5% linear vesting over 6 years
- **Investor Allocations**: 10% with various vesting schedules (0 days to 6 years)
- **Mining Reserve**: 15% allocation for future protocol development

### 5. **Economic Incentives** (`locking.py`)
- **Initial Pledge**: Collateral required when onboarding storage
- **Block Reward Locking**: Portion of mining rewards locked as additional collateral
- **Pledge Release**: Return of collateral when storage commitments expire
- **FIP-81 Implementation**: Gamma trajectory for smooth pledge transitions

## Key Features

### **JAX-Powered Performance**
- Utilizes JAX's JIT compilation for high-speed numerical computations
- Vectorized operations for efficient batch processing
- GPU acceleration support for large-scale simulations

### **Historical Data Integration**
- Loads real Filecoin network data via Spacescope API
- Seamlessly combines historical trends with forward projections
- Validates model accuracy against actual network behavior

### **Flexible Forecasting**
- Time-varying parameters (renewal rates, FIL+ adoption, lock targets)
- Configurable simulation periods and granularity
- Multiple baseline scenarios and sensitivity analysis

### **Protocol Compliance**
- Implements actual Filecoin economic mechanisms
- Follows official specifications for minting and pledge calculations
- Incorporates recent protocol upgrades (FIP-81)

## Use Cases

### **Network Analysis**
- Long-term economic sustainability assessment
- Storage growth impact on token supply and rewards
- Network capacity planning and resource allocation

### **Policy Modeling**
- Protocol parameter optimization
- Economic mechanism design and testing
- Impact assessment of proposed protocol changes

### **Market Intelligence**
- Token supply forecasting for market participants
- Mining profitability analysis under various scenarios
- Risk assessment for storage providers and investors

### **Research and Development**
- Academic research on blockchain economics
- Mechanism design validation and improvement
- Economic security analysis

## Architecture

The simulator follows a modular architecture where each component handles specific aspects of the Filecoin economy:

```
sim.py (Main Orchestrator)
├── power.py (Storage Power Calculations)
├── minting.py (Token Reward Mechanisms)
├── supply.py (Circulating Supply Dynamics)
├── vesting.py (Token Release Schedules)
├── locking.py (Pledge and Collateral Logic)
└── data.py (Historical Data Integration)
```

This design enables independent testing and validation of each economic component while maintaining system-wide consistency through the main simulation orchestrator.

## Technical Innovation

MechaFil-JAX represents a significant advancement in blockchain economic modeling by:

1. **Combining Historical and Predictive Modeling**: Seamlessly integrating real network data with forward-looking simulations
2. **High-Performance Computing**: Leveraging JAX for orders-of-magnitude faster computation than traditional approaches
3. **Comprehensive Protocol Modeling**: Capturing the full complexity of Filecoin's economic mechanisms in a single coherent model
4. **Research-Grade Accuracy**: Providing the precision and flexibility required for serious economic analysis and policy research

The simulator serves as both a practical tool for network participants and a research platform for advancing the understanding of decentralized storage economics.