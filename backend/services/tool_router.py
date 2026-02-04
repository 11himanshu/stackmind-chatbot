from core.logger import get_logger
from llm.prompt import analyze_request
from llm.streaming import stream_llm_response
from tools.web_search import run_web_search

# ------------------------------------------------
# SAFETY GATE (HARD BLOCKS)
# ------------------------------------------------
import re

COPYRIGHT_PATTERNS = [
    r"\blyrics\b",
    r"\bfull lyrics\b",
    r"\bgive lyrics\b",
    r"\bwrite lyrics\b",
    r"\bsong lyrics\b"
]

def _is_copyrighted_request(message: str) -> bool:
    msg = message.lower().strip()
    return any(re.search(p, msg) for p in COPYRIGHT_PATTERNS)


logger = get_logger(__name__)


class ToolRouter:
    """
    Decides how a user message should be handled.

    Responsibilities:
    - Analyze the request (intent + freshness + domain)
    - Enforce real-time vs static knowledge rules
    - Execute external tools when required
    - Route to LLM streaming only when appropriate

    NOTE:
    - No database access
    - No persistence
    """

    @staticmethod
    def stream_response(
        *,
        message: str,
        conversation_history: list[dict]
    ):
        """
        Route the request and return a streaming generator.
        """

        try:
            # ------------------------------------------------
            # SAFETY GATE (RUNS BEFORE ANALYZER)
            # ------------------------------------------------
            if _is_copyrighted_request(message):
                logger.info(
                    "SAFETY_BLOCK | type=copyrighted_text | message=%s",
                    message
                )

                def blocked_stream():
                    yield (
                        "I cannot provide full song lyrics due to copyright restrictions. "
                        "I can summarize the song, explain its meaning, or share a short excerpt."
                    )

                return blocked_stream()

            # ------------------------------------------------
            # Analyze request (authoritative)
            # ------------------------------------------------
            analysis = analyze_request(message)

            intent = analysis["intent"]
            freshness = analysis["knowledge_freshness"]
            domain = analysis["domain"]

            logger.info(
                "TOOL_ROUTER_DECISION | intent=%s | freshness=%s | domain=%s | message=%s",
                intent,
                freshness,
                domain,
                message
            )

            # ------------------------------------------------
            # SYSTEM-LEVEL QUESTIONS
            # ------------------------------------------------
            if freshness == "system":
                logger.info("SYSTEM_QUERY_BLOCKED | reason=not_implemented")

                def system_stream():
                    yield (
                        "System-level information is not enabled yet. "
                        "This capability will be added soon."
                    )

                return system_stream()

            # ------------------------------------------------
            # REAL-TIME KNOWLEDGE (STRICT)
            # ------------------------------------------------
            if freshness == "real_time":
                logger.info(
                    "REAL_TIME_REQUEST | domain=%s | tool=web_search",
                    domain
                )

                tool_context = run_web_search(message)

                # --------------------------------------------
                # Web unavailable → hard stop (no LLM guessing)
                # --------------------------------------------
                if not tool_context:
                    logger.warning(
                        "REAL_TIME_BLOCKED | reason=web_unavailable | domain=%s | message=%s",
                        domain,
                        message
                    )

                    def fallback_stream():
                        yield (
                            "I cannot fetch up-to-date information right now "
                            "because live data access is unavailable. "
                            "If you want, I can explain general background "
                            "or help you enable live data access."
                        )

                    return fallback_stream()

                # --------------------------------------------
                # Web succeeded → LLM allowed with tool context
                # --------------------------------------------
                logger.info(
                    "REAL_TIME_TOOL_SUCCESS | domain=%s | forwarding_to_llm",
                    domain
                )

                return stream_llm_response(
                    message=message,
                    conversation_history=conversation_history,
                    tool_context=tool_context
                )

            # ------------------------------------------------
            # STATIC / TIMELESS KNOWLEDGE
            # ------------------------------------------------
            logger.info(
                "STATIC_REQUEST | forwarding_to_llm | message=%s",
                message
            )

            return stream_llm_response(
                message=message,
                conversation_history=conversation_history,
                tool_context=""
            )

        except Exception:
            logger.exception("TOOL_ROUTER_FAILED")

            def error_stream():
                yield "Something went wrong while processing your request."

            return error_stream()