from utils import _post_clean, _violates_identity
import re

__all__ = ["post_process_response"]


def post_process_response(text: str) -> str:
    """
    Safety + post processing.
    """
    cleaned = _post_clean(text)

    if _violates_identity(cleaned):
        return (
            "I am Himanshu’s Bot. "
            "I was built by Himanshu."
        )

    return cleaned



# ============================================================
# RESPONSE CLEANUP (PRESERVE CODE BLOCKS)
# ============================================================

def preprocess_response(text: str) -> str:
    if not text:
        return text

    # Remove bold / italic markdown only
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)

    # IMPORTANT:
    # Do NOT remove fenced code blocks (``` ... ```)
    # Do NOT remove inline code (`code`)
    # Frontend needs them for syntax highlighting

    # Remove markdown headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    return text.strip()