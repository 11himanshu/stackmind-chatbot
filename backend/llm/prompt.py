import os
import requests
from dotenv import load_dotenv

from core.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"

# ============================================================
# BASE PROMPT (stable, minimal, identity-safe)
# ============================================================

BASE_PROMPT = """
You are Himanshu’s Bot.

Identity rules:
- If explicitly asked your name, say: I am Himanshu’s Bot.
- If explicitly asked who built or owns you, say:
  I was built by Himanshu, the brain behind this masterpiece.
- Do NOT introduce identity unless explicitly asked.
- Do NOT repeat identity information unprompted.

Core behavior:
- Be helpful, calm, intelligent, and precise.
- Prefer correctness over sounding impressive.
- Never hallucinate facts, APIs, tools, events, or capabilities.
- If unsure, say so clearly and explain what is known vs unknown.

Response quality rules:
- Be concise but complete. Avoid unnecessary verbosity.
- Group related ideas instead of listing everything separately.
- Use clear sections when it improves readability.
- Explain the “why” briefly, not just the “what”.
- Avoid repetitive or redundant points.
- Long lists are allowed only when they add real value.

Tone:
- Sound like a thoughtful engineer explaining to another smart human.
- Never defensive, preachy, or overconfident.
- Do not oversell abilities or claim guarantees.
"""

# ============================================================
# INTENT DETECTION (lightweight, deterministic)
# ============================================================

def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(k in msg for k in [
        "architecture", "flow", "diagram", "how does",
        "working of", "explain docker", "kubernetes",
        "oauth", "system design"
    ]):
        return "visual_explanation"

    if any(k in msg for k in [
        "latest", "today", "current", "news",
        "internet", "search", "online"
    ]):
        return "live_data"

    if any(k in msg for k in [
        "error", "exception", "traceback",
        "bug", "not working", "fails"
    ]):
        return "debugging"

    return "general"

# ============================================================
# SAFE WEB SEARCH (SERPAPI / BING)
# ============================================================

def safe_web_search(query: str) -> str:
    """
    Performs a limited, read-only web search.
    Returns summarized text only.
    Never returns raw URLs to the LLM.
    """

    if not ENABLE_WEB_SEARCH:
        return ""

    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        logger.warning("SERPAPI_API_KEY missing")
        return ""

    try:
        logger.info("Performing safe web search")

        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "engine": "bing",
                "api_key": api_key,
                "num": 5
            },
            timeout=8
        )
        response.raise_for_status()
        data = response.json()

        snippets = []
        for r in data.get("organic_results", [])[:3]:
            snippet = r.get("snippet")
            if snippet:
                snippets.append(snippet)

        return "\n".join(snippets)

    except Exception as e:
        logger.error("Web search failed: %s", e)
        return ""

# ============================================================
# DYNAMIC SYSTEM PROMPT BUILDER
# ============================================================

def build_system_prompt(message: str) -> str:
    intent = detect_intent(message)

    web_context = ""
    if intent == "live_data":
        web_context = safe_web_search(message)

    behavior = ""

    if intent == "visual_explanation":
        behavior = """
Explain using intuition first, then details.
Images may be included only if they genuinely improve understanding.
Use at most one image.
Avoid textbook tone.
"""

    elif intent == "live_data":
        behavior = """
You do not have live internet access.
State this limitation briefly in one sentence.
Immediately offer alternatives:
- explain known concepts
- help frame a good search
- reason from general knowledge
Do not overemphasize the limitation.
"""

    elif intent == "debugging":
        behavior = """
Focus on practical reasoning.
Ask at most one clarifying question if needed.
Do not include images or emojis.
"""

    else:
        behavior = """
Be clear and concise.
Emojis are allowed, but at most one, and only if they add warmth.
"""

    if web_context:
        return BASE_PROMPT + "\n" + behavior + "\n\nKnown context:\n" + web_context

    return BASE_PROMPT + "\n" + behavior