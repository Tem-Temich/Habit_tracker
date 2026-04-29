#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${VENV_PATH:-$PROJECT_DIR/.venv}"
SERVICE_NAME="${SERVICE_NAME:-habit-tracker}"
CELERY_SERVICE_NAME="${CELERY_SERVICE_NAME:-habit-tracker-celery}"
CELERY_BEAT_SERVICE_NAME="${CELERY_BEAT_SERVICE_NAME:-habit-tracker-celery-beat}"

cd "$PROJECT_DIR"

if [ ! -f ".env" ]; then
  echo ".env not found in $PROJECT_DIR"
  exit 1
fi

if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
pip install --upgrade pip
pip install poetry
poetry config virtualenvs.create false --local
poetry install --only main --no-root --no-interaction --no-ansi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

sudo systemctl restart "$SERVICE_NAME"
sudo systemctl restart "$CELERY_SERVICE_NAME"
sudo systemctl restart "$CELERY_BEAT_SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager
