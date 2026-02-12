from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from core.logger import get_logger

logger = get_logger(__name__)


# =========================================================
# Intent types
# =========================================================

class IntentType(str, Enum):
    READ = "read"
    ANALYZE = "analyze"
    PATCH = "patch"


class PatchMode(str, Enum):
    SURGICAL = "surgical"     # change specific part only
    REGENERATE = "regenerate" # rewrite entire block
    APPEND = "append"         # add new content


# =========================================================
# Intent output (STRICT CONTRACT)
# =========================================================

class Intent(BaseModel):
    """
    Canonical interpretation of user intent.

    This object decides everything downstream.
    """

    intent_type: IntentType

    # Explicit block scope
    referenced_block_ids: List[str] = Field(default_factory=list)

    # Optional hints
    page_hint: Optional[int] = None
    section_hint: Optional[str] = None

    # Patch-only fields
    patch_mode: Optional[PatchMode] = None
    patch_instruction: Optional[str] = None

    # Vision
    requires_vision: bool = False

    # Safety
    allow_full_document: bool = False


# =========================================================
# Router
# =========================================================

class IntentRouter:
    """
    Determines WHAT the user wants to do.
    Not HOW.
    """

    def route(
        self,
        *,
        user_query: str,
        referenced_block_ids: Optional[List[str]] = None,
    ) -> Intent:
        """
        Lightweight rule-based routing.

        This is intentionally conservative.
        """

        text = user_query.lower().strip()
        referenced_block_ids = referenced_block_ids or []

        # -------------------------------
        # PATCH intent
        # -------------------------------
        if any(k in text for k in ["change", "modify", "replace", "update", "edit"]):
            logger.debug("INTENT_ROUTED | type=PATCH")

            return Intent(
                intent_type=IntentType.PATCH,
                referenced_block_ids=referenced_block_ids,
                patch_mode=PatchMode.SURGICAL,
                patch_instruction=user_query,
                requires_vision=False,
                allow_full_document=False,
            )

        # -------------------------------
        # ANALYZE intent
        # -------------------------------
        if any(k in text for k in ["analyze", "explain", "summarize", "compare", "extract"]):
            logger.debug("INTENT_ROUTED | type=ANALYZE")

            return Intent(
                intent_type=IntentType.ANALYZE,
                referenced_block_ids=referenced_block_ids,
                requires_vision="image" in text or "screenshot" in text,
                allow_full_document=False,
            )

        # -------------------------------
        # READ intent (default)
        # -------------------------------
        logger.debug("INTENT_ROUTED | type=READ")

        return Intent(
            intent_type=IntentType.READ,
            referenced_block_ids=referenced_block_ids,
            requires_vision=False,
            allow_full_document=False,
        )