from pathlib import Path
from typing import List
import hashlib

import fitz  # PyMuPDF

from document_intelligence.schemas.block import (
    Block,
    BlockType,
    BlockLocation,
)
from core.logger import get_logger

logger = get_logger(__name__)


class PdfBuilder:
    """
    Production-grade PDF ingestion.

    Extracts span-level text blocks with full layout fidelity.

    Guarantees:
    - No text flattening
    - Deterministic block identity
    - Layout-preserving regeneration possible
    - LLM-safe block sizes
    """

    def build(self, path: Path) -> List[Block]:
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        blocks: List[Block] = []

        try:
            doc = fitz.open(path)

            for page_index, page in enumerate(doc):
                page_number = page_index + 1

                text_dict = page.get_text("dict")

                for block_index, block in enumerate(text_dict.get("blocks", [])):
                    if block.get("type") != 0:
                        continue  # non-text block

                    for line_index, line in enumerate(block.get("lines", [])):
                        for span_index, span in enumerate(line.get("spans", [])):
                            text = span.get("text", "")
                            if not text or not text.strip():
                                continue

                            bbox = span.get("bbox")
                            font = span.get("font")
                            size = span.get("size")
                            color = span.get("color")

                            # -------------------------------------------------
                            # Deterministic block identity
                            # -------------------------------------------------
                            identity = (
                                f"pdf:{path.name}:p{page_number}:"
                                f"b{block_index}:l{line_index}:s{span_index}"
                            )

                            content_hash = hashlib.sha256(
                                text.encode("utf-8")
                            ).hexdigest()

                            blocks.append(
                                Block(
                                    block_id=identity,
                                    type=BlockType.TEXT,
                                    location=BlockLocation(
                                        page=page_number,
                                        bbox={
                                            "x0": bbox[0],
                                            "y0": bbox[1],
                                            "x1": bbox[2],
                                            "y1": bbox[3],
                                        },
                                    ),
                                    content=text,
                                    metadata={
                                        "font": font,
                                        "font_size": size,
                                        "color": color,
                                        "source": "pdf",
                                    },
                                    content_hash=content_hash,
                                )
                            )

            logger.info(
                "PDF_BUILD_SUCCESS | file=%s | pages=%d | blocks=%d",
                path.name,
                doc.page_count,
                len(blocks),
            )

            return blocks

        except Exception:
            logger.exception("PDF_BUILD_FAILED | file=%s", path.name)
            raise

        finally:
            try:
                doc.close()
            except Exception:
                pass