import regex as re


def _post_clean(text: str) -> str:
    """
    Light cleanup only.
    Frontend handles rendering.
    """
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text.strip()


def _violates_identity(text: str) -> bool:
    """
    Detect identity violations from LLM.
    """
    bad_phrases = [
        "i don't have a name",
        "i do not have a name",
        "i don't have an owner",
        "i do not have an owner",
        "collective project",
        "technology company",
        "assistant or ai assistant"
    ]
    lower = text.lower()
    return any(p in lower for p in bad_phrases)