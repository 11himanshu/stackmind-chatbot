from pathlib import Path
from config import REPO_ROOT, safe_path

def list_files(relative_path: str = ""):
    base = safe_path(REPO_ROOT / relative_path)
    return [
        {
            "name": p.name,
            "path": str(p.relative_to(REPO_ROOT)),
            "is_dir": p.is_dir(),
        }
        for p in base.iterdir()
        if not p.name.startswith(".")
    ]

def read_file(relative_path: str):
    path = safe_path(REPO_ROOT / relative_path)
    if path.is_dir():
        raise ValueError("Cannot read a directory")
    return path.read_text(encoding="utf-8")