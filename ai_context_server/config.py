from pathlib import Path

# Change this only if repo moves
REPO_ROOT = Path("/Users/himanshumishra/chatbot").resolve()

# Safety: never allow access above repo root
def safe_path(path: Path) -> Path:
    resolved = path.resolve()
    if not str(resolved).startswith(str(REPO_ROOT)):
        raise ValueError("Access outside repo root is not allowed")
    return resolved