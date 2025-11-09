# Fly.io Deployment Guide

Fly.io provides global deployment with Docker containers.

## Prerequisites

- Fly.io account
- Fly CLI installed: `curl -L https://fly.io/install.sh | sh`
- Docker (optional, for local testing)

## Architecture

- **Backend**: FastAPI in Docker container
- **Frontend**: React static site served by backend or separate service
- **Database**: Fly Postgres (or SQLite on volume)

## Step 1: Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

## Step 2: Create Backend App

1. Initialize Fly app:
   ```bash
   fly launch --name spendsense-api
   ```

2. Create `Dockerfile` in project root:
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   EXPOSE 8080

   CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

3. Create `fly.toml`:
   ```toml
   app = "spendsense-api"
   primary_region = "iad"

   [build]

   [http_service]
     internal_port = 8080
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
     processes = ["app"]

   [[vm]]
     memory_mb = 512
     cpu_kind = "shared"
     cpus = 1
   ```

4. Set secrets:
   ```bash
   fly secrets set JWT_SECRET_KEY=your-secret-key
   fly secrets set CORS_ORIGINS=https://your-frontend-url.fly.dev
   ```

5. Deploy:
   ```bash
   fly deploy
   ```

## Step 3: Setup Database

### Option A: Fly Postgres

1. Create Postgres database:
   ```bash
   fly postgres create --name spendsense-db
   ```

2. Attach to app:
   ```bash
   fly postgres attach --app spendsense-api spendsense-db
   ```

3. Get connection string and update code

### Option B: SQLite on Volume

1. Create volume:
   ```bash
   fly volumes create data --size 1 --region iad
   ```

2. Mount in `fly.toml`:
   ```toml
   [mounts]
     source = "data"
     destination = "/app/data"
   ```

## Step 4: Deploy Frontend

Option 1: Serve from backend (add static file serving to FastAPI)
Option 2: Separate Fly app for frontend

For separate app:
1. Create new Fly app: `fly launch --name spendsense-frontend`
2. Use nginx or serve static files
3. Set `VITE_API_URL` environment variable

## Cost Estimates

- **Free tier**: 3 shared-cpu-1x VMs with 256MB RAM
- **Postgres**: $1.94/month for 1GB storage
- **Volume**: $0.15/GB/month

## Advantages

- Global edge deployment
- Docker-based (consistent environments)
- Built-in Postgres option
- Free tier available
- Fast cold starts

