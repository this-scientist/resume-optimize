#!/usr/bin/env bash
# 在项目根目录执行：./scripts/start-backend.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

if [[ ! -d .venv ]]; then
  echo "未找到 backend/.venv，请先创建并安装依赖：" >&2
  echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate" >&2
  echo "  pip install --upgrade pip && pip install -r ../requirements.txt" >&2
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir .
