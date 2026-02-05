from core.logger import get_logger
from llm.prompt import analyze_request
from llm.streaming import stream_llm_response
from tools.web_search import run_web_search

import os
import re
import json
import requests
from datetime import datetime
from typing import Generator, List, Dict, Optional

logger = get_logger(__name__)

# ============================================================
# CONFIG
# ============================================================

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

DEFAULT_IMAGE_COUNT = 5
MAX_IMAGE_COUNT = 6

NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
}

PRONOUNS = {"it", "this", "that", "they", "them", "those", "him", "her", "his", "hers"}

# ============================================================
# SAFETY
# ============================================================

COPYRIGHT_PATTERNS = [
    r"\blyrics\b",
    r"\bfull lyrics\b",
    r"\bgive lyrics\b",
    r"\bwrite lyrics\b",
    r"\bsong lyrics\b",
]

def _is_copyrighted_request(message: str) -> bool:
    return any(re.search(p, message.lower()) for p in COPYRIGHT_PATTERNS)

# ============================================================
# IMAGE INTENT
# ============================================================

IMAGE_GENERATE_KEYWORDS = {
    "image", "images", "photo", "photos", "picture", "pictures",
    "pic", "pics", "show me", "with image", "with photo",
    "visual", "visualize", "visualise",
}

IMAGE_DESCRIBE_KEYWORDS = {
    "describe this", "describe the image", "describe the photo",
    "what is this", "what is this image", "what is this photo",
    "what am i seeing", "what am i looking at",
}

def _wants_image_generation(message: str) -> bool:
    return any(k in message.lower() for k in IMAGE_GENERATE_KEYWORDS)

def _wants_image_description(message: str, history: List[Dict]) -> bool:
    if not any(k in message.lower() for k in IMAGE_DESCRIBE_KEYWORDS):
        return False
    return any(m.get("role") == "assistant" and m.get("images") for m in history)

def _extract_named_entity(text: str) -> Optional[str]:
    """
    Extracts the most likely concrete subject (named entity).
    Works for:
    - people
    - animals
    - places
    - objects
    - brands

    Conservative by design:
    - requires noun-like phrases
    - avoids pronouns
    """

    text = text.lower()

    # remove instruction noise
    text = re.sub(
        r"\b(give me|show me|tell me|about|with|and|a|an|the)\b",
        " ",
        text
    )

    # collapse spaces
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return None

    # reject pure pronouns
    if text in PRONOUNS:
        return None

    # reject very short garbage
    if len(text.split()) == 1 and text in {"him", "her", "it", "this", "that"}:
        return None

    return text

# ============================================================
# IMAGE COUNT
# ============================================================

def _extract_image_count(message: str) -> int:
    msg = message.lower()

    num = re.search(r"\b(\d+)\s+(image|images|photo|photos|picture|pictures|pics)\b", msg)
    if num:
        return min(max(int(num.group(1)), 1), MAX_IMAGE_COUNT)

    for word, value in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\s+(image|images|photo|photos|picture|pictures|pics)\b", msg):
            return value

    return DEFAULT_IMAGE_COUNT

# ============================================================
# SUBJECT SANITATION (CRITICAL)
# ============================================================

def _sanitize_subject(subject: str) -> Optional[str]:
    if not subject:
        return None

    s = subject.lower()

    s = re.sub(r"\b(with|using|having)\b.*", "", s)
    s = re.sub(r"\b(image|images|photo|photos|picture|pictures|pic|pics)\b", "", s)
    s = re.sub(r"\b(show me|tell me|give me|about)\b", "", s)
    s = re.sub(r"\b(one|two|three|four|five|six|\d+)\b", "", s)

    s = s.strip()
    return s if s and s not in PRONOUNS else None

def _extract_subject_from_text(text: str) -> Optional[str]:
    patterns = [
        r"image of (.+)",
        r"images of (.+)",
        r"photo of (.+)",
        r"picture of (.+)",
        r"show me (.+)",
        r"tell me about (.+)",
        r"(.+) with (an |a )?(image|photo|picture)",
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return _sanitize_subject(m.group(1))

    return None

# ============================================================
# PRONOUN CONTROL
# ============================================================

def _is_pronoun_only(message: str) -> bool:
    words = set(message.lower().split())
    return bool(words & PRONOUNS) and len(words) <= 5

def _resolve_subject_from_history(history: List[Dict]) -> Optional[str]:
    for m in reversed(history):
        if m.get("role") == "user":
            candidate = _extract_subject_from_text(m["message"].lower())
            if candidate:
                return candidate
    return None

def _resolve_image_subject(
    message: str,
    history: List[Dict],
) -> Optional[str]:

    msg_l = message.lower()

    # 1. Explicit image grammar
    explicit = _extract_subject_from_text(msg_l)
    explicit = _sanitize_subject(explicit) if explicit else None
    if explicit:
        return explicit

    # 2. Named entity in SAME message (CRITICAL FIX)
    entity = _extract_named_entity(msg_l)
    if entity and entity not in PRONOUNS:
        logger.info("NAMED_ENTITY_DETECTED | %s", entity)
        return entity

    # 3. Pronoun → resolve from history (STRICT)
    if _is_pronoun_only(msg_l):
        logger.info("PRONOUN_DETECTED | attempting scoped resolution")
        resolved = _resolve_subject_from_history(history)
        if resolved:
            return resolved

    logger.warning("IMAGE_SUBJECT_UNRESOLVED")
    return None

# ============================================================
# UNSPLASH
# ============================================================

def _resolve_unsplash_images(query: str, count: int) -> List[Dict]:
    if not UNSPLASH_ACCESS_KEY:
        logger.error("UNSPLASH_ACCESS_KEY missing")
        return []

    try:
        r = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": count, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            timeout=6,
        )

        if r.status_code != 200:
            logger.warning("UNSPLASH_FAILED | query=%s | status=%s", query, r.status_code)
            return []

        images = []
        for p in r.json().get("results", [])[:count]:
            images.append({
                "url": p["urls"]["regular"],
                "alt": query,
                "credit": {
                    "name": p["user"]["name"],
                    "link": p["user"]["links"]["html"],
                },
            })

        return images

    except Exception:
        logger.exception("UNSPLASH_EXCEPTION | query=%s", query)
        return []

# ============================================================
# TOOL ROUTER
# ============================================================

class ToolRouter:

    @staticmethod
    def stream_response(
        *,
        message: str,
        conversation_history: List[Dict],
    ) -> Generator[str, None, None]:

        try:
            # ---------- SAFETY ----------
            if _is_copyrighted_request(message):
                yield "I cannot provide full copyrighted lyrics."
                return

            msg_l = message.lower()

            # ---------- SYSTEM ----------
            if any(k in msg_l for k in ("time now", "current time", "date today", "today's date")):
                now = datetime.now()
                yield f"Today is {now.strftime('%B %d, %Y')}. The current time is {now.strftime('%H:%M')}."
                return

            # ---------- IMAGE DESCRIBE ----------
            if _wants_image_description(message, conversation_history):
                logger.info("IMAGE_DESCRIBE_MODE")
                for chunk in stream_llm_response(
                    message="Describe the image the user is currently viewing.",
                    conversation_history=conversation_history,
                    tool_context="",
                ):
                    yield chunk
                return

            # ---------- IMAGE GENERATE ----------
            if _wants_image_generation(message):
                subject = _resolve_image_subject(message, conversation_history)
                if not subject:
                    yield "I need a clearer subject to show an image."
                    return

                count = _extract_image_count(message)
                images = _resolve_unsplash_images(subject, count)

                logger.info(
                    "IMAGE_GENERATE | subject=%s | count=%d | images=%d",
                    subject, count, len(images)
                )

                yield "__META__" + json.dumps({"images": images}) + "\n"

                if any(k in msg_l for k in ("tell me", "about", "describe")):
                    for chunk in stream_llm_response(
                        message=message,
                        conversation_history=conversation_history,
                        tool_context="",
                    ):
                        yield chunk
                return

            # ---------- TEXT / WEB ----------
            analysis = analyze_request(message)
            if analysis.get("knowledge_freshness") == "real_time":
                ctx = run_web_search(message)
                if not ctx:
                    yield "I could not retrieve live information right now."
                    return
                for c in stream_llm_response(message, conversation_history, ctx):
                    yield c
                return

            for c in stream_llm_response(message, conversation_history, ""):
                yield c

        except Exception:
            logger.exception("TOOL_ROUTER_FAILED")
            yield "Something went wrong while processing your request."