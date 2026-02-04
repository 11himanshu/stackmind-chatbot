import os
import time
from core.logger import get_logger
from llm.providers.groq import stream_groq_api, call_groq_api
from llm.providers.ollama import call_ollama_api

logger = get_logger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# Small delay to make streaming feel natural (seconds)
STREAM_THROTTLE_SECONDS = 0.03


def stream_llm_response(
    *,
    message: str,
    conversation_history: list[dict],
    tool_context: str = ""
):
    """
    Yield LLM response chunks.

    tool_context:
    - Output from external tools (web, youtube, etc.)
    - Injected as SYSTEM FACTS, not conversational context
    - Model must treat this as current, authoritative truth
    """

    logger.info(
        "LLM_PROVIDER_SELECTED | provider=%s | tool_context=%s",
        LLM_PROVIDER,
        bool(tool_context)
    )

    # --------------------------------------------------------
    # Inject tool facts as a HARD system constraint
    # --------------------------------------------------------
    if tool_context:
        logger.info("LLM_TOOL_FACTS_INJECTED")

        conversation_history = conversation_history + [
            {
                "role": "system",
                "message": (
                    "FACTS (current and verified):\n"
                    f"{tool_context}\n\n"
                    "Use these facts directly in your answer.\n"
                    "Do NOT mention tools, sources, or how these facts were obtained.\n"
                    "Do NOT add disclaimers about data freshness or model limitations."
                )
            }
        ]

    try:
        # ----------------------------------------------------
        # GROQ (STREAMING)
        # ----------------------------------------------------
        if LLM_PROVIDER == "groq":
            stream = stream_groq_api(message, conversation_history)

            for chunk in stream:
                if chunk:
                    yield chunk
                    time.sleep(STREAM_THROTTLE_SECONDS)

            return

        # ----------------------------------------------------
        # OLLAMA (NON-STREAM FALLBACK)
        # ----------------------------------------------------
        if LLM_PROVIDER == "ollama":
            def fallback():
                logger.info("OLLAMA_STREAM_FALLBACK_USED")
                yield call_ollama_api(message, conversation_history)
            return fallback()

        # ----------------------------------------------------
        # UNKNOWN PROVIDER
        # ----------------------------------------------------
        def error():
            logger.error("UNKNOWN_LLM_PROVIDER | provider=%s", LLM_PROVIDER)
            yield "Unknown LLM provider."

        return error()

    except Exception:
        logger.exception("LLM_STREAM_FAILED")

        def error():
            yield "LLM failed to generate a response."

        return error()