import sys
from pathlib import Path

from fastapi import FastAPI

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

if load_dotenv and "pytest" not in sys.modules:
    # 将 LANGSMITH_* 等未声明在 Settings 中的变量写入 os.environ（供 LangChain / LangGraph 使用）。
    # pytest 运行时不加载，避免污染测试环境或触发外呼。
    for _p in (_REPO_ROOT / ".env", _BACKEND_DIR / ".env"):
        if _p.is_file():
            load_dotenv(_p, override=False)

from app.api.router import api

app = FastAPI(title="Resume Optimizer Local")
app.include_router(api)
