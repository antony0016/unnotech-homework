#!/bin/sh
set -e

# web container 啟動時跑 migrate；其他 container（cron）透過 command 跳過
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "[entrypoint] applying migrations..."
    python manage.py migrate --noinput
fi

exec "$@"
