import os
import json
import requests
from typing import List, Dict, Generator
from dotenv import load_dotenv

from core.logger import get_logger
from llm.prompt import build_system_prompt
from tools.safety import preprocess_response

load_dotenv()
logger = get_logger(__name__)


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
        answer = res.json()["choices"][0]["message"]["content"]
        return preprocess_response(answer)

    except Exception as e:
        logger.error("Groq error: %s", e)
        return "Something went wrong while generating the response."


# ============================================================
# GROQ STREAMING
# ============================================================

def stream_groq_api(
    message: str,
    conversation_history: List[Dict]
) -> Generator[str, None, None]:

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