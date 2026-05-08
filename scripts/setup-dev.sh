#!/usr/bin/env bash
# 一键准备本地开发环境（Python venv + pip + npm）
# 用法：在项目根目录 ./scripts/setup-dev.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Python venv + requirements.txt"
cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r "$ROOT/requirements.txt"

echo "==> Frontend npm ci"
cd "$ROOT/frontend"
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi

echo "完成。启动后端：./scripts/start-backend.sh ；另开终端启动前端：./scripts/start-frontend.sh"
