from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.logger import get_logger
from document_intelligence.pipelines.ingest_pipeline import IngestPipeline
from document_intelligence.pipelines.analysis_pipeline import AnalysisPipeline
from document_intelligence.editors.pdf_patcher import PdfPatcher

logger = get_logger(__name__)
router = APIRouter(prefix="/document", tags=["document-intelligence"])


# =========================================================
# Request / Response schemas
# =========================================================

class DocumentProcessRequest(BaseModel):
    document_id: str
    file_path: str
    query: str | None = None
    mode: str  # ingest | analyze | patch


class DocumentProcessResponse(BaseModel):
    status: str
    data: Dict[str, Any]


# =========================================================
# Service
# =========================================================

@router.post("/process", response_model=DocumentProcessResponse)
def process_document(payload: DocumentProcessRequest):
    """
    Single clean endpoint for:
    - ingest
    - analyze
    - patch (PDF only today)
    """

    logger.info(
        "DOCUMENT_PROCESS_START | doc_id=%s | mode=%s",
        payload.document_id,
        payload.mode,
    )

    try:
        # -------------------------------------------------
        # INGEST
        # -------------------------------------------------
        if payload.mode == "ingest":
            index = IngestPipeline().ingest(
                document_id=payload.document_id,
                file_path=payload.file_path,
            )

            return {
                "status": "ok",
                "data": {
                    "document_id": index.document_id,
                    "blocks": len(index.blocks),
                    "file_type": index.file_type,
                },
            }

        # -------------------------------------------------
        # ANALYZE / READ
        # -------------------------------------------------
        if payload.mode == "analyze":
            if not payload.query:
                raise HTTPException(
                    status_code=400,
                    detail="query is required for analyze",
                )

            result = AnalysisPipeline().run(
                document_id=payload.document_id,
                user_query=payload.query,
            )

            return {
                "status": "ok",
                "data": result,
            }

        # -------------------------------------------------
        # PATCH (PDF only today)
        # -------------------------------------------------
        if payload.mode == "patch":
            if not payload.query:
                raise HTTPException(
                    status_code=400,
                    detail="query is required for patch",
                )

            analysis = AnalysisPipeline().run(
                document_id=payload.document_id,
                user_query=payload.query,
            )

            if analysis["mode"] != "patch_plan":
                raise HTTPException(
                    status_code=400,
                    detail="Patch intent not detected",
                )

            plan = analysis["plan"]

            input_path = Path(payload.file_path)
            output_path = input_path.with_name(
                f"{input_path.stem}_patched{input_path.suffix}"
            )

            patcher = PdfPatcher()

            for step in plan["steps"]:
                patcher.apply_patch(
                    input_path=input_path,
                    output_path=output_path,
                    block=step["block"],
                    instruction=step["instruction"],
                )

            return {
                "status": "ok",
                "data": {
                    "patched_file": str(output_path),
                    "steps_applied": len(plan["steps"]),
                },
            }

        # -------------------------------------------------
        # INVALID MODE
        # -------------------------------------------------
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported mode: {payload.mode}",
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception("DOCUMENT_PROCESS_FAILED")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )