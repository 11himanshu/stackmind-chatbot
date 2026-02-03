import requests
from typing import List, Dict
from core.logger import get_logger
from llm.prompt import build_system_prompt
from tools.safety import preprocess_response

logger = get_logger(__name__)


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
        logger.error("Ollama error: %s", e)
        return "Something went wrong while generating the response."