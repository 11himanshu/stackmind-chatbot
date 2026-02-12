from typing import List, Dict, Any
from pydantic import BaseModel, Field

from core.logger import get_logger
from document_intelligence.schemas.block import Block
from document_intelligence.intent_router import Intent, PatchMode

logger = get_logger(__name__)


# =========================================================
# Patch Plan Schema
# =========================================================

class PatchOperation(BaseModel):
    """
    Atomic patch instruction.
    """

    block_id: str
    operation: str = Field(
        ...,
        description="replace | append | regenerate"
    )
    instruction: str
    location: Dict[str, Any]


class PatchPlan(BaseModel):
    """
    Output-only plan.

    This is what an executor would later apply.
    """

    document_id: str
    operations: List[PatchOperation]
    safe: bool = True
    notes: str = ""


# =========================================================
# Planner
# =========================================================

class PatchPlanner:
    """
    Produces deterministic patch plans.

    Never mutates blocks.
    Never touches files.
    """

    def plan(
        self,
        *,
        document_id: str,
        intent: Intent,
        blocks: List[Block],
    ) -> PatchPlan:

        # -----------------------------------------------------
        # Validate intent
        # -----------------------------------------------------
        if str(intent.intent_type).lower() != "patch":
            raise ValueError("PatchPlanner called with non-patch intent")

        if not blocks:
            raise ValueError("Patch requires resolved target blocks")

        operations: List[PatchOperation] = []

        for block in blocks:
            operation = (
                "replace"
                if intent.patch_mode == PatchMode.SURGICAL
                else "regenerate"
            )

            operations.append(
                PatchOperation(
                    block_id=block.block_id,
                    operation=operation,
                    instruction=intent.patch_instruction or "",
                    location=block.location.dict(exclude_none=True),
                )
            )

        if not operations:
            logger.warning(
                "PATCH_PLAN_EMPTY | doc_id=%s",
                document_id
            )

        logger.info(
            "PATCH_PLAN_CREATED | doc_id=%s | ops=%d",
            document_id,
            len(operations),
        )

        return PatchPlan(
            document_id=document_id,
            operations=operations,
            safe=True,
            notes="Surgical patch only. No regeneration unless explicitly requested.",
        )