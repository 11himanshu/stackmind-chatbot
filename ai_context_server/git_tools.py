import subprocess
from typing import List
from config import REPO_ROOT


def git_log(limit: int = 20) -> List[str]:
    """
    Returns last N commits in one-line format.
    """
    result = subprocess.run(
        ["git", "log", f"-{limit}", "--oneline"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout.strip().split("\n")


def git_show(commit_hash: str) -> str:
    """
    Returns full diff and metadata for a given commit.
    """
    result = subprocess.run(
        ["git", "show", commit_hash],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout