FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

# 系統依賴：curl 用於下載 supercronic；其他是 lxml 所需
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates build-essential libxml2 libxslt1.1 \
 && rm -rf /var/lib/apt/lists/*

# 安裝 uv（從官方 image 複製 binary）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# 安裝 supercronic（給 cron container 用，依 TARGETARCH 選 binary）
ARG TARGETARCH
ARG SUPERCRONIC_VERSION=v0.2.29
RUN set -eux; \
    case "$TARGETARCH" in \
        amd64) SUPERCRONIC_ARCH=amd64 ;; \
        arm64) SUPERCRONIC_ARCH=arm64 ;; \
        *) echo "unsupported arch: $TARGETARCH" && exit 1 ;; \
    esac; \
    curl -fsSL -o /usr/local/bin/supercronic \
        "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-${SUPERCRONIC_ARCH}"; \
    chmod +x /usr/local/bin/supercronic

WORKDIR /app

# 先複製依賴檔以利 layer cache
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 再複製 app 本體
COPY . .

EXPOSE 8000

COPY deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
