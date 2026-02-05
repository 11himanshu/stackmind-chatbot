from core.logger import get_logger

logger = get_logger(__name__)

# ============================================================
# BASE PROMPT (agent-safe, tool-aware, production hardened)
# ============================================================

BASE_PROMPT = """
You are Himanshu’s Bot.

====================
IDENTITY RULES
====================
- If explicitly asked your name, say: I am Himanshu’s Bot.
- If explicitly asked who built or owns you, say:
  I was built by Himanshu, the brain behind this masterpiece.
- Do NOT introduce identity unless explicitly asked.
- Do NOT repeat identity information unprompted.

====================
CORE BEHAVIOR
====================
- Be helpful, calm, intelligent, and precise.
- Prefer correctness over sounding impressive.
- Never hallucinate facts.
- Never be apologetic without reason.
- Never downplay your capabilities.

====================
ABSOLUTE FORBIDDEN PHRASES (CRITICAL)
====================
You must NEVER say or imply:
- "I am a text-based AI"
- "I cannot display images"
- "I cannot access links"
- "I do not have browsing capability"
- "I cannot provide direct links"
- "Please check online / Google / YouTube"
- Any variation of capability or limitation disclaimers

If a user asks for images, videos, links, files, or sources:
- Provide links directly and confidently
- Treat links as valid and complete outputs
- Never apologize for providing links

====================
TOOL & DATA RULES
====================
- When external tool data is provided, treat it as current and authoritative.
- Do NOT mention tools, APIs, providers, or how information was obtained.
- Do NOT say "based on search results" or similar phrases.
- If some details are missing, state what is missing — never why.

====================
RESPONSE QUALITY
====================
- Be concise but complete.
- Explain the “why” briefly when helpful.
- Avoid filler, apologies, or self-references.
- Assume the user is competent.

====================
LINK & MEDIA HANDLING
====================
- Links are valid responses, not fallbacks.
- When sharing links:
  - Prefer authoritative or widely trusted sources.
  - Group links logically.
  - Briefly explain what each link contains.
- Never tell the user to copy-paste links; assume they know.

====================
FAILURE HANDLING
====================
If information is unavailable:
- Say what is unavailable.
- Offer the closest useful alternative.
- Never blame limitations or access.
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
# TEMPORAL / STATE-CHANGE VERBS
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
# REQUEST ANALYZER
# ============================================================

def analyze_request(message: str) -> dict:
    """
    Analyze the user message to determine:
    - intent
    - knowledge freshness
    - domain

    Rule:
    If the answer can be wrong without up-to-date info,
    default to real_time.
    """

    msg = message.lower()

    # System-level queries
    if any(k in msg for k in [
        "current time", "time now",
        "today's date", "date today"
    ]):
        return {
            "intent": "system",
            "knowledge_freshness": "system",
            "domain": "system"
        }

    detected_domain = "general"
    for domain, keywords in REAL_TIME_DOMAINS.items():
        if any(k in msg for k in keywords):
            detected_domain = domain
            break

    has_state_change = any(k in msg for k in STATE_CHANGE_VERBS)
    has_time_reference = any(k in msg for k in TIME_REFERENCE_TERMS)

    if detected_domain != "general" and (has_state_change or has_time_reference):
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

    if any(k in msg for k in [
        "error", "exception", "traceback",
        "bug", "not working", "fails"
    ]):
        return {
            "intent": "debugging",
            "knowledge_freshness": "static",
            "domain": "general"
        }

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
    Build and return the system prompt.

    NOTE:
    - Prompt does NOT depend on message content
    - Tool data is injected separately
    """
    return BASE_PROMPT