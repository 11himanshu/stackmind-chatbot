from pathlib import Path
from config import REPO_ROOT

def search_code(query: str):
    results = []
    for path in REPO_ROOT.rglob("*.py"):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue

        text = path.read_text(errors="ignore")
        if query in text:
            results.append(str(path.relative_to(REPO_ROOT)))

    return results