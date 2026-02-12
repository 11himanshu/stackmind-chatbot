from pathlib import Path
from typing import Dict

from core.logger import get_logger
from document_intelligence.cache.index_cache import DocumentIndexCache
from document_intelligence.patcher.pdf_patcher import PdfPatcher
from document_intelligence.schemas.patch_plan import PatchPlan

logger = get_logger(__name__)


class PdfPatchExecutor:
    """
    Executes a PatchPlan against a PDF.

    Guarantees:
    - Sequential, deterministic patching
    - One output file
    - No mutation of original
    - Stops on first failure
    """

    def __init__(self):
        self.cache = DocumentIndexCache()
        self.patcher = PdfPatcher()

    def execute(
        self,
        *,
        plan: PatchPlan,
        input_pdf: Path,
        output_pdf: Path,
    ) -> Path:
        """
        Execute patch plan and return final output path.
        """

        if not input_pdf.exists():
            raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

        logger.info(
            "PATCH_EXEC_START | doc_id=%s | ops=%d",
            plan.document_id,
            len(plan.operations),
        )

        index = self.cache.get(plan.document_id)

        # We patch incrementally:
        # input -> temp -> temp -> final
        current_input = input_pdf

        for i, op in enumerate(plan.operations):
            logger.info(
                "PATCH_EXEC_OP | step=%d | block_id=%s | op=%s",
                i + 1,
                op.block_id,
                op.operation,
            )

            block = index.get_block(op.block_id)

            if op.operation != "replace":
                raise ValueError(
                    f"Unsupported PDF operation: {op.operation}"
                )

            temp_output = output_pdf.with_suffix(
                f".step{i + 1}.pdf"
            )

            self.patcher.apply_patch(
                input_path=current_input,
                output_path=temp_output,
                block=block,
                instruction=self._extract_instruction(op),
            )

            current_input = temp_output

        # Rename final temp file to requested output
        current_input.replace(output_pdf)

        logger.info(
            "PATCH_EXEC_COMPLETE | output=%s",
            output_pdf.name,
        )

        return output_pdf

    # -----------------------------------------------------

    def _extract_instruction(self, op) -> Dict[str, str]:
        """
        Normalize instruction payload.
        """

        if not isinstance(op.instruction, dict):
            raise ValueError("Patch instruction must be a dict")

        if "old_text" not in op.instruction or "new_text" not in op.instruction:
            raise ValueError("Patch instruction missing old_text or new_text")

        return {
            "old_text": op.instruction["old_text"],
            "new_text": op.instruction["new_text"],
        }