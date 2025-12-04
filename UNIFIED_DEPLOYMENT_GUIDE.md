# MechaFil Complete Deployment Guide

Quick deployment guide for both MechaFil API Server and MCP Server on Fly.io with serverless architecture.

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Claude.ai Web                                 │
│                     (Custom Connector)                               │
└─────────────────────────┬────────────────────────────────────────────┘
                          │ HTTPS
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MCP Server (mechafil-mcp-server.fly.dev)                           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  FastMCP HTTP Server                                          │  │
│  │  - fetch_context() → System docs                             │  │
│  │  - get_historical_data() → Cached Filecoin data              │  │
│  │  - simulate() → Run simulations                               │  │
│  └────────────────────────┬──────────────────────────────────────┘  │
│                           │                                         │
│  Resources:               │ HTTP Calls                              │
│  - 512MB RAM, 1 CPU       │                                         │
│  - Auto-stop: Yes         │                                         │
│  - Cold start: ~5s        │                                         │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MechaFil API (mechafil-api.fly.dev)                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Server                                               │  │
│  │  - /health                                                    │  │
│  │  - /historical-data → DiskCache                               │  │
│  │  - /simulate → JAX computation                                │  │
│  │  - /admin/update-cache                                        │  │
│  └────────────────────────┬──────────────────────────────────────┘  │
│                           │                                         │
│                           ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Persistent Volume: /data/shared-cache (3GB)                │   │
│  │  - Survives restarts                                        │   │
│  │  - DiskCache storage                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Resources:                                                         │
│  - 2GB RAM, 2 CPUs                                                  │
│  - Auto-stop: Yes                                                   │
│  - Cold start: ~15s                                                 │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Fetches data
                           ▼
                    Spacescope API
```

## Prerequisites

```bash
# Install Fly.io CLI
curl -L https://fly.io/install.sh | sh
export PATH="$HOME/.fly/bin:$PATH"

# Login to Fly.io
flyctl auth login

# Get Spacescope API token
# Format: Bearer ghp_xxxxxxxxxxxxx (NO quotes!)
```

## Part 1: Deploy MechaFil API Server

### Quick Steps

```bash
# 1. Navigate to mechafil-server
cd /path/to/mechafil/programs/mechafil-server

# 2. Create app
flyctl apps create mechafil-api

# 3. Create persistent volume (3GB)
flyctl volumes create shared_cache --region fra --size 3 --app mechafil-api

# 4. Set Spacescope token (NO quotes!)
flyctl secrets set SPACESCOPE_TOKEN='Bearer YOUR_TOKEN_HERE' --app mechafil-api

# 5. Deploy
flyctl deploy --app mechafil-api

# 6. Populate cache (takes ~40s)
curl -X POST https://mechafil-api.fly.dev/admin/update-cache

# 7. Test
curl https://mechafil-api.fly.dev/health
curl https://mechafil-api.fly.dev/historical-data
curl -X POST https://mechafil-api.fly.dev/simulate \
  -H 'Content-Type: application/json' \
  -d '{"rbp": 4.0, "forecast_length_days": 365}'
```

### Configuration (fly.toml)

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
  auto_stop_machines = "stop"   # Serverless
  auto_start_machines = true
  min_machines_running = 0      # Scale to zero

[[vm]]
  memory = "2gb"
  cpu_kind = "shared"
  cpus = 2
```

### Key Features

- **Serverless**: Auto-stops after ~2-3 min idle, auto-starts on requests
- **Persistent Cache**: 3GB volume survives restarts
- **Performance**: Cold start ~15s, warm requests <1s
- **Cost**: ~$1-5/month (serverless) or ~$15-25/month (24/7)

## Part 2: Deploy MCP Server

### Quick Steps

```bash
# 1. Navigate to mcp-server-mechafil
cd /path/to/mechafil/programs/mcp-server-mechafil

# 2. Create app
flyctl apps create mechafil-mcp-server

# 3. Deploy
flyctl deploy --app mechafil-mcp-server

# 4. If 2 machines created, destroy one
flyctl machine list --app mechafil-mcp-server
flyctl machine destroy <MACHINE_ID> --app mechafil-mcp-server --force

# 5. Test
curl https://mechafil-mcp-server.fly.dev/mcp
```

### Configuration (fly.toml)

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
  auto_stop_machines = "stop"   # Serverless
  auto_start_machines = true
  min_machines_running = 0      # Scale to zero

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

### Key Features

- **Lightweight**: 512MB RAM, 1 CPU
- **Fast**: Cold start ~5s
- **Stateless**: No persistent storage
- **Cost**: ~$0-1/month (serverless)

## Part 3: Connect to Claude.ai

### Add Custom Connector

1. Go to **Claude.ai** (https://claude.ai)
2. Open **Settings** → **Custom Connectors**
3. Click **Add custom connector**
4. Enter:
   - **Name**: MechaFil Server
   - **URL**: `https://mechafil-mcp-server.fly.dev/mcp`
5. Save and test

### Test in Claude

Ask Claude:
```
"Get the historical Filecoin data"
"Run a simulation with RBP=4.0 and FPR=0.90"
"What tools do you have available?"
```

## Part 4: Automated Cache Updates (Optional)

### GitHub Actions Setup

The API server includes `.github/workflows/update-cache-daily.yml` that runs daily at 1:00 UTC.

**Enable it:**
1. Push workflow file to `main` branch
2. Test manually: GitHub → Actions → Daily Cache Update → Run workflow
3. Verify it runs automatically daily

**What it does:**
```
GitHub Actions (1:00 UTC)
    ↓
POST /admin/update-cache
    ↓
Machine auto-starts
    ↓
Fetches data from Spacescope
    ↓
Updates cache volume
    ↓
Reloads data in memory
    ↓
Machine auto-stops
```

## Quick Reference

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
flyctl machine restart <ID> --app mechafil-api

# Secrets
flyctl secrets list --app mechafil-api
flyctl secrets set KEY=value --app mechafil-api

# Volumes
flyctl volumes list --app mechafil-api
flyctl volumes snapshots create <VOL-ID> --app mechafil-api

# Update cache manually
curl -X POST https://mechafil-api.fly.dev/admin/update-cache
```

### API Endpoints

```bash
# Health check
curl https://mechafil-api.fly.dev/health

# Get historical data
curl https://mechafil-api.fly.dev/historical-data

# Run simulation
curl -X POST https://mechafil-api.fly.dev/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "rbp": 4.0,
    "rr": 0.85,
    "fpr": 0.90,
    "forecast_length_days": 365,
    "output": ["available_supply", "network_RBP_EIB"]
  }'

# Update cache
curl -X POST https://mechafil-api.fly.dev/admin/update-cache
```

## Troubleshooting

### Machine Not Auto-Stopping

**Problem:** Machine stays running, increasing costs

**Solution:**
```bash
# Verify no health checks in fly.toml
grep -A 10 "http_service" fly.toml
# Should NOT have [[http_service.checks]]

# If health checks exist, remove them and redeploy
flyctl machine destroy <ID> --app mechafil-api --force
flyctl deploy --app mechafil-api
```

### Cache Not Loading

**Problem:** API returns 503 errors

**Solution:**
```bash
# Trigger cache update
curl -X POST https://mechafil-api.fly.dev/admin/update-cache -v

# Or SSH and run manually
flyctl ssh console --app mechafil-api
python3 -m services.cache_updater.main --once
exit
```

### Slow Cold Starts

**Problem:** First request takes 15-20s

**Solutions:**
1. **Accept it** (normal for serverless)
2. **Keep warm** (disable auto-stop in fly.toml)
3. **Ping regularly** (add health check via external service)

### Spacescope API Errors

**Problem:** 401 Unauthorized

**Solution:**
```bash
# Update token (NO quotes!)
flyctl secrets set SPACESCOPE_TOKEN='Bearer NEW_TOKEN' --app mechafil-api
flyctl machine restart <ID> --app mechafil-api
```

## Cost Breakdown

### Serverless Mode (Recommended)

| Service | Monthly Cost |
|---------|--------------|
| API Server compute | $0-2 |
| API Server volume (3GB) | $0.45 |
| MCP Server compute | $0-1 |
| **Total** | **$1-5** |

### Always-On Mode

| Service | Monthly Cost |
|---------|--------------|
| API Server | $15-20 |
| Volume | $0.45 |
| MCP Server | $5-8 |
| **Total** | **$20-30** |

## Summary

### Deployed URLs

- **API Docs**: https://mechafil-api.fly.dev/docs
- **API Health**: https://mechafil-api.fly.dev/health
- **Admin Endpoint**: https://mechafil-api.fly.dev/admin/update-cache
- **MCP Server**: https://mechafil-mcp-server.fly.dev/mcp

### Architecture Benefits

- **Cost-effective**: Both services scale to zero when idle
- **Persistent**: Cache survives restarts
- **Automated**: Daily cache updates via GitHub Actions
- **Independent**: Services can be updated separately
- **Scalable**: Increase resources by editing fly.toml

### Typical Usage Flow

```
User asks Claude a question
    ↓
Claude calls MCP Server (auto-starts ~5s)
    ↓
MCP Server calls API Server (auto-starts ~15s if cold)
    ↓
API Server loads cache and runs simulation
    ↓
Returns results to MCP Server
    ↓
MCP Server returns to Claude
    ↓
Both machines idle for 2-3 min
    ↓
Both auto-stop
```

## Next Steps

1. ✅ Deploy API Server
2. ✅ Deploy MCP Server
3. ✅ Connect to Claude.ai
4. ✅ Test simulations
5. ✅ Enable GitHub Actions (optional)
6. 📊 Monitor costs in Fly.io dashboard
7. 📈 Monitor logs and performance

## Support

- **Fly.io Docs**: https://fly.io/docs/
- **Fly.io Community**: https://community.fly.io/
- **GitHub Issues**: Report issues in your repository
