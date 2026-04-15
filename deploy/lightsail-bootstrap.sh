#!/usr/bin/env bash
# 在乾淨的 AWS Lightsail Amazon Linux 2023 instance 上一步部署本專案。
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

# ---- 1. 安裝 Docker Engine ----
if ! command -v docker >/dev/null 2>&1; then
    log "安裝 Docker (dnf)..."
    dnf install -y docker
    systemctl enable --now docker
else
    log "Docker 已安裝，跳過"
fi

# ---- 2. 安裝 docker compose plugin ----
# Amazon Linux 2023 官方 repo 沒有 docker-compose-plugin，手動下載 binary 當 CLI plugin。
COMPOSE_PLUGIN_DIR="/usr/libexec/docker/cli-plugins"
COMPOSE_BIN="$COMPOSE_PLUGIN_DIR/docker-compose"
if ! docker compose version >/dev/null 2>&1; then
    log "安裝 docker compose plugin..."
    COMPOSE_VERSION="${COMPOSE_VERSION:-v2.29.7}"
    ARCH="$(uname -m)"
    mkdir -p "$COMPOSE_PLUGIN_DIR"
    curl -fsSL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${ARCH}" \
        -o "$COMPOSE_BIN"
    chmod +x "$COMPOSE_BIN"
fi
docker compose version >/dev/null 2>&1 || die "docker compose plugin 安裝失敗"

# 讓當前 user 免 sudo 用 docker（需 re-login 生效）
if [ -n "${SUDO_USER:-}" ] && ! id -nG "$SUDO_USER" | tr ' ' '\n' | grep -qx docker; then
    usermod -aG docker "$SUDO_USER"
    log "已將 $SUDO_USER 加入 docker group（下次登入生效）"
fi

# ---- 3. 產生 .env ----
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

# ---- 4. build + up ----
log "docker compose up -d --build..."
docker compose up -d --build

log "部署完成。目前狀態："
docker compose ps

WEB_PORT="$(grep -E '^WEB_PORT=' .env | cut -d= -f2)"
PUBLIC_IP="$(curl -fsS --max-time 5 https://checkip.amazonaws.com 2>/dev/null | tr -d '[:space:]' || echo '<your-ip>')"
log "首頁：http://${PUBLIC_IP}:${WEB_PORT:-80}/"
log "提醒：Lightsail networking 需開放 ${WEB_PORT:-80}/tcp"
