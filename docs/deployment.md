# Ekosistem Satwa — Deployment Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Host                          │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  ekosistem-satwa-  │    │  ekosistem-satwa-  │    │ ekosistem-satwa- │ │
│  │  api         │───▶│  db          │    │ pgadmin    │ │
│  │  (port 8080) │    │  (port 5432) │    │ (port 5050)│ │
│  │              │    │              │    │ (debug)    │ │
│  └──────────────┘    └──────────────┘    └────────────┘ │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐                                        │
│  │  host.docker │  (Ollama / vLLM for local inference)   │
│  │  .internal   │                                        │
│  └──────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

**Services:**
| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| API | ekosistemsatwa-api | 8080:8000 | FastAPI backend (ML + AI) |
| DB | ekosistemsatwa-db | 5432 | PostgreSQL 16 |
| pgAdmin | ekosistemsatwa-pgadmin | 5050:80 | DB admin (debug profile only) |

## Prerequisites

- Docker Engine 24+ with Compose V2
- 4 GB free RAM minimum (2 GB for API + 1 GB for DB + overhead)
- 2+ CPU cores recommended for ML inference
- (Optional) Ollama or vLLM running on host for local AI inference

## Quick Start

```bash
# 1. Clone & enter project
cd /path/to/ekosistem-satwa-ai

# 2. Copy production env template and fill secrets
cp .env.production .env
# Edit .env — set API keys, passwords, etc.

# 3. Build and start
docker compose -f docker-compose.prod.yml up -d

# 4. Verify health
curl http://localhost:8080/health

# 5. Check logs
docker compose -f docker-compose.prod.yml logs -f api
```

## Environment Variables

See `.env.production` for the full list. Key variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `POSTGRES_PASSWORD` | Yes | — | DB password |
| `EKOSISTEM_SATWA_VET_API_KEY` | Yes* | — | Auth key for vet endpoints |
| `EKOSISTEM_SATWA_ADMIN_API_KEY` | Yes* | — | Auth key for admin endpoints |
| `EKOSISTEM_SATWA_AI_PROVIDER` | No | `local` | AI provider: openai/anthropic/local |
| `OPENAI_API_KEY` | If OpenAI | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | If Anthropic | — | Anthropic API key |

*Required for production; leave empty for dev.

## Resource Limits

The API service has resource constraints defined in docker-compose:

| Resource | Limit | Reservation |
|----------|-------|-------------|
| API CPU | 2.0 cores | 0.5 cores |
| API Memory | 2 GB | 512 MB |
| DB CPU | 1.0 core | 0.25 cores |
| DB Memory | 1 GB | 256 MB |

**ML Inference Notes:**
- RandomForest models are CPU-bound — more cores = faster inference
- Models are loaded at startup (~50-200 MB per species)
- Expect ~100-500ms per prediction depending on model size

## Health Checks

The API has a built-in health endpoint at `/health`:

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "ok",
  "llm_available": true,
  "knowledge_base": {
    "categories": 10,
    "breeds": 177,
    "diseases": 44,
    "symptoms": 146
  },
  "learning_store": { "count": 0 }
}
```

Docker also runs a container-level HEALTHCHECK every 30s. Check status:
```bash
docker inspect --format='{{.State.Health.Status}}' ekosistem-satwa-api
```

## Deployment Steps (Production)

### 1. Build the Image

```bash
docker compose -f docker-compose.prod.yml build api
```

This creates a multi-stage slim image:
- **Builder stage**: Installs all Python deps (including build tools for scikit-learn)
- **Runtime stage**: Python 3.11-slim + only runtime deps (~300-400 MB final image)

### 2. Deploy Stack

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Wait for DB to be healthy (20-30s)
docker compose -f docker-compose.prod.yml logs -f postgres

# Verify API is healthy
curl http://localhost:8080/health
```

### 3. Seed Database (First Deploy Only)

```bash
# Generate seed SQL
docker compose -f docker-compose.prod.yml exec api python -m ekosistem_satwa.seed_generator

# Apply schema
docker compose -f docker-compose.prod.yml exec -T postgres psql -U ekosistemsatwa -d ekosistemsatwa < seed/schema.sql

# Apply seed data
docker compose -f docker-compose.prod.yml exec -T postgres psql -U ekosistemsatwa -d ekosistemsatwa < seed/seed.sql
```

### 4. Train ML Models (First Deploy / After Data Changes)

```bash
docker compose -f docker-compose.prod.yml exec api python -m ekosistem_satwa.ml.train
```

### 5. Verify Full System

```bash
# System status
curl http://localhost:8080/api/status

# ML prediction test
curl -X POST http://localhost:8080/ml/predict \
  -H 'Content-Type: application/json' \
  -d '{"category_slug":"dog","symptoms":["Muntah hebat","Diare berdarah","Lemas/lesu"]}'

# Knowledge base stats
curl http://localhost:8080/api/stats/breakdown
```

## Rollback

```bash
# Roll back to previous image
docker compose -f docker-compose.prod.yml stop api
docker compose -f docker-compose.prod.yml rm api
docker compose -f docker-compose.prod.yml up -d --no-build api

# Or use a specific tag
docker compose -f docker-compose.prod.yml up -d api:previous-tag
```

## Backup & Restore

### Database Backup
```bash
docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U ekosistemsatwa ekosistemsatwa > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Database Restore
```bash
cat backup_file.sql | docker compose -f docker-compose.prod.yml exec -T postgres psql -U ekosistemsatwa -d ekosistemsatwa
```

### Artifacts Backup
```bash
# ML models and learning data live in a Docker volume
docker run --rm -v ekosistem_satwa_artifacts:/data -v $(pwd):/backup alpine tar czf /backup/artifacts_backup.tar.gz -C /data .
```

## Monitoring

### Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# API only
docker compose -f docker-compose.prod.yml logs -f api

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 api
```

### Resource Usage
```bash
docker stats ekosistem-satwa-api ekosistem-satwa-db
```

### Health Check Automation
The API exposes `/api/status` with component-level health:
- `backend` — API version and name
- `data` — knowledge base stats
- `ai` — LLM availability and provider info
- `ml` — trained model count
- `database` — PostgreSQL connectivity
- `ai_usage` — recent token usage telemetry

## Troubleshooting

### API won't start
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs api

# Verify .env exists and has required vars
docker compose -f docker-compose.prod.yml config

# Test connectivity to DB
docker compose -f docker-compose.prod.yml exec api python -c "from ekosistem_satwa.api.deps import db_status; print(db_status())"
```

### ML models not found
```bash
# Train models inside container
docker compose -f docker-compose.prod.yml exec api python -m ekosistem_satwa.ml.train

# Check artifacts volume
docker compose -f docker-compose.prod.yml exec api ls -la /app/artifacts/models/
```

### Out of memory
- Increase memory limit in `docker-compose.prod.yml` under `deploy.resources.limits.memory`
- Reduce ML model count or use smaller models
- Consider a dedicated inference server for large deployments

## Security Notes

1. **NEVER commit .env to git** — it's in `.gitignore`
2. Change default passwords (`POSTGRES_PASSWORD`, `PGADMIN_PASSWORD`)
3. pgAdmin runs under `debug` profile only — omit `--profile debug` in production
4. API auth keys (`EKOSISTEM_SATWA_VET_API_KEY`, `EKOSISTEM_SATWA_ADMIN_API_KEY`) should be strong random strings
5. DB port 5432 is not exposed to host by default (comment in docker-compose if needed)

## Reverse Proxy (Nginx)

A shared nginx reverse proxy at `infra/nginx/` provides TLS termination and routing:

| Domain | Target | Service |
|--------|--------|---------|
| `vet.naincode.id` | `ekosistemsatwa-api:8000` | Ekosistem Satwa API |
| `api.naincode.id` | `naincode-platform-api:8000` | Naincode Platform API |
| `app.naincode.id` | `naincode-platform-web:3000` | Naincode Platform Web |

```bash
# Start the reverse proxy (from repo root)
docker compose -f infra/nginx/docker-compose.yml up -d

# Verify config
docker compose -f infra/nginx/docker-compose.yml exec nginx nginx -t
```

See `infra/nginx/ssl/README.md` for SSL certificate setup.

## Disaster Recovery

### Full System Restore
```bash
# 1. Restore database
gunzip -c /backups/ekosistem_satwa_YYYYMMDD/backup.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres psql -U ekosistemsatwa -d ekosistemsatwa

# 2. Restore artifacts (ML models, learning data)
docker run --rm \
  -v ekosistemsatwa_artifacts:/dest \
  -v /backups/ekosistem_satwa_YYYYMMDD:/src \
  alpine tar xzf /src/artifacts.tar.gz -C /dest

# 3. Restart stack
docker compose -f docker-compose.prod.yml up -d
```

### Container Restart Loop
```bash
# Check restart count
docker inspect --format='{{.RestartCount}}' ekosistemsatwa-api

# If >5 restarts in 60s, investigate logs
docker logs ekosistemsatwa-api --tail 100

# Force recreate
docker compose -f docker-compose.prod.yml up -d --force-recreate api
```
