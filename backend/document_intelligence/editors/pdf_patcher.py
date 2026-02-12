from pathlib import Path
from typing import Dict, Any

import fitz  # PyMuPDF

from core.logger import get_logger
from document_intelligence.schemas.block import Block

logger = get_logger(__name__)


class PdfPatcher:
    """
    Applies safe, surgical patches to an existing PDF.

    Guarantees:
    - Only specified content is modified
    - No full regeneration
    - No layout-wide rewrite
    - Fails fast if text not found or ambiguous
    """

    def apply_patch(
        self,
        *,
        input_path: Path,
        output_path: Path,
        block: Block,
        instruction: Dict[str, Any],
    ) -> None:
        """
        Apply a single patch instruction to a PDF.

        instruction must contain:
        - old_text
        - new_text
        """

        if not input_path.exists():
            raise FileNotFoundError(f"PDF not found: {input_path}")

        old_text = instruction.get("old_text")
        new_text = instruction.get("new_text")

        if not old_text or not new_text:
            raise ValueError("Patch instruction missing old_text or new_text")

        page_number = block.location.page
        if page_number is None:
            raise ValueError("PDF patch requires page number")

        logger.info(
            "PDF_PATCH_START | file=%s | page=%d | block_id=%s",
            input_path.name,
            page_number,
            block.block_id,
        )

        doc = None

        try:
            doc = fitz.open(input_path)
            page = doc[page_number - 1]

            # -------------------------------------------------
            # Search for exact text occurrence
            # -------------------------------------------------
            matches = page.search_for(old_text)

            if not matches:
                logger.error(
                    "PDF_PATCH_TEXT_NOT_FOUND | page=%d | text=%s",
                    page_number,
                    old_text,
                )
                raise ValueError("Target text not found in PDF")

            if len(matches) > 1:
                logger.error(
                    "PDF_PATCH_AMBIGUOUS | page=%d | text=%s | matches=%d",
                    page_number,
                    old_text,
                    len(matches),
                )
                raise ValueError("Ambiguous patch: multiple matches found")

            rect = matches[0]

            # -------------------------------------------------
            # Redact old text (single pass)
            # -------------------------------------------------
            page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()

            # -------------------------------------------------
            # Insert new text (layout-preserving)
            # -------------------------------------------------
            fontsize = rect.height * 0.75

            page.insert_textbox(
                rect,
                new_text,
                fontsize=fontsize,
                color=(0, 0, 0),
                align=fitz.TEXT_ALIGN_LEFT,
            )

            # -------------------------------------------------
            # Save patched PDF
            # -------------------------------------------------
            output_path.parent.mkdir(parents=True, exist_ok=True)
            doc.save(output_path)

            logger.info(
                "PDF_PATCH_SUCCESS | output=%s",
                output_path.name,
            )

        except Exception:
            logger.exception(
                "PDF_PATCH_FAILED | file=%s | block_id=%s",
                input_path.name,
                block.block_id,
            )
            raise

        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass