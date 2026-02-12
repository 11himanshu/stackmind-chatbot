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

from document_intelligence.schemas.document_index import DocumentIndex

logger = get_logger(__name__)

# ============================================================
# CONFIG
# ============================================================

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

DEFAULT_IMAGE_COUNT = 6
MAX_IMAGE_COUNT = 20
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 3

# ------------------------------------------------------------
# NUMBER WORDS
# ------------------------------------------------------------

_NUMBER_WORD_LIST = [
    "zero", "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen",
    "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen", "twenty",
]

NUMBER_WORDS = {
    word: i for i, word in enumerate(_NUMBER_WORD_LIST) if i > 0
}

QUANTITY_PHRASES = {
    "a": 1,
    "a couple of": 2,
    "couple of": 2,
    "a few": 3,
    "few": 3,
    "several": 5,
    "dozen": 12,
}

PRONOUNS = {
    "it", "this", "that", "they", "them",
    "those", "him", "her", "his", "hers"
}

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
    return any(re.search(p, message) for p in COPYRIGHT_PATTERNS)

# ============================================================
# IMAGE INTENT
# ============================================================

IMAGE_GENERATE_KEYWORDS = {
    "image", "images", "photo", "photos", "picture", "pictures",
    "pic", "pics", "show me", "with image", "with photo",
    "visual", "visualize", "visualise",
}

IMAGE_DESCRIBE_KEYWORDS = {
    "describe this",
    "describe the image",
    "describe the photo",
    "describe the picture",
    "describing the image",
    "describing the photo",
    "what is this",
    "what is this image",
    "what is this photo",
    "what am i seeing",
    "what am i looking at",
    "while describing",
    "while describing them",
}

def _wants_image_generation(message: str) -> bool:
    return any(k in message for k in IMAGE_GENERATE_KEYWORDS)

def _wants_image_description(message: str, history: List[Dict]) -> bool:
    if not any(k in message for k in IMAGE_DESCRIBE_KEYWORDS):
        return False
    return any(m.get("role") == "assistant" and m.get("images") for m in history)

def _wants_image_and_description(message: str) -> bool:
    return (
        _wants_image_generation(message)
        and any(k in message for k in IMAGE_DESCRIBE_KEYWORDS)
    )

# ============================================================
# SUBJECT EXTRACTION
# ============================================================

def _extract_named_entity(text: str) -> Optional[str]:
    text = re.sub(
        r"\b(give me|show me|tell me|about|with|and|a|an|the)\b",
        " ",
        text
    )
    text = re.sub(r"\s+", " ", text).strip()
    if not text or text in PRONOUNS:
        return None
    return text

# ============================================================
# IMAGE COUNT
# ============================================================

def _extract_image_count(message: str) -> int:
    num = re.search(r"\b(\d{1,2})\b", message)
    if num:
        return min(max(int(num.group(1)), 1), MAX_IMAGE_COUNT)

    for word, value in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\b", message):
            return min(value, MAX_IMAGE_COUNT)

    for phrase, value in QUANTITY_PHRASES.items():
        if phrase in message:
            return min(value, MAX_IMAGE_COUNT)

    return DEFAULT_IMAGE_COUNT

# ============================================================
# SUBJECT SANITATION
# ============================================================

def _sanitize_subject(subject: str) -> Optional[str]:
    if not subject:
        return None
    s = subject
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
    words = set(message.split())
    return bool(words & PRONOUNS) and len(words) <= 5

def _resolve_subject_from_history(history: List[Dict]) -> Optional[str]:
    for m in reversed(history):
        if m.get("role") == "user":
            candidate = _extract_subject_from_text(m["message"].lower())
            if candidate:
                return candidate
    return None

def _resolve_image_subject(message: str, history: List[Dict]) -> Optional[str]:
    explicit = _extract_subject_from_text(message)
    if explicit:
        return explicit
    entity = _extract_named_entity(message)
    if entity:
        return entity
    if _is_pronoun_only(message):
        return _resolve_subject_from_history(history)
    return None

# ============================================================
# UNSPLASH
# ============================================================

def _fetch_exact_unsplash_images(query: str, count: int) -> List[Dict]:
    images: List[Dict] = []
    page = 1
    while len(images) < count:
        per_page = min(30, count - len(images))
        r = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "query": query,
                "page": page,
                "per_page": per_page,
                "orientation": "landscape",
            },
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            timeout=6,
        )
        if r.status_code != 200:
            break
        for p in r.json().get("results", []):
            if len(images) >= count:
                break
            images.append({
                "url": p["urls"]["regular"],
                "alt": query,
                "credit": {
                    "name": p["user"]["name"],
                    "link": p["user"]["links"]["html"],
                },
            })
        page += 1
    return images

# ============================================================
# TOOL ROUTER
# ============================================================

class ToolRouter:

    @staticmethod
    def stream_response(
        *,
        message: str,
        conversation_history: List[Dict],
        document_index: Optional[DocumentIndex] = None
    ) -> Generator[str, None, None]:

        try:
            raw_message = message
            msg = re.sub(r"\s+", " ", message.lower()).strip()

            # ====================================================
            # DOCUMENT METADATA (DETERMINISTIC, NO LLM)
            # ====================================================

            if document_index is not None:
                if "how many blocks" in msg:
                    yield str(len(document_index.blocks))
                    return

                if "how many pages" in msg:
                    pages = {
                        b.location.page
                        for b in document_index.blocks
                        if b.location.page is not None
                    }
                    yield str(len(pages))
                    return

            # ====================================================
            # SAFETY
            # ====================================================

            if _is_copyrighted_request(msg):
                yield "I cannot provide full copyrighted lyrics."
                return

            # ====================================================
            # IMAGE + DESCRIPTION
            # ====================================================

            if _wants_image_and_description(msg):
                subject = _resolve_image_subject(msg, conversation_history)
                if not subject:
                    yield "I need a clearer subject to show images."
                    return

                requested_count = _extract_image_count(msg)
                images = _fetch_exact_unsplash_images(subject, requested_count)

                yield "__META__" + json.dumps({
                    "images": images,
                    "requested": requested_count,
                }) + "\n"

                for chunk in stream_llm_response(
                    message=raw_message,
                    conversation_history=conversation_history,
                    tool_context="",
                ):
                    yield chunk
                return

            if _wants_image_description(msg, conversation_history):
                for chunk in stream_llm_response(
                    message=raw_message,
                    conversation_history=conversation_history,
                    tool_context="",
                ):
                    yield chunk
                return

            if _wants_image_generation(msg):
                subject = _resolve_image_subject(msg, conversation_history)
                if not subject:
                    yield "I need a clearer subject to show an image."
                    return

                requested_count = _extract_image_count(msg)
                images = _fetch_exact_unsplash_images(subject, requested_count)

                yield "__META__" + json.dumps({
                    "images": images,
                    "requested": requested_count,
                }) + "\n"
                return

            # ====================================================
            # WEB SEARCH
            # ====================================================

            analysis = analyze_request(raw_message)
            if analysis.get("knowledge_freshness") == "real_time":
                ctx = run_web_search(raw_message)
                for c in stream_llm_response(
                    message=raw_message,
                    conversation_history=conversation_history,
                    tool_context=ctx,
                ):
                    yield c
                return

            # ====================================================
            # DEFAULT LLM
            # ====================================================

            for c in stream_llm_response(
                message=raw_message,
                conversation_history=conversation_history,
                tool_context="",
            ):
                yield c

        except Exception:
            logger.exception("TOOL_ROUTER_FAILED")
            yield "Something went wrong while processing your request."