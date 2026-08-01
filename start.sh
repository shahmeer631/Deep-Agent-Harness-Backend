#!/usr/bin/env sh
set -e
exec uvicorn api.server:app --host 0.0.0.0 --port "${PORT:-8000}"
