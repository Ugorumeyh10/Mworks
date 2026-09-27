#!/bin/sh
set -eu
cd /app
./scripts/gen_jwt_keys.sh
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-server-header
