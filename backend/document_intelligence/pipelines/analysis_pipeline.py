from typing import Dict, Any, List

from core.logger import get_logger
from document_intelligence.cache.index_cache import DocumentIndexCache
from document_intelligence.schemas.block import Block, BlockType
from document_intelligence.intent_router import IntentRouter, IntentType
from document_intelligence.patch_planner import PatchPlanner
from document_intelligence.validator import InstructionValidator

logger = get_logger(__name__)

# ---------------------------------------------------------
# Shared cache (process-wide)
# ---------------------------------------------------------
_INDEX_CACHE = DocumentIndexCache()


class AnalysisPipeline:
    """
    High-level document analysis pipeline.

    Responsibilities:
    - Load indexed document from cache
    - Interpret user intent
    - Resolve referenced blocks only
    - Perform deep analysis on demand
    - NEVER mutate document directly
    """

    def __init__(self):
        self.cache = _INDEX_CACHE
        self.intent_router = IntentRouter()
        self.patch_planner = PatchPlanner()
        self.validator = InstructionValidator()

    # =========================================================
    # Public entrypoint
    # =========================================================

    def run(
        self,
        *,
        document_id: str,
        user_query: str,
    ) -> Dict[str, Any]:
        """
        Execute analysis for a given document and user request.
        """

        logger.info(
            "ANALYSIS_START | doc_id=%s | query=%s",
            document_id,
            user_query,
        )

        if not self.cache.exists(document_id):
            logger.error("ANALYSIS_DOC_NOT_INDEXED | doc_id=%s", document_id)
            raise KeyError(f"Document not indexed: {document_id}")

        index = self.cache.get(document_id)

        # -----------------------------------------------------
        # 1️⃣ Determine intent
        # -----------------------------------------------------
        intent = self.intent_router.route(user_query)

        logger.debug(
            "ANALYSIS_INTENT | doc_id=%s | intent=%s",
            document_id,
            intent.intent_type,
        )

        # -----------------------------------------------------
        # 2️⃣ Resolve relevant blocks
        # -----------------------------------------------------
        blocks = self._resolve_blocks(index.blocks, intent)

        logger.debug(
            "ANALYSIS_BLOCKS_RESOLVED | count=%d",
            len(blocks),
        )

        # -----------------------------------------------------
        # 3️⃣ Validate scope
        # -----------------------------------------------------
        self.validator.validate(intent=intent, blocks=blocks)

        # -----------------------------------------------------
        # 4️⃣ Dispatch by intent
        # -----------------------------------------------------
        if intent.intent_type == IntentType.READ:
            return self._read(blocks)

        if intent.intent_type == IntentType.ANALYZE:
            return self._analyze(blocks)

        if intent.intent_type == IntentType.PATCH:
            return self._plan_patch(
                document_id=document_id,
                intent=intent,
                blocks=blocks,
            )

        raise ValueError(f"Unsupported intent: {intent.intent_type}")

    # =========================================================
    # Internal handlers
    # =========================================================

    def _resolve_blocks(
        self,
        all_blocks: List[Block],
        intent,
    ) -> List[Block]:
        """
        Resolve only blocks explicitly referenced or safely inferred.
        """

        if intent.block_ids:
            return [
                b for b in all_blocks
                if b.block_id in intent.block_ids
            ]

        # Safe default: first few TEXT blocks only
        return [
            b for b in all_blocks
            if b.type == BlockType.TEXT
        ][:3]

    # ---------------------------------------------------------

    def _read(self, blocks: List[Block]) -> Dict[str, Any]:
        """
        Non-destructive read.
        """

        logger.info(
            "ANALYSIS_READ | blocks=%d",
            len(blocks),
        )

        return {
            "mode": "read",
            "blocks": [
                {
                    "block_id": b.block_id,
                    "type": b.type.value,
                    "content": b.content,
                    "location": b.location.dict(),
                }
                for b in blocks
            ],
        }

    # ---------------------------------------------------------

    def _analyze(self, blocks: List[Block]) -> Dict[str, Any]:
        """
        Deep analysis (tables, reasoning, images on demand).
        """

        logger.info(
            "ANALYSIS_DEEP | blocks=%d",
            len(blocks),
        )

        analysis_units = []

        for block in blocks:
            if block.type == BlockType.IMAGE:
                analysis_units.append(
                    {
                        "block_id": block.block_id,
                        "type": "image",
                        "analysis": "vision_required_on_demand",
                        "reference": block.content,
                    }
                )
            else:
                analysis_units.append(
                    {
                        "block_id": block.block_id,
                        "type": block.type.value,
                        "content": block.content,
                    }
                )

        return {
            "mode": "analysis",
            "analysis_units": analysis_units,
        }

    # ---------------------------------------------------------

    def _plan_patch(
        self,
        *,
        document_id: str,
        intent,
        blocks: List[Block],
    ) -> Dict[str, Any]:
        """
        Create a safe patch plan WITHOUT applying it.
        """

        logger.info(
            "ANALYSIS_PATCH_PLAN | doc_id=%s | blocks=%d",
            document_id,
            len(blocks),
        )

        plan = self.patch_planner.create_plan(
            document_id=document_id,
            intent=intent,
            blocks=blocks,
        )

        return {
            "mode": "patch_plan",
            "plan": plan.dict(),
        }