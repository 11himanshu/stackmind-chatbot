from typing import Dict, List
from pydantic import BaseModel, Field, validator

from .block import Block


class DocumentIndex(BaseModel):
    """
    Lightweight cached representation of a document.

    Guarantees:
    - Immutable block order
    - Stable block lookup
    - No reasoning, no LLM output
    - Safe for patching & references
    """

    document_id: str = Field(..., description="Internal document id")
    file_name: str
    file_type: str  # pdf, docx, xlsx, pptx

    blocks: List[Block]

    # block_id -> index in blocks list
    block_map: Dict[str, int] = Field(
        default_factory=dict,
        description="Fast lookup table"
    )

    # =========================================================
    # Validation
    # =========================================================

    @validator("document_id")
    def document_id_not_empty(cls, v: str):
        if not v.strip():
            raise ValueError("document_id cannot be empty")
        return v

    @validator("blocks")
    def blocks_not_empty(cls, v: List[Block]):
        if not v:
            raise ValueError("DocumentIndex must contain at least one block")
        return v

    # =========================================================
    # Index building
    # =========================================================

    def build_index(self) -> None:
        """
        Build internal lookup map.

        Must be called exactly once after ingest.
        """
        self.block_map = {}

        for idx, block in enumerate(self.blocks):
            if block.block_id in self.block_map:
                raise ValueError(
                    f"Duplicate block_id detected: {block.block_id}"
                )
            self.block_map[block.block_id] = idx

    # =========================================================
    # Safe accessors
    # =========================================================

    def get_block(self, block_id: str) -> Block:
        """
        Resolve a block safely.
        """
        idx = self.block_map.get(block_id)
        if idx is None:
            raise KeyError(f"Block not found: {block_id}")
        return self.blocks[idx]

    def has_block(self, block_id: str) -> bool:
        """
        Fast existence check (no exception).
        """
        return block_id in self.block_map