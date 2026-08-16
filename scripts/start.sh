#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "   MiniMax H3 AI 视频生成平台"
echo "=========================================="

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m pip install -r backend/requirements.txt
mkdir -p data/uploads data/videos logs

"$PYTHON_BIN" -m uvicorn backend.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" &
BACKEND_PID=$!
"$PYTHON_BIN" -m http.server "${FRONTEND_PORT:-3000}" --directory . &
FRONTEND_PID=$!

echo "前端: http://localhost:${FRONTEND_PORT:-3000}"
echo "API: http://localhost:${PORT:-8000}"
echo "文档: http://localhost:${PORT:-8000}/docs"

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' INT TERM EXIT
wait "$BACKEND_PID"
