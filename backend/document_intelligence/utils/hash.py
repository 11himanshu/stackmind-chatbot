import hashlib
import json
from typing import Any


def compute_content_hash(content: Any) -> str:
    """
    Stable hash for block content.
    Used to detect drift and apply safe patches.
    """
    normalized = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()