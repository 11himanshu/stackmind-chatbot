import os
from core.logger import get_logger
from llm.providers.groq import stream_groq_api, call_groq_api
from llm.providers.ollama import call_ollama_api

logger = get_logger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")


def stream_llm_response(
    *,
    message: str,
    conversation_history: list[dict]
):
    """
    Yield LLM response chunks.
    """

    logger.info("LLM_PROVIDER_SELECTED | %s", LLM_PROVIDER)

    if LLM_PROVIDER == "groq":
        return stream_groq_api(message, conversation_history)

    if LLM_PROVIDER == "ollama":
        def fallback():
            yield call_ollama_api(message, conversation_history)
        return fallback()

    def error():
        yield "Unknown LLM provider."

    return error()