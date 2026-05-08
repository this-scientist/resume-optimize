from __future__ import annotations

import os
from pathlib import Path


def get_data_dir() -> Path:
    """
    本地用户数据根目录。优先环境变量 RESUME_OPTIMIZER_DATA_DIR；
    缺省为 macOS: ~/Library/Application Support/ResumeOptimizer
    其他平台: ~/.local/share/resume-optimizer
    """
    override = os.environ.get("RESUME_OPTIMIZER_DATA_DIR")
    if override:
        p = Path(override).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    home = Path.home()
    if (home / "Library" / "Application Support").exists():
        base = home / "Library" / "Application Support" / "ResumeOptimizer"
    else:
        base = home / ".local" / "share" / "resume-optimizer"
    base.mkdir(parents=True, exist_ok=True)
    return base.resolve()


def sqlite_url(data_dir: Path) -> str:
    db_path = data_dir / "app.sqlite3"
    return f"sqlite:///{db_path.as_posix()}"
