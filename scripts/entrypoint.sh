#!/usr/bin/env bash
set -e

if [ "${WAIT_FOR_DB:-1}" = "1" ]; then
  echo "Waiting for postgres..."
  until python -c "import socket; socket.create_connection((\"${POSTGRES_HOST:-db}\", int(\"${POSTGRES_PORT:-5432}\")), 2)" >/dev/null 2>&1; do
    sleep 1
  done
fi

exec "$@"
