#!/usr/bin/env bash
set -e

exec celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
