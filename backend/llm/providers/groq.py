import os
import json
import time
import threading
import requests
from typing import List, Dict, Generator
from dotenv import load_dotenv

from core.logger import get_logger
from llm.prompt import build_system_prompt
from tools.safety import preprocess_response

load_dotenv()
logger = get_logger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Retry config
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1

# Circuit breaker config
FAILURE_THRESHOLD = 5
COOLDOWN_SECONDS = 60


# ============================================================
# CIRCUIT BREAKER (PROCESS-LOCAL)
# ============================================================

class _CircuitBreaker:
    def __init__(self):
        self.failures = 0
        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN
        self.opened_at = None
        self.lock = threading.Lock()

    def allow_request(self) -> bool:
        with self.lock:
            if self.state == "OPEN":
                elapsed = time.time() - self.opened_at
                if elapsed >= COOLDOWN_SECONDS:
                    self.state = "HALF_OPEN"
                    logger.info("GROQ_CIRCUIT_HALF_OPEN")
                    return True

                logger.warning(
                    "GROQ_CIRCUIT_OPEN | retry_after=%ss",
                    int(COOLDOWN_SECONDS - elapsed)
                )
                return False

            return True

    def record_success(self):
        with self.lock:
            if self.state != "CLOSED":
                logger.info("GROQ_CIRCUIT_CLOSED")

            self.failures = 0
            self.state = "CLOSED"
            self.opened_at = None

    def record_failure(self):
        with self.lock:
            self.failures += 1

            if self.failures >= FAILURE_THRESHOLD:
                self.state = "OPEN"
                self.opened_at = time.time()
                logger.error(
                    "GROQ_CIRCUIT_OPENED | failures=%s",
                    self.failures
                )


_circuit = _CircuitBreaker()


# ============================================================
# INTERNAL: RETRY DECISION
# ============================================================

def _is_retryable_error(exc: Exception) -> bool:
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
    logger.info("GROQ_BACKOFF_SLEEP | seconds=%s", delay)
    time.sleep(delay)


# ============================================================
# HARD BEHAVIOR CONSTRAINT (CRITICAL FIX)
# ============================================================

def _build_behavior_guard() -> str:
    """
    This guard prevents all generic LLM disclaimers and
    forces image-capable, assistant-like behavior.
    """
    return (
        "IMPORTANT RESPONSE RULES:\n"
        "- You are NOT a text-based AI. Never say that.\n"
        "- Never mention model limitations, training data, or access constraints.\n"
        "- Never suggest checking external websites or apps.\n"
        "- If the user asks for images, you may describe them or request image search implicitly.\n"
        "- Do NOT refuse image-related requests unless explicitly blocked by safety rules.\n"
        "- Do NOT include disclaimers like 'I cannot display images'.\n"
        "- Answer directly and confidently.\n"
    )


# ============================================================
# GROQ (NON-STREAM)
# ============================================================

def call_groq_api(message: str, conversation_history: List[Dict]) -> str:
    if not _circuit.allow_request():
        return "The service is temporarily unavailable. Please try again shortly."

    logger.info("GROQ_CALL_START")

    system_prompt = build_system_prompt(message)
    behavior_guard = _build_behavior_guard()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": behavior_guard},
    ]

    for m in conversation_history[-10:]:
        messages.append({"role": m["role"], "content": m["message"]})

    messages.append({"role": "user", "content": message})

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.6,
        "presence_penalty": 0.4,
        "frequency_penalty": 0.3,
        "max_tokens": 1024
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }

    for attempt in range(MAX_RETRIES):
        try:
            logger.info("GROQ_CALL_ATTEMPT | attempt=%s", attempt + 1)

            res = requests.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=12
            )
            res.raise_for_status()

            _circuit.record_success()

            answer = res.json()["choices"][0]["message"]["content"]
            return preprocess_response(answer)

        except Exception as exc:
            logger.warning(
                "GROQ_CALL_FAILED | attempt=%s | error=%s",
                attempt + 1,
                type(exc).__name__
            )

            if attempt == MAX_RETRIES - 1 or not _is_retryable_error(exc):
                _circuit.record_failure()
                logger.exception("GROQ_CALL_ABORTED")
                break

            _sleep_with_backoff(attempt)

    return "Something went wrong while generating the response."


# ============================================================
# GROQ STREAMING
# ============================================================

def stream_groq_api(
    message: str,
    conversation_history: List[Dict]
) -> Generator[str, None, None]:

    if not _circuit.allow_request():
        yield "The service is temporarily unavailable. Please try again shortly."
        return

    logger.info("GROQ_STREAM_START")

    system_prompt = build_system_prompt(message)
    behavior_guard = _build_behavior_guard()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": behavior_guard},
    ]

    for m in conversation_history[-10:]:
        messages.append({"role": m["role"], "content": m["message"]})

    messages.append({"role": "user", "content": message})

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.6,
        "stream": True
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }

    for attempt in range(MAX_RETRIES):
        try:
            logger.info("GROQ_STREAM_ATTEMPT | attempt=%s", attempt + 1)

            with requests.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                stream=True,
                timeout=60
            ) as response:

                response.raise_for_status()
                _circuit.record_success()

                for line in response.iter_lines():
                    if not line:
                        continue

                    decoded = line.decode("utf-8").strip()
                    if not decoded.startswith("data:"):
                        continue

                    data = decoded.replace("data:", "").strip()
                    if data == "[DONE]":
                        return

                    try:
                        parsed = json.loads(data)
                        token = parsed["choices"][0]["delta"].get("content")
                        if token:
                            yield token
                    except Exception:
                        continue

                return

        except Exception as exc:
            logger.warning(
                "GROQ_STREAM_FAILED | attempt=%s | error=%s",
                attempt + 1,
                type(exc).__name__
            )

            if attempt == MAX_RETRIES - 1 or not _is_retryable_error(exc):
                _circuit.record_failure()
                logger.exception("GROQ_STREAM_ABORTED")
                yield "\n[Streaming error. Please try again.]"
                return

            _sleep_with_backoff(attempt)