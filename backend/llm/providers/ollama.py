import time
import requests
from typing import List, Dict

from core.logger import get_logger
from llm.prompt import build_system_prompt
from tools.safety import preprocess_response

logger = get_logger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 0.5


# ============================================================
# INTERNAL: RETRY DECISION
# ============================================================

def _is_retryable_error(exc: Exception) -> bool:
    """
    Decide whether an Ollama error is retryable.

    Retry only on transient failures:
    - service not up yet
    - network issues
    - timeouts
    - 5xx responses
    """

    if isinstance(exc, requests.exceptions.Timeout):
        return True

    if isinstance(exc, requests.exceptions.ConnectionError):
        return True

    if isinstance(exc, requests.exceptions.HTTPError):
        status = exc.response.status_code if exc.response else None
        if status and 500 <= status < 600:
            return True

    return False


def _sleep_with_backoff(attempt: int):
    delay = BASE_BACKOFF_SECONDS * (2 ** attempt)
    logger.info("OLLAMA_BACKOFF_SLEEP | seconds=%s", delay)
    time.sleep(delay)


# ============================================================
# OLLAMA (NON-STREAM) WITH BACKOFF
# ============================================================

def call_ollama_api(message: str, conversation_history: List[Dict]) -> str:
    logger.info("OLLAMA_CALL_START")

    prompt = build_system_prompt(message) + f"\n\nUser: {message}\nAssistant:"

    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    }

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(
                "OLLAMA_CALL_ATTEMPT | attempt=%s",
                attempt + 1
            )

            res = requests.post(
                OLLAMA_API_URL,
                json=payload,
                timeout=30
            )
            res.raise_for_status()

            return preprocess_response(
                res.json().get("response", "")
            )

        except Exception as exc:
            logger.warning(
                "OLLAMA_CALL_FAILED | attempt=%s | error=%s",
                attempt + 1,
                type(exc).__name__
            )

            if attempt == MAX_RETRIES - 1 or not _is_retryable_error(exc):
                logger.exception("OLLAMA_CALL_ABORTED")
                break

            _sleep_with_backoff(attempt)

    return "Something went wrong while generating the response."