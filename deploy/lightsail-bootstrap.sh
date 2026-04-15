#!/usr/bin/env bash
# 在乾淨的 AWS Lightsail Ubuntu instance 上一步部署本專案。
#
# 用法（SSH 進 instance 後）：
#   cd unnotech-homework
#   sudo bash deploy/lightsail-bootstrap.sh
#
# 冪等：重跑會跳過已安裝/已設定的步驟，並重新 build + up。

set -euo pipefail

log() { printf '\033[1;32m[bootstrap]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[bootstrap]\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31m[bootstrap]\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "請用 sudo 執行（需安裝 docker）"

cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"
log "專案目錄：$PROJECT_DIR"

# ---- 1. 安裝 Docker Engine + compose plugin ----
if ! command -v docker >/dev/null 2>&1; then
    log "安裝 Docker..."
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    . /etc/os-release
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
else
    log "Docker 已安裝，跳過"
fi

docker compose version >/dev/null 2>&1 || die "docker compose plugin 未安裝"

# ---- 2. 產生 .env ----
if [ ! -f .env ]; then
    log "建立 .env..."
    SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))' 2>/dev/null \
        || openssl rand -base64 50 | tr -d '\n/+=')"

    PUBLIC_IP="$(curl -fsS --max-time 5 https://checkip.amazonaws.com 2>/dev/null | tr -d '[:space:]' || true)"
    [ -z "$PUBLIC_IP" ] && PUBLIC_IP="$(curl -fsS --max-time 5 ifconfig.me 2>/dev/null || true)"

    HOSTS="localhost,127.0.0.1,web"
    [ -n "$PUBLIC_IP" ] && HOSTS="$HOSTS,$PUBLIC_IP" && log "偵測到 public IP：$PUBLIC_IP"

    cat > .env <<EOF
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=$HOSTS
WEB_PORT=${WEB_PORT:-80}
EOF
    chmod 600 .env
    log ".env 已建立（SECRET_KEY 已隨機產生）"
else
    log ".env 已存在，保留不覆寫"
fi

# ---- 3. build + up ----
log "docker compose up -d --build..."
docker compose up -d --build

log "部署完成。目前狀態："
docker compose ps

WEB_PORT="$(grep -E '^WEB_PORT=' .env | cut -d= -f2)"
PUBLIC_IP="$(curl -fsS --max-time 5 https://checkip.amazonaws.com 2>/dev/null | tr -d '[:space:]' || echo '<your-ip>')"
log "首頁：http://${PUBLIC_IP}:${WEB_PORT:-80}/"
log "提醒：Lightsail networking 需開放 ${WEB_PORT:-80}/tcp"
