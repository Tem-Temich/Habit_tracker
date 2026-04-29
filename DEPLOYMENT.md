# Habit Tracker deployment guide

## 1. Server bootstrap

1. Create Ubuntu server and connect as `root`.
2. Clone repository to `/opt/habit_tracker`.
3. Run:
   - `sudo bash scripts/setup_server.sh`
4. Copy service files:
   - `sudo cp deploy/systemd/*.service /etc/systemd/system/`
   - `sudo systemctl daemon-reload`
   - `sudo systemctl enable habit-tracker habit-tracker-celery habit-tracker-celery-beat`
5. Copy nginx config:
   - `sudo cp deploy/nginx/habit-tracker.conf /etc/nginx/sites-available/habit-tracker`
   - `sudo ln -sf /etc/nginx/sites-available/habit-tracker /etc/nginx/sites-enabled/habit-tracker`
   - `sudo nginx -t && sudo systemctl restart nginx`

## 2. SSH and firewall hardening

1. Add public key to `~/.ssh/authorized_keys` on server.
2. Disable password auth in `/etc/ssh/sshd_config`:
   - `PasswordAuthentication no`
   - `PubkeyAuthentication yes`
3. Restart ssh daemon:
   - `sudo systemctl restart ssh`
4. Ensure only required ports are open:
   - `22/tcp` (SSH)
   - `80/tcp` and `443/tcp` (HTTP/HTTPS)

## 3. Environment variables

1. Copy `.env.template` to `.env`.
2. Fill all secrets and production values.
3. Never commit real `.env` file.

## 4. GitHub Actions secrets

Add these repository secrets:

- `SERVER_HOST` - server IP or domain.
- `SERVER_USER` - ssh user for deployment.
- `SERVER_PORT` - usually `22`.
- `SERVER_SSH_KEY` - private key used by GitHub Actions.
- `PROJECT_PATH` - absolute path to project on server (e.g. `/opt/habit_tracker`).

## 5. CI/CD pipeline behavior

Workflow file: `.github/workflows/ci_cd.yml`

Pipeline order:

1. `tests` - runs `pytest`.
2. `lint` - runs `flake8`.
3. `build` - runs `manage.py check --deploy` and `collectstatic`.
4. `deploy` - runs on push to `main` only after all previous jobs pass.

If tests/lint/build fail, deploy is not executed.

## 6. Manual verification checklist

1. `sudo systemctl status habit-tracker`
2. `sudo systemctl status habit-tracker-celery`
3. `sudo systemctl status habit-tracker-celery-beat`
4. Open `http://<server-ip>/` and verify API responds.
5. Check auto-restart:
   - `sudo systemctl restart habit-tracker` and ensure app returns.
