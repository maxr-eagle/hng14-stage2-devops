HNG Stage 2 DevOps Project

General Overview

This project is a multi-service application built using a DevOps workflow. It demonstrates containerization, service orchestration, CI/CD automation, and integration testing.

The system consists of:

API (FastAPI) – handles job creation and status
Worker – processes jobs from a queue
Redis – message broker
Frontend – user interface
Docker Compose – orchestrates all services
GitHub Actions – CI pipeline (lint, test, build, integration)

Architecture

```
Frontend (3000) → API (8000) → Redis → Worker
```

1). The frontend communicates with the API
2). The API pushes jobs to Redis
3). The Worker consumes and processes jobs
4). Redis acts as a queue between API and Worker


Technologies Used

Python (FastAPI, Pytest, Flake8)
Node.js (Frontend)
Redis
Docker & Docker Compose
GitHub Actions (CI/CD)

📂 Project Structure

```
.
├── api/
├── worker/
├── frontend/
├── docker-compose.yml
├── .github/workflows/
└── .env.example
```

---

🔐 Environment Variables
Create a `.env` file (do NOT commit it):
```
REDIS_PASSWORD=yourpassword
API_URL=http://api:8000
```

How to Run Locally

1. Clone the repository

```
git clone <your-repo-url>
cd hng14-stage2-devops
```

2. Create `.env`

```
cp .env.example .env
```

3. Start services

```
docker compose up --build
```

4. Access services
API → http://localhost:8000/health
Frontend → http://localhost:3000

Running Tests
```
pytest api/tests -q
```
Linting
```
flake8 api worker
```
🔄 CI/CD Pipeline

GitHub Actions pipeline includes:

1. Lint Stage
    Code quality checks using Flake8

2. Test Stage
    Unit tests with Pytest

3. Build Stage
    Docker images are built for all services

4. Integration Stage
    Full system is started with Docker Compose
    Health checks ensure all services are running


Health Checks
Each service includes a health check:
API → `/health`
Frontend → `/health`
Redis → container health
Worker → startup validation

Important Notes
* .env is ignored and not committed
* No secrets are hardcoded in the repository
* All services communicate via internal Docker network
* CI pipeline ensures reproducibility


Project Goal
To demonstrate:
* Containerized microservices architecture
* CI/CD pipeline setup
* Service communication and orchestration
* Debugging and reliability in distributed systems

Author
Maxwell Grant

