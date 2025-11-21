# MechaFil Deployment Guide

Complete guide for deploying the MechaFil API server and MCP server to Fly.io with serverless architecture.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Part 1: Deploying the MechaFil API Server](#part-1-deploying-the-mechafil-api-server)
4. [Part 2: Deploying the MCP Server](#part-2-deploying-the-mcp-server)
5. [Understanding the Components](#understanding-the-components)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Cost Breakdown](#cost-breakdown)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

The deployment consists of two independent serverless applications on Fly.io:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Claude.ai Web                           │
│                    (Custom Connector)                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ HTTPS
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│           MCP Server (mechafil-mcp-server.fly.dev)              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FastMCP HTTP Server (Port 8080)                          │  │
│  │  - fetch_context() tool                                   │  │
│  │  - simulate() tool                                        │  │
│  │  - get_historical_data() tool                             │  │
│  └─────────────────────┬─────────────────────────────────────┘  │
│                        │                                         │
│  Fly.io Machine:      │ Makes HTTP calls                        │
│  - Auto-start: true   │                                         │
│  - Auto-stop: true    │                                         │
│  - Min machines: 0    │                                         │
│  - 512MB RAM, 1 CPU   │                                         │
└────────────────────────┼─────────────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           MechaFil API (mechafil-api.fly.dev)                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FastAPI Service (Port 8000)                              │  │
│  │  - /health - Health check                                 │  │
│  │  - /historical-data - Get cached data                     │  │
│  │  - /simulate - Run Filecoin simulations                   │  │
│  │  - /admin/update-cache - Trigger cache refresh            │  │
│  └─────────────────────┬─────────────────────────────────────┘  │
│                        │                                         │
│                        ▼                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Persistent Volume: /data/shared-cache (3GB)             │  │
│  │  - DiskCache storage                                      │  │
│  │  - Survives machine restarts                              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Fly.io Machine:                                                 │
│  - Auto-start: true                                              │
│  - Auto-stop: true                                               │
│  - Min machines: 0                                               │
│  - 2GB RAM, 2 CPUs                                               │
│  - Volume attached: shared_cache (3GB)                           │
└───────────────────────────────────────────────────────────────┬─┘
                                                                  │
                                                                  │ Fetches data
                                                                  ▼
                                                          Spacescope API
                                                          (Filecoin data)
```

### Key Architectural Decisions

1. **Two Separate Apps**: MCP server and API server are independent deployments
   - MCP server is a lightweight proxy/tool provider for Claude.ai
   - API server handles heavy computation and data caching

2. **True Serverless**: Both machines scale to zero when idle
   - No health checks (allows faster auto-stop)
   - Auto-start on incoming requests
   - Cost-effective: only pay for actual usage

3. **Persistent Cache**: API server uses a Fly.io volume
   - Stores historical data from Spacescope API
   - Survives machine stops/restarts
   - Updated via admin endpoint (can be triggered by GitHub Actions)

4. **Lazy Loading**: API server loads cache on first request, not at startup
   - Faster cold starts (~15 seconds)
   - Reduced memory footprint during idle periods

---

## Prerequisites

### Required Tools

1. **Fly CLI**: Install and authenticate
   ```bash
   # Install
   curl -L https://fly.io/install.sh | sh

   # Add to PATH (add to ~/.bashrc or ~/.zshrc)
   export PATH="$HOME/.fly/bin:$PATH"

   # Login
   flyctl auth login

   # Verify
   flyctl auth whoami
   ```

2. **Docker**: Required for building images
   ```bash
   docker --version
   ```

3. **Spacescope API Token**: Required for fetching Filecoin data
   - Get your token from Spacescope
   - Format: `Bearer ghp_xxxxxxxxxxxxx`

### Important Configuration Notes

**Critical: Token Format**

Your Spacescope token must NOT have quotes around it:

```bash
# ❌ Wrong (causes API failures)
SPACESCOPE_TOKEN="Bearer ghp_..."

# ✅ Correct
SPACESCOPE_TOKEN=Bearer ghp_...
```

---

## Part 1: Deploying the MechaFil API Server

The MechaFil API server is the core computational service that runs Filecoin economic simulations.

### Step 1: Create the Fly.io App

Navigate to the mechafil-server directory and create the app:

```bash
cd /path/to/mechafil/programs/mechafil-server

# Create app
flyctl apps create mechafil-api
```

**What this does:**
- Registers a new app named `mechafil-api` in your Fly.io account
- Reserves the URL `mechafil-api.fly.dev`
- No machines or resources are created yet

### Step 2: Create Persistent Volume

The API server needs persistent storage for caching Spacescope data:

```bash
# Create 3GB volume in Frankfurt region
flyctl volumes create shared_cache --region fra --size 3 --app mechafil-api
```

**Options explained:**
- `shared_cache`: Volume name (must match `fly.toml` mount configuration)
- `--region fra`: Frankfurt data center (choose closest to your users)
- `--size 3`: 3GB capacity (~$0.45/month, enough for 100-500MB cache)
- `--app mechafil-api`: Associates volume with the app

**Important volume constraints:**
- Volumes can only be attached to ONE machine at a time
- This is why we use a single-machine architecture
- Volume data persists even when the machine stops

### Step 3: Set Secret Environment Variables

Set the Spacescope API token as a secret:

```bash
# Set secret (replace YOUR_TOKEN_HERE with actual token)
flyctl secrets set SPACESCOPE_TOKEN='Bearer YOUR_TOKEN_HERE' --app mechafil-api
```

**Why use secrets:**
- Encrypted at rest and in transit
- Not visible in logs or `fly.toml`
- Automatically available as environment variables in the app

**Verify secrets are set:**
```bash
flyctl secrets list --app mechafil-api
```

### Step 4: Review fly.toml Configuration

The `fly.toml` file in `/programs/mechafil-server/` configures the deployment:

```toml
app = "mechafil-api"
primary_region = "fra"

[build]
  dockerfile = "docker/Dockerfile"

[env]
  USE_SHARED_CACHE = "true"
  SHARED_CACHE_DIR = "/data/shared-cache"
  HOST = "0.0.0.0"
  PORT = "8000"

[mounts]
  source = "shared_cache"
  destination = "/data/shared-cache"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "stop"  # Scale to zero when idle
  auto_start_machines = true   # Start on incoming request
  min_machines_running = 0     # True serverless

  # No health checks - allows faster auto-stop when idle

[[vm]]
  memory = "2gb"
  cpu_kind = "shared"
  cpus = 2
```

**Key settings:**

- **`auto_stop_machines = "stop"`**: Machine stops after ~2 minutes of inactivity
- **`auto_start_machines = true`**: Wakes up automatically on HTTP request
- **`min_machines_running = 0`**: No machines running when idle (serverless)
- **No health checks**: Removed to allow faster auto-stop (health checks keep machines awake)
- **Volume mount**: `/data/shared-cache` persists across restarts

### Step 5: Deploy the API Server

Deploy the application:

```bash
cd /path/to/mechafil/programs/mechafil-server

# Deploy (builds Docker image and creates machine)
flyctl deploy --app mechafil-api

# Monitor deployment
flyctl logs --app mechafil-api
```

**What happens during deployment:**

1. **Build Phase** (~2-3 minutes):
   - Dockerfile at `docker/Dockerfile` is built
   - Installs Python 3.11, Poetry, JAX, dependencies
   - Image size: ~1-2GB
   - Built remotely on Fly.io builders

2. **Deploy Phase** (~1 minute):
   - Creates a new machine with 2GB RAM, 2 CPUs
   - Attaches the `shared_cache` volume to `/data/shared-cache`
   - Starts the FastAPI application
   - Machine becomes available at `mechafil-api.fly.dev`

3. **Startup** (~15 seconds cold start):
   - JAX initializes (CPU backend)
   - FastAPI starts on port 8000
   - Cache is NOT loaded yet (lazy loading)

### Step 6: Initial Cache Population

The API server needs historical data from Spacescope. Trigger the first cache update:

```bash
# Trigger cache update via admin endpoint
curl -X POST https://mechafil-api.fly.dev/admin/update-cache \
  -H "Content-Type: application/json" \
  -v
```

**Expected behavior:**
- Takes ~40 seconds to complete
- Fetches data from Spacescope API
- Writes to `/data/shared-cache` volume
- Returns: `{"status":"success","message":"Cache updated and historical data reloaded"}`

**What gets cached:**
- Historical Filecoin network metrics
- Used as baseline data for simulations
- Typically ~100-500MB

### Step 7: Test the API

Verify the deployment works:

```bash
# Health check (cold start ~15 seconds)
curl https://mechafil-api.fly.dev/health

# Get historical data
curl https://mechafil-api.fly.dev/historical-data

# Run a simulation with defaults
curl -X POST https://mechafil-api.fly.dev/simulate \
  -H "Content-Type: application/json" \
  -d '{}'

# Custom simulation
curl -X POST https://mechafil-api.fly.dev/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "rbp": 4.0,
    "rr": 0.85,
    "fpr": 0.90,
    "forecast_length_days": 365,
    "output": ["available_supply", "network_RBP_EIB"]
  }'
```

**Performance expectations:**
- **Cold start**: ~15 seconds (machine start + JAX initialization)
- **First request**: ~5-6 seconds (lazy loads cache)
- **Subsequent requests**: <1 second (cache in memory)
- **Auto-stop**: ~2-3 minutes after last request

### Step 8: Configure Automated Cache Updates (Optional)

Set up GitHub Actions to update the cache daily:

The repository includes `.github/workflows/update-cache-daily.yml`:

```yaml
name: Daily Cache Update

on:
  schedule:
    - cron: '0 1 * * *'  # 1:00 AM UTC daily
  workflow_dispatch:     # Manual trigger

jobs:
  update-cache:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Cache Update
        run: |
          curl -X POST https://mechafil-api.fly.dev/admin/update-cache \
            -H "Content-Type: application/json" \
            -f -v
```

**Setup:**

1. Ensure the workflow file is in the `main` branch (GitHub only runs scheduled workflows from the default branch)

2. Test manually:
   - Go to **Actions** tab in GitHub
   - Select **Daily Cache Update**
   - Click **Run workflow** > **Run workflow**

3. The workflow will run automatically at 1:00 AM UTC daily

**What it does:**
- Wakes up the machine (auto-start)
- Calls `/admin/update-cache` endpoint
- Machine fetches fresh data from Spacescope
- Updates the cache volume
- Machine goes back to sleep after ~2-3 minutes

---

## Part 2: Deploying the MCP Server

The MCP (Model Context Protocol) server provides Claude.ai with tools to interact with the MechaFil API.

### What is the MCP Server?

The MCP server is a lightweight HTTP service that:
- Exposes tools that Claude.ai can call
- Acts as a bridge between Claude and the MechaFil API
- Uses the FastMCP framework for easy tool definition
- Runs independently from the API server

**Tools provided:**
- `fetch_context()`: Returns system prompt and documentation
- `simulate()`: Runs Filecoin economic simulations
- `get_historical_data()`: Retrieves cached historical data

### Step 1: Prepare the MCP Server Code

The MCP server is located at `/programs/mcp-server-mechafil/`.

**Key file: `server.py`**

The server is configured to support both local (stdio) and remote (HTTP) transports:

```python
if __name__ == "__main__":
    import os
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "http":
        port = int(os.getenv("PORT", "8080"))
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")
```

**Environment variable control:**
- `MCP_TRANSPORT=http`: Uses HTTP transport (for remote deployment)
- `MCP_TRANSPORT=stdio` (or unset): Uses stdio transport (for local Claude Desktop)
- `PORT`: HTTP port (default 8080)
- `MECHAFIL_SERVER_URL`: API server URL (default: `https://mechafil-api.fly.dev`)

### Step 2: Review Dockerfile

The `Dockerfile` in `/programs/mcp-server-mechafil/`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv pip install --system --no-cache fastmcp mcp pydantic requests

# Copy application files
COPY server.py ./
COPY system-prompt.txt ./
COPY documentation-and-instructions/ ./documentation-and-instructions/

# Expose port
EXPOSE 8080

# Set environment variables for HTTP transport
ENV MCP_TRANSPORT=http
ENV PORT=8080
ENV MECHAFIL_SERVER_URL=https://mechafil-api.fly.dev

# Run the server
CMD ["python", "server.py"]
```

**What this does:**
- Lightweight Python 3.11 base image
- Uses `uv` for fast dependency installation
- Installs FastMCP, MCP, Pydantic, Requests
- Configures HTTP transport mode
- Points to deployed API server

### Step 3: Create fly.toml for MCP Server

Create `fly.toml` in `/programs/mcp-server-mechafil/`:

```toml
app = "mechafil-mcp-server"
primary_region = "fra"

[build]
  dockerfile = "Dockerfile"

[env]
  MCP_TRANSPORT = "http"
  PORT = "8080"
  MECHAFIL_SERVER_URL = "https://mechafil-api.fly.dev"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "stop"  # Scale to zero when idle
  auto_start_machines = true   # Start on incoming request
  min_machines_running = 0     # True serverless

  # No health checks - allows faster auto-stop when idle

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

**Key differences from API server:**
- Smaller resources: 512MB RAM, 1 CPU (lightweight proxy)
- Port 8080 (FastMCP default)
- No volume mount (stateless service)
- Same serverless configuration (auto-stop/auto-start)

### Step 4: Create the Fly.io App

```bash
cd /path/to/mechafil/programs/mcp-server-mechafil

# Create app
flyctl apps create mechafil-mcp-server
```

**Result:**
- App URL: `mechafil-mcp-server.fly.dev`
- No machines created yet

### Step 5: Deploy the MCP Server

```bash
# Deploy
flyctl deploy --app mechafil-mcp-server

# Monitor logs
flyctl logs --app mechafil-mcp-server
```

**Deployment process:**

1. **Build** (~1 minute):
   - Builds Docker image
   - Installs dependencies via uv
   - Image size: ~75MB (much smaller than API server)

2. **Deploy** (~30 seconds):
   - Creates machine with 512MB RAM, 1 CPU
   - Starts FastMCP server on port 8080
   - Available at `mechafil-mcp-server.fly.dev`

3. **Startup** (~3-5 seconds):
   - FastMCP initializes
   - Registers tools: `fetch_context`, `simulate`, `get_historical_data`
   - Uvicorn starts HTTP server on port 8080

**Expected log output:**
```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│                   ▄▀▀ ▄▀█ █▀▀ ▀█▀ █▀▄▀█ █▀▀ █▀█          │
│                   █▀  █▀█ ▄▄█  █  █ ▀ █ █▄▄ █▀▀          │
│                                                          │
│                      FastMCP 2.13.1                      │
│                                                          │
│          🖥  Server name: mechafil-server                 │
│          📦 Transport:   HTTP                            │
│          🔗 Server URL:  http://0.0.0.0:8080/mcp         │
│                                                          │
╰──────────────────────────────────────────────────────────╯
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Step 6: Handle Multiple Machines (If Created)

Fly.io sometimes creates 2 machines for high availability. For serverless cost savings, keep only one:

```bash
# List machines
flyctl machine list --app mechafil-mcp-server

# If 2 machines exist, destroy one
flyctl machine destroy <MACHINE_ID> --app mechafil-mcp-server --force
```

### Step 7: Test the MCP Server

The MCP server endpoint is at `/mcp`:

```bash
# Test (should return MCP protocol response)
curl https://mechafil-mcp-server.fly.dev/mcp
```

**Expected behavior:**
- Cold start: ~5 seconds (machine start + FastMCP initialization)
- Returns MCP protocol information
- Auto-stops after ~2-3 minutes of inactivity

### Step 8: Connect to Claude.ai

The MCP server is now ready to use with Claude.ai's Custom Connector feature:

1. Go to **Claude.ai** (https://claude.ai)

2. Click on **Settings** or **Custom Connector** option

3. Select **"Add custom connector"** or **"Remote MCP server URL"**

4. Enter the MCP server URL:
   ```
   https://mechafil-mcp-server.fly.dev/mcp
   ```

5. Give it a name like **"MechaFil Server"**

6. Save the connector

7. Start a new conversation in Claude.ai

**Verify it works:**

In Claude.ai, try asking:
- "Get the historical Filecoin data"
- "Run a simulation with RBP=4.0 and FPR=0.90"
- "What tools do you have available for Filecoin analysis?"

Claude should be able to call the MCP tools and interact with your deployed API.

---

## Understanding the Components

### Component 1: MechaFil API Server

**Location:** `/programs/mechafil-server/`

**Purpose:** Core computational service for Filecoin economic simulations

**Technology Stack:**
- **FastAPI**: Python web framework
- **JAX**: High-performance numerical computing
- **DiskCache**: Persistent caching on volume
- **Poetry**: Python dependency management

**Endpoints:**

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|---------------|
| `/health` | GET | Health check | <1s (warm), ~15s (cold) |
| `/historical-data` | GET | Get cached Filecoin data | <1s (warm), ~5s (cold) |
| `/simulate` | POST | Run economic simulation | 1-5s depending on parameters |
| `/admin/update-cache` | POST | Refresh cache from Spacescope | ~40s |
| `/docs` | GET | Auto-generated API docs | <1s |

**Cold Start Behavior:**
1. Machine starts (Fly.io boots Firecracker VM): ~5s
2. Docker container starts: ~5s
3. JAX imports and initializes: ~5s
4. FastAPI starts listening: <1s
5. **Total cold start: ~15 seconds**

**Warm Behavior:**
- Machine stays running after first request
- Subsequent requests: <1 second
- Auto-stops after ~2-3 minutes of inactivity

**Volume Usage:**
- Location: `/data/shared-cache`
- Size: 3GB (expandable)
- Content: DiskCache database with Spacescope historical data
- Typical usage: 100-500MB
- Persists across machine stops/restarts

**Memory Usage:**
- Startup: ~300-400MB
- After loading cache: ~800MB-1.2GB
- During simulation: ~1-1.5GB
- Configuration: 2GB RAM (comfortable headroom)

### Component 2: MCP Server

**Location:** `/programs/mcp-server-mechafil/`

**Purpose:** Provides Claude.ai with tools to interact with MechaFil API

**Technology Stack:**
- **FastMCP**: Framework for building MCP servers
- **MCP SDK**: Model Context Protocol implementation
- **Pydantic**: Data validation
- **Requests**: HTTP client for API calls

**MCP Tools:**

| Tool | Purpose | Implementation |
|------|---------|----------------|
| `fetch_context()` | Returns system prompt and docs | Reads local files |
| `get_historical_data()` | Gets cached Filecoin data | Calls API `/historical-data` |
| `simulate(SimulationInputs)` | Runs simulation | Calls API `/simulate` |

**How it works:**

1. Claude.ai connects to MCP server via HTTP
2. MCP server exposes tools in MCP protocol format
3. When Claude calls a tool, MCP server:
   - Validates inputs with Pydantic
   - Makes HTTP request to MechaFil API
   - Returns formatted response to Claude

**Cold Start Behavior:**
1. Machine starts: ~3s
2. FastMCP imports: ~1s
3. Server starts listening: <1s
4. **Total cold start: ~5 seconds** (much faster than API)

**Resource Usage:**
- Memory: ~100-150MB
- CPU: Minimal (just proxying requests)
- No persistent storage needed

### Component 3: Fly.io Volume

**Name:** `shared_cache`

**Purpose:** Persistent storage for DiskCache database

**Characteristics:**
- **Type:** Persistent SSD storage
- **Size:** 3GB ($0.15/GB/month = ~$0.45/month)
- **Region:** Frankfurt (fra)
- **Attachment:** Single machine only (Fly.io limitation)
- **Lifecycle:** Survives machine stops, restarts, and redeployments

**What happens when machine stops:**
- Volume data remains intact
- No storage costs during idle time
- Data immediately available when machine restarts

**Backup strategy:**
- Volume is not automatically backed up
- Consider periodic snapshots via Fly.io CLI or custom script
- Data can be regenerated from Spacescope API if lost

### Component 4: GitHub Actions (Optional)

**File:** `.github/workflows/update-cache-daily.yml`

**Purpose:** Automatically refresh cache with latest Spacescope data

**Schedule:** Daily at 1:00 AM UTC

**What it does:**
1. Sends POST request to `/admin/update-cache`
2. Machine wakes up (auto-start)
3. API fetches latest data from Spacescope
4. Cache volume is updated
5. API reloads historical data in memory
6. Machine goes back to sleep

**Cost:** ~$0.01-0.02 per run (40 seconds of compute time)

**Manual trigger:**
- GitHub UI: Actions tab → Daily Cache Update → Run workflow
- CLI: `curl -X POST https://mechafil-api.fly.dev/admin/update-cache`

---

## Monitoring and Maintenance

### Checking Application Status

```bash
# API server status
flyctl status --app mechafil-api

# MCP server status
flyctl status --app mechafil-mcp-server

# List machines
flyctl machine list --app mechafil-api
flyctl machine list --app mechafil-mcp-server
```

**Machine states:**
- `started`: Running and accepting requests
- `stopped`: Idle (scaled to zero)
- `starting`: Waking up from stopped state

### Viewing Logs

```bash
# Real-time logs
flyctl logs --app mechafil-api --follow
flyctl logs --app mechafil-mcp-server --follow

# Recent logs only
flyctl logs --app mechafil-api
flyctl logs --app mechafil-mcp-server

# Specific machine logs
flyctl logs --app mechafil-api --machine <MACHINE_ID>
```

**What to look for:**
- **Startup messages**: JAX backend, server starting
- **Request logs**: HTTP method, path, response code
- **Errors**: Stack traces, failed API calls
- **Auto-stop messages**: "Machine stopped"

### SSH Access

```bash
# SSH into API server machine
flyctl ssh console --app mechafil-api

# Once inside, check cache contents
python3 -c "from diskcache import Cache; c = Cache('/data/shared-cache'); print(list(c))"

# Check cache size
df -h /data/shared-cache
```

### Updating Code

**API Server:**

```bash
cd /path/to/mechafil/programs/mechafil-server

# Make code changes
git add .
git commit -m "Update API logic"

# Redeploy
flyctl deploy --app mechafil-api

# Old machine is destroyed, new one created with updated code
# Volume data persists across redeployment
```

**MCP Server:**

```bash
cd /path/to/mechafil/programs/mcp-server-mechafil

# Make code changes
git add .
git commit -m "Update MCP tools"

# Redeploy
flyctl deploy --app mechafil-mcp-server

# Machine is replaced with new code
```

### Scaling Considerations

**Current setup:** Single machine per app (serverless)

**If traffic increases:**

Option 1: Keep serverless, increase machine size
```bash
# Update fly.toml [[vm]] section
memory = "4gb"  # Increase from 2gb
cpus = 4        # Increase from 2

# Redeploy
flyctl deploy --app mechafil-api
```

Option 2: Run machine 24/7 (no auto-stop)
```toml
[http_service]
  auto_stop_machines = false
  min_machines_running = 1
```

**Note:** With current serverless setup, you CANNOT horizontally scale to multiple machines because:
- Volume can only attach to ONE machine
- Multi-machine would require different caching strategy (e.g., Redis, S3)

### Restarting Machines

```bash
# Restart API server machine
flyctl machine restart <MACHINE_ID> --app mechafil-api

# Restart MCP server machine
flyctl machine restart <MACHINE_ID> --app mechafil-mcp-server

# Restart all machines in an app
flyctl apps restart mechafil-api
```

### Destroying and Recreating

**If you need to start fresh:**

```bash
# Destroy app (warning: deletes everything including volume)
flyctl apps destroy mechafil-api

# Or destroy just the machine (keeps volume)
flyctl machine destroy <MACHINE_ID> --app mechafil-api

# Then redeploy
flyctl deploy --app mechafil-api
```

---

## Cost Breakdown

All costs based on Fly.io pricing (as of 2024):

### MechaFil API Server

| Resource | Usage | Cost/Month |
|----------|-------|------------|
| **Compute (serverless)** | ~100 requests/day, 2-3 min each | $0-2 |
| **Compute (if 24/7)** | 2GB RAM, 2 CPU | ~$15-20 |
| **Volume (3GB)** | Always provisioned | $0.45 |
| **Bandwidth** | Negligible for API responses | $0 |
| **Cache updates** | Daily 40s runs via GitHub Actions | $0-1 |
| **Total (serverless)** | | **$1-5** |
| **Total (24/7)** | | **$15-25** |

### MCP Server

| Resource | Usage | Cost/Month |
|----------|-------|------------|
| **Compute (serverless)** | ~50 requests/day, 1-2 min each | $0-1 |
| **Compute (if 24/7)** | 512MB RAM, 1 CPU | ~$5-8 |
| **Bandwidth** | Negligible | $0 |
| **Total (serverless)** | | **$0-1** |
| **Total (24/7)** | | **$5-8** |

### Combined Total

- **Serverless setup**: **$1-6/month**
- **Always-on setup**: **$20-30/month**

### Cost Optimization Tips

1. **Minimize cold starts**: Longer auto-stop timeout keeps machine warm longer (but costs more)

2. **Batch cache updates**: Update cache once daily instead of multiple times

3. **Monitor usage**: Check Fly.io dashboard for actual compute hours
   ```bash
   flyctl billing show
   ```

4. **Adjust resources**: If API is fast enough, reduce RAM/CPU in `fly.toml`

5. **Regional placement**: Keep both apps in same region to reduce inter-region bandwidth

---

## Troubleshooting

### Problem: API Returns "No cache data found"

**Symptoms:**
- `/historical-data` returns error
- `/simulate` fails with 503 error

**Cause:** Cache hasn't been populated yet

**Fix:**
```bash
# Manually trigger cache update
curl -X POST https://mechafil-api.fly.dev/admin/update-cache -v

# Wait ~40 seconds for completion

# Verify
curl https://mechafil-api.fly.dev/health
```

### Problem: Slow Cold Starts (>20 seconds)

**Cause:** JAX initialization takes time

**Workaround:**
- Accept longer cold starts (architectural limitation)
- Keep machine warm by sending periodic requests
- Increase `auto_stop_machines` grace period (not recommended, increases cost)

**Future improvement:** Use lighter simulation library than JAX

### Problem: Machine Won't Auto-Stop

**Symptoms:**
- Machine stays in `started` state indefinitely
- Higher than expected costs

**Possible causes:**

1. **Health checks still configured**
   ```bash
   # Check fly.toml has no [[http_service.checks]] section
   # Redeploy if needed
   flyctl deploy --app mechafil-api
   ```

2. **Background processes running**
   ```bash
   # SSH in and check processes
   flyctl ssh console --app mechafil-api
   ps aux | grep python
   ```

3. **Long-running requests**
   - Simulations taking >2 minutes will keep machine alive
   - This is expected behavior

### Problem: "Volume Already Attached" Error

**Symptoms:**
```
Error: volume shared_cache is already attached to a machine
```

**Cause:** Trying to create second machine while volume is attached

**Fix:**
```bash
# Option 1: Destroy existing machine first
flyctl machine list --app mechafil-api
flyctl machine destroy <MACHINE_ID> --app mechafil-api
flyctl deploy --app mechafil-api

# Option 2: Detach volume (not recommended, causes downtime)
flyctl volumes detach <VOLUME_ID> --app mechafil-api
```

### Problem: MCP Server Not Visible in Claude.ai

**Symptoms:**
- Can't find tools in Claude conversation
- Custom connector shows error

**Troubleshooting:**

1. **Verify MCP server is running:**
   ```bash
   curl https://mechafil-mcp-server.fly.dev/mcp
   ```

2. **Check logs for errors:**
   ```bash
   flyctl logs --app mechafil-mcp-server
   ```

3. **Verify URL in Claude.ai:**
   - Must be: `https://mechafil-mcp-server.fly.dev/mcp`
   - Include `/mcp` endpoint path
   - Use `https://` not `http://`

4. **Test from Claude.ai:**
   - Delete and re-add the custom connector
   - Start a new conversation
   - Explicitly ask: "What tools do you have available?"

### Problem: Spacescope API Errors

**Symptoms:**
```
Failed to fetch from Spacescope API: 401 Unauthorized
```

**Cause:** Invalid or missing Spacescope token

**Fix:**
```bash
# Verify token is set
flyctl secrets list --app mechafil-api

# Update token (no quotes!)
flyctl secrets set SPACESCOPE_TOKEN='Bearer YOUR_NEW_TOKEN' --app mechafil-api

# Restart machine
flyctl machine restart <MACHINE_ID> --app mechafil-api

# Retry cache update
curl -X POST https://mechafil-api.fly.dev/admin/update-cache
```

### Problem: Build Fails (Out of Memory)

**Symptoms:**
```
Error: failed to build: docker build failed
```

**Cause:** Local Docker has insufficient memory for large JAX build

**Fix:**
```bash
# Use Fly.io's remote builder (more RAM)
flyctl deploy --remote-only --app mechafil-api
```

### Problem: Volume Full

**Check usage:**
```bash
flyctl ssh console --app mechafil-api
df -h /data/shared-cache
exit
```

**Expand volume:**
```bash
# List volumes
flyctl volumes list --app mechafil-api

# Extend to 5GB
flyctl volumes extend <VOLUME_ID> --size 5 --app mechafil-api
```

### Problem: GitHub Actions Workflow Not Running

**Symptoms:**
- Cache not updating daily
- No runs in Actions tab

**Possible causes:**

1. **Workflow not in main branch**
   ```bash
   git checkout main
   git log --oneline .github/workflows/update-cache-daily.yml
   # Should show the file exists in main
   ```

2. **Repository not active**
   - Make a commit in the last 60 days
   - GitHub disables scheduled workflows in inactive repos

3. **Syntax error in workflow file**
   - Check Actions tab for parsing errors
   - Validate YAML syntax

**Manual trigger to test:**
```bash
# Via GitHub UI: Actions → Daily Cache Update → Run workflow

# Via CLI (requires gh CLI)
gh workflow run update-cache-daily.yml
```

---

## Summary

You now have a complete serverless deployment:

### Deployed Services

1. **MechaFil API** (`mechafil-api.fly.dev`)
   - FastAPI service with JAX-based simulations
   - 3GB persistent cache volume
   - Auto-stop/auto-start for cost savings
   - Daily cache updates via GitHub Actions

2. **MCP Server** (`mechafil-mcp-server.fly.dev`)
   - FastMCP HTTP server
   - Provides Claude.ai with 3 tools
   - Lightweight proxy to API server
   - Auto-stop/auto-start enabled

### Architecture Benefits

- **Serverless**: Both services scale to zero when idle (~$1-6/month)
- **Persistent**: Volume survives machine stops
- **Automated**: Daily cache updates via GitHub Actions
- **Independent**: API and MCP server can be updated separately
- **Scalable**: Can increase machine sizes without changing architecture

### Key URLs

- **API Docs**: https://mechafil-api.fly.dev/docs
- **API Health**: https://mechafil-api.fly.dev/health
- **Admin Endpoint**: https://mechafil-api.fly.dev/admin/update-cache
- **MCP Server**: https://mechafil-mcp-server.fly.dev/mcp

### Next Steps for Your Colleagues

1. Test the API endpoints with curl
2. Add MCP server to Claude.ai Custom Connector
3. Ask Claude to run simulations
4. Review logs to understand cold start behavior
5. Monitor costs in Fly.io dashboard
6. Experiment with different simulation parameters

---

## Appendix: Quick Reference

### Useful Commands

```bash
# Status
flyctl status --app mechafil-api
flyctl status --app mechafil-mcp-server

# Logs
flyctl logs --app mechafil-api
flyctl logs --app mechafil-mcp-server

# SSH
flyctl ssh console --app mechafil-api

# Restart
flyctl machine restart <MACHINE_ID> --app mechafil-api

# Deploy
flyctl deploy --app mechafil-api
flyctl deploy --app mechafil-mcp-server

# Secrets
flyctl secrets list --app mechafil-api
flyctl secrets set KEY=VALUE --app mechafil-api

# Volumes
flyctl volumes list --app mechafil-api
flyctl volumes extend <VOLUME_ID> --size 5

# Billing
flyctl billing show
```

### API Endpoints

```bash
# Health
curl https://mechafil-api.fly.dev/health

# Historical data
curl https://mechafil-api.fly.dev/historical-data

# Simulate
curl -X POST https://mechafil-api.fly.dev/simulate \
  -H "Content-Type: application/json" \
  -d '{"rbp": 4.0, "forecast_length_days": 365}'

# Update cache
curl -X POST https://mechafil-api.fly.dev/admin/update-cache
```

### File Locations

- API server: `/programs/mechafil-server/`
- MCP server: `/programs/mcp-server-mechafil/`
- API fly.toml: `/programs/mechafil-server/fly.toml`
- MCP fly.toml: `/programs/mcp-server-mechafil/fly.toml`
- API Dockerfile: `/programs/mechafil-server/docker/Dockerfile`
- MCP Dockerfile: `/programs/mcp-server-mechafil/Dockerfile`
- GitHub workflow: `.github/workflows/update-cache-daily.yml`
