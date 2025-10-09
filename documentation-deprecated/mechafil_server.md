# MechaFil Server: Web API for Filecoin Economic Simulations

## Overview

MechaFil Server is a production-ready FastAPI web service that provides HTTP endpoints for running Filecoin economic forecasts. It wraps the high-performance **mechafil-jax** simulation engine, making sophisticated economic modeling accessible through simple web requests.

### Key Features

- **Unified API Structure**: All endpoints now return standardized response formats using dataclass containers
- **Monday Downsampling**: Results automatically downsampled to weekly values for efficient data transfer
- **Field Filtering**: Request only specific metrics using the `output` parameter
- **Consistent Response Format**:
  - Simulations: `{"input": {...}, "simulation_output": {...}}`
  - Historical data: `{"data": {...}}`
- **Simplified Endpoints**: Single `/simulate` endpoint (removed `/simulate/full`), single `/historical-data` endpoint

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MechaFil Server                          │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Web Layer                                         │
│  ├── /health              - Health checks                  │
│  ├── /                    - Documentation redirect         │
│  ├── /historical-data     - Monday-downsampled data        │
│  └── /simulate            - Monday-downsampled forecasts   │
├─────────────────────────────────────────────────────────────┤
│  Results Processing Layer (results.py)                      │
│  ├── SimulationResults    - Wraps simulation outputs       │
│  ├── FetchDataResults     - Wraps historical data          │
│  ├── Monday downsampling  - Weekly data reduction          │
│  └── Field filtering      - Output selection               │
├─────────────────────────────────────────────────────────────┤
│  Data Processing Layer (data.py)                            │
│  ├── Historical data fetching and caching                  │
│  ├── Parameter validation and transformation               │
│  ├── Data trimming for simulation periods                  │
│  └── Background data refresh scheduling                    │
├─────────────────────────────────────────────────────────────┤
│  MechaFil-JAX Integration                                   │
│  ├── Direct simulation engine calls                        │
│  ├── JAX array parameter conversion                        │
│  └── Result post-processing                                │
├─────────────────────────────────────────────────────────────┤
│  External Dependencies                                      │
│  ├── Spacescope API (via pystarboard)                     │
│  ├── DiskCache for data persistence                        │
│  └── JAX for high-performance computing                    │
└─────────────────────────────────────────────────────────────┘
```

## API Response Format

All API endpoints now return structured responses using standardized container classes:

### **Simulation Response (`/simulate`)**

Returns a `SimulationResults` object serialized to JSON with two main sections:

```json
{
  "input": {
    "current date": "2025-01-01",
    "forecast_length_days": 365,
    "raw_byte_power": 3.38,
    "renewal_rate": 0.83,
    "filplus_rate": 0.86
  },
  "simulation_output": {
    "available_supply": [580250000.12, 582100000.45, ...],
    "network_RBP_EIB": [15.2, 15.4, 15.6, ...],
    "1y_sector_roi": [0.18, 0.17, 0.16, ...],
    // ... all other simulation metrics
  }
}
```

- **`input`**: Metadata about the simulation run (dates, parameters used)
- **`simulation_output`**: Dictionary mapping metric names to time series arrays (Monday values)

### **Historical Data Response (`/historical-data`)**

Returns a `FetchDataResults` object with a single top-level `data` dictionary:

```json
{
  "data": {
    // 30-day smoothed metrics
    "raw_byte_power_averaged_over_previous_30days": 3.38,
    "renewal_rate_averaged_over_previous_30days": 0.83,
    "filplus_rate_averaged_over_previous_30days": 0.86,

    // Historical time series (Monday values)
    "raw_byte_power": [2.1, 2.3, 2.5, ...],
    "renewal_rate": [0.75, 0.78, 0.82, ...],
    "filplus_rate": [0.80, 0.83, 0.85, ...],

    // Offline model data (scalars and arrays)
    "rb_power_zero": 1234.56,
    "qa_power_zero": 2345.67,
    "circ_supply_zero": 123456789.12,
    "locked_fil_zero": 45678901.23,
    "historical_raw_power_eib": [12.5, 13.1, ...],
    // ... all other offline data fields
  }
}
```

## Core Components

### 1. **Main Application (`main.py`)**

The FastAPI application entry point that handles:

#### **Application Lifecycle**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load historical data and start scheduler
    loaded_data = Data()
    loaded_data.load_historical_data()
    data_scheduler = DataRefreshScheduler(loaded_data.refresh_historical_data)
    data_scheduler.start()
    
    yield
    
    # Shutdown: Clean up resources
    await data_scheduler.stop_async()
```

#### **Key Endpoints**

**Health and Information:**
- `GET /health` - Service health check with JAX backend information
- `GET /` - Root endpoint redirecting to documentation (Sphinx docs if built, otherwise Swagger UI)

**Historical Data:**
- `GET /historical-data` - Monday-downsampled historical metrics
  - Returns: `{"data": {...}}` with smoothed metrics, time series, and offline data

**Simulations:**
- `POST /simulate` - Run forecasts with Monday-downsampled results
  - Returns: `{"input": {...}, "simulation_output": {...}}`
  - Supports `output` parameter for field filtering

### 2. **Data Management (`data.py`)**

Handles all data operations and integration with mechafil-jax:

#### **Historical Data Pipeline**
```python
def get_offline_data(self, start_date, current_date, end_date):
    # 1. Fetch raw blockchain data via Spacescope
    offline_data = get_simulation_data(bearer_or_file, start_date, current_date, end_date)
    
    # 2. Process historical metrics
    _, hist_rbp = get_historical_daily_onboarded_power(...)
    _, hist_rr = get_historical_renewal_rate(...)
    _, hist_fpr = get_historical_filplus_rate(...)
    
    # 3. Compute smoothed defaults for API
    smoothed_rbp = float(np.median(hist_rbp[-30:]))  # 30-day median
    smoothed_rr = float(np.median(hist_rr[-30:]))
    smoothed_fpr = float(np.median(hist_fpr[-30:]))
```

#### **Intelligent Caching**
- Uses `diskcache` for persistent data storage
- Cache keys include date ranges to ensure data freshness
- Automatic cache invalidation during daily refreshes
- Fallback retry logic if data fetching fails

#### **Data Trimming for Simulations**
```python
def trim_data_for_simulation(self, forecast_length):
    # Expire vectors: forecast period only
    new_data['rb_known_scheduled_expire_vec'] = hist_data['rb_known_scheduled_expire_vec'][:forecast_length]
    new_data['qa_known_scheduled_expire_vec'] = hist_data['qa_known_scheduled_expire_vec'][:forecast_length]
    
    # Pledge release: historical + forecast period
    pledge_release_length = historical_days + forecast_length
    new_data['known_scheduled_pledge_release_full_vec'] = hist_data['known_scheduled_pledge_release_full_vec'][:pledge_release_length]
```

### 3. **Results Containers (`results.py`)**

Dataclasses that wrap and process simulation/historical data results:

#### **SimulationResults**
Container for simulation output with methods for:
- `from_raw()`: Convert raw mechafil-jax output to structured format
- `downsample_mondays()`: Filter time series to Monday values only
- `filter_fields()`: Return only requested output fields
- `to_dict()`: Serialize to JSON with `input` and `simulation_output` sections

**Structure:**
```python
@dataclass
class SimulationResults:
    input_data: Dict[str, Any]  # Simulation metadata
    simulation_output: Dict[str, Union[List[float], float, str]]  # Metrics
```

#### **FetchDataResults**
Container for historical data with methods for:
- `from_raw()`: Combine historical arrays, offline data, and smoothed metrics
- `downsample_mondays()`: Filter arrays to Monday values
- `filter_fields()`: Return subset of data fields
- `to_dict()`: Serialize to JSON with single `data` section

**Structure:**
```python
@dataclass
class FetchDataResults:
    data: Dict[str, Union[List[float], float, str]]  # All historical data
```

### 4. **Request/Response Models (`models.py`)**

Pydantic models that define the API interface:

#### **Simulation Request Model**
```python
class SimulationRequest(BaseModel):
    rbp: Optional[Union[float, List[float]]] = None              # Raw byte power (PIB/day)
    rr: Optional[Union[float, List[float]]] = None               # Renewal rate (0..1)
    fpr: Optional[Union[float, List[float]]] = None              # FIL+ rate (0..1)
    lock_target: Optional[Union[float, List[float]]] = None      # Target lock ratio
    forecast_length_days: Optional[int] = None                   # Forecast period
    sector_duration_days: Optional[int] = None                   # Average sector duration
    output: Optional[Union[str, List[str]]] = None               # Field filtering
```

**Key Features:**
- All parameters are optional with intelligent defaults
- Supports both constant values and time-varying arrays
- Built-in validation for output field names
- Example payloads for API documentation

### 5. **Configuration Management (`config.py`)**

Centralized settings and environment variable handling:

```python
class Settings:
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Data source authentication
    SPACESCOPE_TOKEN: Optional[str] = os.getenv("SPACESCOPE_TOKEN")
    SPACESCOPE_AUTH_FILE: str = os.getenv("SPACESCOPE_AUTH_FILE")
    
    # Simulation defaults
    STARTUP_DATE: date = date(2025, 1, 1)
    WINDOW_DAYS: int = 10 * 365  # 10-year default forecast
    SECTOR_DURATION_DAYS: int = 540
    LOCK_TARGET: float = 0.3
    
    # Data refresh scheduling
    RELOAD_TRIGGER: str = os.getenv("RELOAD_TRIGGER", "02:00")  # Daily at 2 AM UTC
    RELOAD_TEST_MODE: bool = os.getenv("RELOAD_TEST_MODE", "false").lower() == "true"
```

### 6. **Background Scheduler (`scheduler.py`)**

Automated daily data refresh system:

#### **Scheduling Logic**
```python
def seconds_until_next_refresh(self):
    # Test mode: refresh every 2 minutes
    if settings.RELOAD_TEST_MODE:
        return 120.0
        
    # Production: daily refresh at configured time
    now = datetime.now()
    refresh_time = self.parse_time_string(settings.RELOAD_TRIGGER)
    today_refresh = datetime.combine(now.date(), refresh_time)
    
    # If time has passed today, schedule for tomorrow
    if today_refresh <= now:
        today_refresh = today_refresh.replace(day=today_refresh.day + 1)
```

**Features:**
- Configurable daily refresh time (default: 02:00 UTC)
- Test mode for development (2-minute intervals)
- Graceful error handling - server continues if refresh fails
- Proper asyncio task management

## Request Flow and Processing

### 1. **API Request Processing**

When a simulation request arrives:

```python
@app.post("/simulate")
async def simulate(req: SimulationRequest):
    # 1. Load historical data
    hist_data = loaded_data.get_historical_data()

    # 2. Apply defaults for missing parameters
    forecast_len = req.forecast_length_days or settings.WINDOW_DAYS
    rbp_value = req.rbp or hist_data["smoothed_rbp"]
    rr_value = req.rr or hist_data["smoothed_rr"]
    fpr_value = req.fpr or hist_data["smoothed_fpr"]

    # 3. Convert to JAX arrays
    rbp = jnp.ones(forecast_len) * rbp_value if isinstance(rbp_value, float) else jnp.array(rbp_value)
    rr = jnp.ones(forecast_len) * rr_value if isinstance(rr_value, float) else jnp.array(rr_value)
    fpr = jnp.ones(forecast_len) * fpr_value if isinstance(fpr_value, float) else jnp.array(fpr_value)

    # 4. Call mechafil-jax simulation
    raw_results = mechafil_sim.run_sim(
        rbp, rr, fpr, lock_target, start_date, current_date,
        forecast_len, sector_duration_days, simulation_offline_data,
        use_available_supply=False
    )

    # 5. Wrap results in SimulationResults container
    results = SimulationResults.from_raw(
        raw_results, start_date, current_date, forecast_len,
        smoothed_rbp, smoothed_rr, smoothed_fpr
    )

    # 6. Downsample to Mondays
    results = results.downsample_mondays(start_date)

    # 7. Filter output if requested
    if req.output is not None:
        results = results.filter_fields(req.output)

    # 8. Return as dict with 'input' and 'simulation_output' keys
    return results.to_dict()
```

### 2. **Parameter Handling**

The server provides intelligent parameter processing:

**Default Value Resolution:**
1. Use explicit request parameter if provided
2. Fall back to smoothed historical data (30-day median)
3. Use configuration defaults as last resort

**Array Conversion:**
- Single values → Constant JAX arrays: `jnp.ones(length) * value`
- Python lists → JAX arrays: `jnp.array(list)`
- Time-varying parameters supported for all inputs

**Validation:**
- Output field names validated against actual simulation outputs
- Parameter ranges checked (e.g., renewal rates between 0 and 1)
- Array lengths must match forecast length

### 3. **Result Processing**

**Single Endpoint with Optional Downsampling (`/simulate`):**
- Returns results downsampled to Monday values for efficient data transfer
- Complete daily time series for all output variables
- Used for analysis and visualization applications

**Monday Downsampling Logic:**
```python
def select_mondays(data_array, start_date):
    """Select results that fall on Mondays for bandwidth efficiency."""
    mondays = []
    for i, val in enumerate(data_array):
        current_date = start_date + timedelta(days=i)
        if current_date.weekday() == 0:  # Monday
            mondays.append(round(float(val), 2))
    return mondays
```

**Field Filtering:**
```python
# Example: Request specific fields only
{
    "forecast_length_days": 365,
    "output": ["available_supply", "network_RBP_EIB", "1y_sector_roi"]
}
```

**Output Structure:**
The API returns a standardized response with two main sections:
```json
{
  "input": {
    "current date": "2025-01-01",
    "forecast_length_days": 365,
    "raw_byte_power": 3.38,
    "renewal_rate": 0.83,
    "filplus_rate": 0.86
  },
  "simulation_output": {
    "available_supply": [580250000.12, 582100000.45, ...],
    "network_RBP_EIB": [15.2, 15.4, 15.6, ...],
    "1y_sector_roi": [0.18, 0.17, 0.16, ...],
    // ... other output fields
  }
}
```

## Data Flow and Caching Strategy

### 1. **Historical Data Lifecycle**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Spacescope    │    │   Data Cache    │    │   API Server    │
│   API Source    │────▶│  (DiskCache)    │────▶│   Endpoints     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Daily Refresh   │    │ Cache Warmup    │    │ Real-time       │
│ 02:00 UTC       │    │ on Startup      │    │ Simulations     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. **Cache Management**

**Cache Key Structure:**
```python
cache_key = f"offline_data_{start_date}{current_date}{end_date}"
```

**Cache Operations:**
- **Startup:** Check cache, load if available, fetch if missing
- **Daily Refresh:** Clear old entries, fetch fresh data, update cache
- **Retry Logic:** Fall back to previous days if current data unavailable

### 3. **Performance Optimizations**

**JAX Configuration:**
```python
from jax import config
config.update("jax_enable_x64", True)  # Enable 64-bit precision
```

**Result Formatting:**
- Round floating-point numbers to 2 decimal places for bandwidth
- Convert JAX arrays to Python lists for JSON serialization
- Lazy loading of historical data on first request

## Testing and Validation

### 1. **Mathematical Accuracy Testing**

The server includes comprehensive tests that ensure API responses are **mathematically identical** to offline simulations:

```python
def test_simulation_accuracy(api_client, offline_simulation_scripts):
    # Call API endpoint
    api_response = api_client.post("/simulate", json={"lock_target": 0.1})
    api_data = api_response.json()

    # Run equivalent offline simulation
    offline_result = run_offline_simulation(lock_target=0.1)

    # Extract simulation_output from new response format
    api_simulation_data = api_data["simulation_output"]

    # Assert mathematical equality with tolerance
    compare_results(api_simulation_data, offline_result, tolerance=1e-10)
```

### 2. **Test Categories**

**API Validation Tests:**
- Default simulation parameters vs offline scripts
- Custom parameter scenarios (lock targets, forecast lengths)
- Historical data endpoint accuracy
- Multiple parameter combinations

**Endpoint Functionality Tests:**
- Request/response structure validation
- Error handling and parameter validation
- Health checks and service monitoring

**Integration Tests:**
- End-to-end workflow testing
- Data refresh and caching behavior
- Background scheduler functionality

## Production Deployment

### 1. **Environment Configuration**

**Required Environment Variables:**
```bash
# Spacescope authentication (choose one)
SPACESCOPE_TOKEN=Bearer YOUR_TOKEN_HERE
# or
SPACESCOPE_AUTH_FILE=/path/to/auth.json

# Optional configuration
HOST=0.0.0.0
PORT=8000
RELOAD_TRIGGER=02:00  # Daily refresh time (UTC)
LOG_LEVEL=INFO
CORS_ORIGINS=*
```

### 2. **Installation and Startup**

**Using Poetry (recommended):**
```bash
cd mechafil-server
poetry install
poetry run mechafil-server
```

**Direct Uvicorn:**
```bash
poetry run uvicorn mechafil_server.main:app --host 0.0.0.0 --port 8000
```

### 3. **Production Features**

**Reliability:**
- Graceful error handling for data source failures
- Retry logic with exponential backoff
- Health check endpoints for monitoring
- Comprehensive logging with configurable levels

**Performance:**
- JAX JIT compilation for fast simulations
- Intelligent caching reduces API response times
- Background data processing doesn't block requests
- CORS support for web application integration

**Security:**
- Environment variable configuration for sensitive data
- Input validation and sanitization
- No hardcoded credentials or tokens

## API Usage Examples

### 1. **Basic Simulation**

```bash
# Minimal request using all defaults (returns Monday-downsampled results)
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Response structure:**
```json
{
  "input": {
    "current date": "2025-01-01",
    "forecast_length_days": 3650,
    "raw_byte_power": 3.38,
    "renewal_rate": 0.83,
    "filplus_rate": 0.86
  },
  "simulation_output": {
    "available_supply": [580250000.12, 582100000.45, ...],
    "network_RBP_EIB": [15.2, 15.4, ...],
    // ... all other metrics
  }
}
```

### 2. **Custom Parameters**

```bash
# 5-year forecast with custom parameters
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "rbp": 4.0,
    "rr": 0.85,
    "fpr": 0.9,
    "lock_target": 0.25,
    "forecast_length_days": 1825,
    "sector_duration_days": 360
  }'
```

### 3. **Time-Varying Parameters**

```bash
# Parameters that change over time
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "rbp": [3.0, 3.5, 4.0, 4.5, 5.0],
    "rr": [0.8, 0.82, 0.85, 0.87, 0.9],
    "forecast_length_days": 5
  }'
```

### 4. **Selective Output Fields**

```bash
# Request only specific result fields
curl -X POST http://localhost:8000/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "forecast_length_days": 365,
    "output": ["available_supply", "1y_sector_roi", "day_network_reward"]
  }'
```

**Filtered response:**
```json
{
  "input": {
    "current date": "2025-01-01",
    "forecast_length_days": 365,
    "raw_byte_power": 3.38,
    "renewal_rate": 0.83,
    "filplus_rate": 0.86
  },
  "simulation_output": {
    "available_supply": [580250000.12, 582100000.45, ...],
    "1y_sector_roi": [0.18, 0.17, 0.16, ...],
    "day_network_reward": [123456.78, 123500.12, ...]
  }
}
```

## Monitoring and Maintenance

### 1. **Health Monitoring**

**Health Check Endpoint:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "jax_backend": "cpu"
}
```

### 2. **Data Freshness**

The server automatically maintains current data through:
- Daily refresh at configurable time (default: 02:00 UTC)
- Automatic retry with previous dates if current data unavailable
- Cache management to prevent stale data usage
- Logging of all data operations for debugging

### 3. **Error Handling**

**Common Issues and Solutions:**
- **Missing Spacescope credentials:** Configure `SPACESCOPE_TOKEN` or `SPACESCOPE_AUTH_FILE`
- **Data fetch failures:** Server continues with cached data, logs errors
- **JAX initialization issues:** Check JAX installation and backend configuration
- **Memory issues:** Reduce `WINDOW_DAYS` or forecast lengths for large simulations

The MechaFil Server provides a robust, production-ready interface to the sophisticated mechafil-jax simulation engine, making Filecoin economic modeling accessible to a wide range of applications and users while maintaining mathematical accuracy and performance.