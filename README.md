# HNG14 Stage 2 DevOps — Job Processing System

A production-ready job processing system built with three services:
- **Frontend** — Node.js/Express server for submitting and tracking jobs
- **API** — Python/FastAPI service that creates jobs and serves status updates
- **Worker** — Python service that picks up and processes jobs from a queue
- **Redis** — Shared message queue between the API and worker

---

## Architecture

```
Browser → Frontend (port 3000) → API (port 8000) → Redis
                                                      ↑
                                                   Worker
```

All services communicate over a named internal Docker network.
Redis is never exposed to the host machine.

---

## Prerequisites

Make sure the following are installed on your machine before starting:

| Tool | Version | Install |
|------|---------|---------|
| Docker | 24.0+ | https://docs.docker.com/get-docker |
| Docker Compose | 2.0+ | Included with Docker Desktop |
| Git | Any | https://git-scm.com |

Verify your installations:
```bash
docker --version
docker compose version
git --version
```

---

## Quick Start

### Step 1 — Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/hng14-stage2-devops.git
cd hng14-stage2-devops
```

### Step 2 — Create your environment file
```bash
cp .env.example .env
```

Open `.env` and set a strong Redis password:
```bash
REDIS_PASSWORD=your_strong_password_here
API_URL=http://api:8000
```

### Step 3 — Build and start the stack
```bash
docker compose up --build -d
```

### Step 4 — Verify all services are healthy
```bash
docker compose ps
```

You should see all four services with `healthy` status:
```
NAME                             STATUS
hng14-stage2-devops-redis-1      Up (healthy)
hng14-stage2-devops-api-1        Up (healthy)
hng14-stage2-devops-worker-1     Up (healthy)
hng14-stage2-devops-frontend-1   Up (healthy)
```

### Step 5 — Open the dashboard
Navigate to http://localhost:3000 in your browser.

---

## Using the Application

1. Open http://localhost:3000
2. Click **Submit New Job**
3. Watch the job status update from `queued` → `completed`
4. Submit multiple jobs and track them all simultaneously

---

## Stopping the Stack

```bash
# Stop all containers
docker compose down

# Stop and remove all data including Redis volume
docker compose down -v
```

---

## Environment Variables

All configuration is managed through environment variables.
Copy `.env.example` to `.env` and fill in real values.

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_PASSWORD` | Password for Redis authentication | `K9#mP2$vL8nQ4@xR` |
| `API_URL` | URL frontend uses to reach the API | `http://api:8000` |

> ⚠️ Never commit your `.env` file. It is protected by `.gitignore`.

---

## CI/CD Pipeline

The pipeline runs automatically on every push and pull request.
It consists of 6 stages that run in strict order:

```
lint → test → build → security-scan → integration-test → deploy
```

| Stage | What it does |
|-------|-------------|
| **lint** | Runs flake8 (Python), eslint (JavaScript), hadolint (Dockerfiles) |
| **test** | Runs pytest with mocked Redis, uploads coverage report as artifact |
| **build** | Builds all three images, tags with git SHA and latest, pushes to local registry |
| **security-scan** | Scans all images with Trivy, fails on CRITICAL findings, uploads SARIF |
| **integration-test** | Spins up full stack, submits a job, polls until completion, tears down |
| **deploy** | Performs rolling update — validates new image before replacing old one |

A failure in any stage prevents all subsequent stages from running.

The deploy stage only runs on pushes to `main`.

---

## Project Structure

```
hng14-stage2-devops/
├── .github/
│   └── workflows/
│       └── pipeline.yml      # CI/CD pipeline
├── api/
│   ├── Dockerfile            # Production Dockerfile (multi-stage)
│   ├── .dockerignore
│   ├── main.py               # FastAPI application
│   ├── requirements.txt      # Pinned Python dependencies
│   └── tests/
│       ├── __init__.py
│       └── test_main.py      # Unit tests with mocked Redis
├── frontend/
│   ├── Dockerfile            # Production Dockerfile (multi-stage)
│   ├── .dockerignore
│   ├── app.js                # Express server
│   ├── package.json
│   ├── package-lock.json
│   └── views/
│       └── index.html        # Job dashboard UI
├── worker/
│   ├── Dockerfile            # Production Dockerfile (multi-stage)
│   ├── .dockerignore
│   ├── worker.py             # Job processing worker
│   └── requirements.txt      # Pinned Python dependencies
├── docker-compose.yml        # Full stack orchestration
├── .env.example              # Environment variable template
├── FIXES.md                  # All bugs found and fixed
└── README.md                 # This file
```

---

## Viewing Logs

```bash
# All services
docker compose logs -f

# Individual service
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f frontend
docker compose logs -f redis
```

---

## Troubleshooting

### Services not becoming healthy
```bash
# Check detailed status
docker compose ps

# Check specific service logs
docker compose logs api
```

### Port already in use
```bash
# Find what is using the port
lsof -i :3000
lsof -i :8000

# Stop the process using the port then retry
docker compose up -d
```

### Redis connection errors
```bash
# Verify Redis is running and healthy
docker compose ps redis

# Test Redis connection
docker compose exec redis redis-cli ping
```

### Full reset
```bash
# Remove everything and start fresh
docker compose down -v
docker system prune -f
docker compose up --build -d
```

---

## Security

- All services run as non-root users inside containers
- Redis is not exposed to the host machine
- No secrets are hardcoded anywhere in the codebase
- All images are scanned for vulnerabilities with Trivy on every build
- Environment variables are used for all configuration

---

## Bug Fixes

See [FIXES.md](./FIXES.md) for a full list of all bugs found in the
original source code and how each one was fixed.
