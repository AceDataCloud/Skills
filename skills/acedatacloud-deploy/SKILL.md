---
name: acedatacloud-deploy
description: Deploy AceDataCloud services and integrations. Use when deploying to Kubernetes, setting up OpenClaw agents, configuring WeChat/Telegram bots, or managing Docker containers. Covers Helm chart deployment, CI/CD pipeline, and environment setup.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires access to Tencent Cloud TKE Kubernetes cluster and GHCR container registry.
---

# AceDataCloud Deployment Guide

Deploy and manage AceDataCloud services and integrations.

## Architecture Overview

```
GitHub Actions CI/CD
    → Docker build → ghcr.io/acedatacloud/<image>
    → Helm upgrade → Tencent Cloud TKE (Kubernetes)
```

## Deployment Methods

### 1. Kubernetes (Production)

All services are deployed to Tencent Cloud TKE (Kubernetes) via Helm charts.

**Namespace:** `acedatacloud`

**Container Registry:** `ghcr.io/acedatacloud/`

**CI/CD Trigger:** Push to `main` branch → auto-deploy

### 2. Docker Compose (Development)

Each service has its own `docker-compose.yaml`:

```bash
cd <ServiceDir> && docker compose up --build
```

### 3. Local Development

```bash
# Backend services
cd PlatformBackend && poetry install && python manage.py runserver 0.0.0.0:8007

# Frontend services
cd PlatformFrontend && npm install && npm run dev

# MCP servers
cd MCPSuno && pip install -e ".[dev]" && python main.py
```

## Service Ports

| Service | Port |
|---------|------|
| PlatformBackend | 8007 |
| PlatformGateway | 8000 |
| AuthBackend | 8001 |
| PayBackend | 5003 |
| PlatformFrontend | 8081 |
| Nexior | 8084 |

## OpenClaw Deployment

Deploy AI agents using the OpenClaw Helm chart:

```bash
# Install from the DeploymentOpenClaw chart
helm install <release-name> ./DeploymentOpenClaw \
  --set agent.apiToken=$ACEDATACLOUD_API_TOKEN \
  --set ingress.host=<your-domain> \
  -n acedatacloud
```

Features:
- Multi-ingress support for dynamic host generation
- Auto-scaling based on request volume
- Health check and readiness probes

## CI/CD Pipeline

| Event | Action |
|-------|--------|
| Push to `main` | Build Docker → Push to GHCR → Deploy to K8s |
| Pull Request | Lint + Test + Build (no deploy) |
| Release tag | PyPI publish (MCP servers) |

### Docker Build (PlatformBackend)

```dockerfile
# Runs pytest during build — tests MUST pass
RUN pytest tests/api_cost
```

## Environment Setup

Each service has its own `.env` file (never committed):

```bash
cp .env.example .env
# Edit .env with your credentials
```

Key variables:
- `DATABASE_URL` — PostgreSQL connection
- `REDIS_URL` — Redis connection
- `SECRET_KEY` — Django secret
- `ACEDATACLOUD_API_TOKEN` — API access token

## Bot Integration

### MCP Server Deployment

MCP servers can be deployed as:
- **PyPI packages** (installed via `pip install mcp-suno`, etc.)
- **Hosted endpoints** at `https://<service>.mcp.acedata.cloud/mcp`

### Dify Integration

Dify at `dify.acedata.cloud` auto-provisions AceDataCloud API tokens on OAuth login. 13 custom plugins available for all major services.

## Gotchas

- **PlatformBackend Dockerfile runs `pytest tests/api_cost`** during build — failing tests block deployment
- **PlatformGateway runs 20 replicas** in production for high availability
- **Never commit `.env` files** — each service has its own secrets
- **Database migrations** — PlatformBackend owns the schema; PlatformGateway uses unmanaged models on the same DB
- **MCP server versions** are auto-generated from date (CalVer) in CI
- Always test locally with `docker compose up --build` before pushing to `main`
