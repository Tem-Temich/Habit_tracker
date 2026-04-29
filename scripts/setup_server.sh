#!/usr/bin/env bash
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Run as root: sudo bash scripts/setup_server.sh"
  exit 1
fi

PROJECT_USER="${PROJECT_USER:-deploy}"
PROJECT_DIR="${PROJECT_DIR:-/opt/habit_tracker}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
DOMAIN="${DOMAIN:-_}"

apt update
apt install -y \
  git \
  nginx \
  redis-server \
  postgresql \
  postgresql-contrib \
  python${PYTHON_VERSION} \
  python${PYTHON_VERSION}-venv \
  python3-pip \
  ufw

if ! id "$PROJECT_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$PROJECT_USER"
fi

mkdir -p "$PROJECT_DIR"
chown -R "$PROJECT_USER:$PROJECT_USER" "$PROJECT_DIR"

ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
cat > /etc/nginx/sites-available/habit-tracker <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 10M;

    location /static/ {
        alias ${PROJECT_DIR}/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/habit-tracker /etc/nginx/sites-enabled/habit-tracker
nginx -t
systemctl enable nginx
systemctl restart nginx

echo "Disable SSH password auth manually in /etc/ssh/sshd_config:"
echo "PasswordAuthentication no"
echo "PubkeyAuthentication yes"
echo "Then run: sudo systemctl restart ssh"
