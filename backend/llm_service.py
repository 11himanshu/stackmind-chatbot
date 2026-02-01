import os
import time
import requests
import re
import logging
import json
from typing import List, Dict, Generator
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
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
        logger.error(f"Web search failed: {e}")
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

# ============================================================
# SELF-CRITIQUE (HALLUCINATION GUARD)
# ============================================================

def self_critique(original_answer: str) -> str:
    critique_prompt = f"""
Review the answer below.

If it contains uncertainty, speculation, or assumptions,
add a brief clarifying sentence.
Do NOT change correct content.
Do NOT add new facts.

Answer:
{original_answer}
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "You improve factual accuracy."},
                    {"role": "user", "content": critique_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 200
            },
            timeout=8
        )
        response.raise_for_status()
        return original_answer + "\n\n" + response.json()["choices"][0]["message"]["content"]
    except Exception:
        return original_answer

# ============================================================
# GROQ (NON-STREAM)
# ============================================================

def call_groq_api(message: str, conversation_history: List[Dict]) -> str:
    logger.info("Calling Groq API")

    system_prompt = build_system_prompt(message)

    messages = [{"role": "system", "content": system_prompt}]
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

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=12
        )
        res.raise_for_status()
        answer = preprocess_response(res.json()["choices"][0]["message"]["content"])
        return self_critique(answer)
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "Something went wrong while generating the response."

# ============================================================
# GROQ STREAMING (UNCHANGED)
# ============================================================

def stream_groq_api(message: str, conversation_history: List[Dict]) -> Generator[str, None, None]:
    logger.info("Streaming from Groq")

    system_prompt = build_system_prompt(message)

    messages = [{"role": "system", "content": system_prompt}]
    for m in conversation_history[-10:]:
        messages.append({"role": m["role"], "content": m["message"]})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.6,
        "stream": True
    }

    try:
        with requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            },
            json=payload,
            stream=True,
            timeout=60
        ) as response:

            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                decoded = line.decode("utf-8").strip()
                if not decoded.startswith("data:"):
                    continue

                data = decoded.replace("data:", "").strip()
                if data == "[DONE]":
                    break

                try:
                    parsed = json.loads(data)
                    token = parsed["choices"][0]["delta"].get("content")
                    if token:
                        yield token
                except Exception:
                    continue

    except Exception as e:
        yield f"\n[Streaming error: {str(e)}]"

# ============================================================
# OLLAMA (SAFE, UNCHANGED)
# ============================================================

def call_ollama_api(message: str, conversation_history: List[Dict]) -> str:
    logger.info("Calling Ollama")

    prompt = build_system_prompt(message) + f"\n\nUser: {message}\nAssistant:"

    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2", "prompt": prompt, "stream": False},
            timeout=30
        )
        res.raise_for_status()
        return preprocess_response(res.json().get("response", ""))
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return "Something went wrong while generating the response."

# ============================================================
# PROVIDER ROUTER
# ============================================================

def get_llm_response(message: str, conversation_history: List[Dict]) -> str:
    logger.info(f"LLM provider selected: {LLM_PROVIDER}")

    if LLM_PROVIDER == "groq":
        return call_groq_api(message, conversation_history)
    if LLM_PROVIDER == "ollama":
        return call_ollama_api(message, conversation_history)

    return "Unknown LLM provider."

def get_llm_response_stream(message: str, conversation_history: List[Dict]):
    if LLM_PROVIDER == "groq":
        return stream_groq_api(message, conversation_history)

    if LLM_PROVIDER == "ollama":
        def fallback():
            yield call_ollama_api(message, conversation_history)
        return fallback()
