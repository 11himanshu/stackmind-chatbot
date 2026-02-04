import re
from typing import Optional


# ----------------------------------------------------
# HARD-BLOCKED REQUESTS (LEGAL / SAFETY)
# ----------------------------------------------------

COPYRIGHT_PATTERNS = [
    r"\blyrics\b",
    r"\bfull lyrics\b",
    r"\bentire lyrics\b",
    r"\bsong lyrics\b",
    r"\bwrite lyrics\b",
    r"\bgive lyrics\b"
]


def detect_block_reason(message: str) -> Optional[str]:
    """
    Returns a block reason string if request must be blocked.
    Returns None if request is safe.
    """
    msg = message.lower().strip()

    for pattern in COPYRIGHT_PATTERNS:
        if re.search(pattern, msg):
            return "copyrighted_text"

    return None