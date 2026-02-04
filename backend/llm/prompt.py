from core.logger import get_logger

logger = get_logger(__name__)

# ============================================================
# BASE PROMPT (agent-safe, tool-aware)
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
- Never hallucinate facts.

IMPORTANT TOOL RULES:
- When external tool data is provided, treat it as current and authoritative.
- Do NOT mention model limitations, training data, or internet access.
- Do NOT mention tools, external context, or how information was obtained.
- Do NOT suggest checking websites or apps when tool data is available.
- If some details are missing from tool data, state what is missing, not why.

Response quality rules:
- Be concise but complete.
- Explain the “why” briefly, not just the “what”.
- Avoid unnecessary repetition.
"""

# ============================================================
# DOMAIN KEYWORDS (EXTENSIBLE, NOT ENTITY-BASED)
# ============================================================

REAL_TIME_DOMAINS = {
    "sports": [
        "match", "score", "result", "won", "lost",
        "t20", "odi", "test", "ipl", "world cup",
        "captain", "coach", "playing", "retired"
    ],
    "politics": [
        "election", "government", "minister",
        "president", "prime minister", "pm",
        "policy", "bill", "parliament"
    ],
    "business": [
        "ceo", "company", "startup", "layoffs",
        "funding", "acquisition", "merger"
    ],
    "entertainment": [
        "movie", "film", "release", "trailer",
        "box office", "series", "season"
    ],
    "music": [
        "song", "album", "track", "release",
        "concert", "tour"
    ],
    "tech": [
        "launch", "released", "update",
        "iphone", "android", "ai model"
    ],
    "finance": [
        "stock", "market", "price", "share",
        "crypto", "bitcoin", "sensex", "nifty",
        "interest rate"
    ],
    "weather": [
        "weather", "temperature", "rain",
        "storm", "forecast"
    ]
}

# ============================================================
# TEMPORAL / STATE-CHANGE VERBS (CRITICAL)
# ============================================================

STATE_CHANGE_VERBS = [
    "is", "are", "was", "were",
    "still", "currently",
    "retired", "playing", "resigned",
    "appointed", "removed", "quit",
    "won", "lost", "ended",
    "released", "launched"
]

TIME_REFERENCE_TERMS = [
    "last", "latest", "recent", "new",
    "current", "today", "now",
    "this year", "this month", "yesterday"
]

# ============================================================
# REQUEST ANALYZER (AUTHORITATIVE)
# ============================================================

def analyze_request(message: str) -> dict:
    """
    Analyze the user message to determine:
    - intent
    - knowledge freshness (static | real_time | system)
    - domain

    Design principle:
    If the answer can be wrong without up-to-date information,
    default to real_time.
    """

    msg = message.lower()

    # -----------------------------
    # System-level questions
    # -----------------------------
    if any(k in msg for k in [
        "current time", "time now",
        "today's date", "date today"
    ]):
        return {
            "intent": "system",
            "knowledge_freshness": "system",
            "domain": "system"
        }

    # -----------------------------
    # Domain detection
    # -----------------------------
    detected_domain = "general"
    for domain, keywords in REAL_TIME_DOMAINS.items():
        if any(k in msg for k in keywords):
            detected_domain = domain
            break

    # -----------------------------
    # Temporal reasoning
    # -----------------------------
    has_state_change = any(k in msg for k in STATE_CHANGE_VERBS)
    has_time_reference = any(k in msg for k in TIME_REFERENCE_TERMS)

    # -----------------------------
    # Real-time decision rule
    # -----------------------------
    if (
        detected_domain != "general"
        and (has_state_change or has_time_reference)
    ):
        return {
            "intent": "lookup",
            "knowledge_freshness": "real_time",
            "domain": detected_domain
        }

    if has_time_reference:
        
        return {
            "intent": "lookup",
            "knowledge_freshness": "real_time",
            "domain": detected_domain
        }
    
    # -----------------------------
    # Debugging / explanation
    # -----------------------------
    if any(k in msg for k in [
        "error", "exception", "traceback",
        "bug", "not working", "fails"
    ]):
        return {
            "intent": "debugging",
            "knowledge_freshness": "static",
            "domain": "general"
        }

    # -----------------------------
    # Default: timeless knowledge
    # -----------------------------
    
    return {
        "intent": "general",
        "knowledge_freshness": "static",
        "domain": "general"
    }

# ============================================================
# SYSTEM PROMPT BUILDER
# ============================================================

def build_system_prompt(message: str | None = None) -> str:
    """
    Build the system prompt.

    NOTE:
    - message is accepted for backward compatibility
    - prompt does NOT depend on message content
    - tool data is injected separately by the LLM layer
    """
    
    return BASE_PROMPT