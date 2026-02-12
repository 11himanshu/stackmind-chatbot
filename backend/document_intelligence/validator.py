from typing import List

from core.logger import get_logger
from document_intelligence.schemas.block import Block

logger = get_logger(__name__)


class InstructionValidator:
    """
    Validates whether an analysis / patch request is safe and scoped.

    Responsibilities:
    - Ensure blocks are provided
    - Prevent full-document mutation by default
    - Enforce explicit references for patch operations
    """

    def validate(self, *, intent, blocks: List[Block]) -> None:
        """
        Raise if instruction is unsafe or ambiguous.
        """

        if not blocks:
            logger.error("VALIDATION_FAILED | no_blocks_resolved")
            raise ValueError("No document blocks resolved for this request")

        # -------------------------------------------------
        # Patch intent must be explicitly scoped
        # -------------------------------------------------
        if intent.intent_type == "patch":
            if not intent.block_ids:
                logger.error(
                    "VALIDATION_FAILED | patch_without_block_ids"
                )
                raise ValueError(
                    "Patch operations require explicit block references"
                )

        # -------------------------------------------------
        # Analyze intent: allow but log scope
        # -------------------------------------------------
        if intent.intent_type == "analyze":
            logger.info(
                "VALIDATION_ANALYZE | blocks=%d",
                len(blocks),
            )

        # -------------------------------------------------
        # Read intent: always allowed
        # -------------------------------------------------
        if intent.intent_type == "read":
            logger.debug(
                "VALIDATION_READ | blocks=%d",
                len(blocks),
            )

        logger.debug(
            "VALIDATION_OK | intent=%s | blocks=%d",
            intent.intent_type,
            len(blocks),
        )