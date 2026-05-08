#!/usr/bin/env bash
# 在项目根目录执行：./scripts/start-frontend.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

if [[ ! -d node_modules ]]; then
  echo "未找到 node_modules，请先执行：cd frontend && npm ci （或 npm install）" >&2
  exit 1
fi

exec npm run dev
