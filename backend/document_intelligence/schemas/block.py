from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator


class BlockType(str, Enum):
    """
    Canonical block types.

    These types are stable and must NEVER be renamed once data is cached.
    """
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    FORMULA = "formula"
    SLIDE = "slide"
    CELL = "cell"


class BlockLocation(BaseModel):
    """
    Precise location of a block inside a document.

    Used for:
    - Surgical patching (edit only what is referenced)
    - Anchoring LLM reasoning
    - Image region references
    """

    # PDF / image documents
    page: Optional[int] = None

    # PPT
    slide: Optional[int] = None

    # Excel
    sheet: Optional[str] = None
    row: Optional[int] = None
    column: Optional[int] = None

    # Image bounding box (relative or absolute, decided by builder)
    bbox: Optional[Dict[str, float]] = None


class Block(BaseModel):
    """
    Canonical block representation.

    Invariants:
    - This is the ONLY structure cached in DB
    - This is the ONLY structure referenced by the LLM
    - This is the ONLY structure eligible for patching

    Builders MUST populate this model exactly.
    """

    # Stable unique identifier for references and patches
    block_id: str = Field(..., description="Stable unique block id")

    # Semantic type of the block
    type: BlockType

    # Exact location inside the source document
    location: BlockLocation

    # Raw content:
    # - text: str
    # - table: structured dict / list
    # - image: None (image lives on disk, metadata holds pointer)
    # - formula: str
    content: Any

    # Non-semantic metadata (never sent blindly to LLM)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Deterministic hash of content.
    # MUST be computed using a stable hashing strategy (sha256 over normalized content).
    # Used for cache validation and safe patching.
    content_hash: str

    @validator("block_id")
    def block_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("block_id cannot be empty")
        return v

    @validator("content_hash")
    def content_hash_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("content_hash cannot be empty")
        return v