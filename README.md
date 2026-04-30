# Habit Tracker (Docker + CI/CD)

Django REST project with Celery, Redis and PostgreSQL.

## Services

The project runs in separate containers:

- `web` - Django + Gunicorn
- `db` - PostgreSQL
- `redis` - Redis
- `celery` - Celery worker
- `celery-beat` - Celery beat scheduler
- `nginx` - reverse proxy for web/static

## Local run (one command)

1. Create local env file:
   - `cp .env.template .env`
2. Fill required values in `.env`.
3. Start all services:
   - `docker compose up --build -d`

Application will be available on `http://localhost`.

Stop all services:

- `docker compose down`

## CI/CD pipeline

Workflow: `.github/workflows/ci_cd.yml`

Pipeline order:

1. `tests` - run `pytest`
2. `lint` - run `flake8`
3. `build` - docker build + docker compose config validation
4. `publish_image` - push image to GitHub Container Registry (GHCR)
5. `deploy` - auto deploy to remote server (only on push to `main`)

If any previous stage fails, the next stage will not run.

## Remote server setup (Yandex Cloud VM)

Install Docker + Docker Compose plugin:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

Re-login after adding user to docker group.

On server prepare project directory (example):

```bash
mkdir -p /var/www/drf_project
cd /var/www/drf_project
git clone <YOUR_REPOSITORY_URL> .
cp .env.template .env
```

## GitHub Secrets

Configure repository secrets:

- `SERVER_HOST` - server IP/domain
- `SERVER_USER` - SSH user
- `SERVER_PORT` - SSH port (usually `22`)
- `SERVER_SSH_KEY` - private key for deployment
- `PROJECT_PATH` - absolute path on server (e.g. `/var/www/drf_project`)
- `SERVER_ENV_FILE` - full content of production `.env` file
- `GHCR_USERNAME` - GitHub username with access to package
- `GHCR_TOKEN` - GitHub token/PAT with `read:packages`

## Auto-deploy behavior

On push to `main`:

1. image is built and pushed to GHCR
2. workflow connects to server through SSH
3. server updates code to `origin/main` and rewrites `.env`
4. server logs in to GHCR and pulls image
5. `docker compose -f deploy/docker-compose.prod.yml up -d`

## Quick verification on server

```bash
cd /var/www/drf_project
docker compose -f deploy/docker-compose.prod.yml ps
docker compose -f deploy/docker-compose.prod.yml logs --tail=100 web
```
