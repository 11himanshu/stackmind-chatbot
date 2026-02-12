from pathlib import Path
from typing import List, Optional
import hashlib
import json

from core.logger import get_logger
from document_intelligence.builders.docx_builder import DocxBuilder
from document_intelligence.builders.pdf_builder import PdfBuilder
from document_intelligence.builders.pptx_builder import PptxBuilder
from document_intelligence.builders.xlsx_builder import XlsxBuilder
from document_intelligence.cache.index_cache import DocumentIndexCache
from document_intelligence.schemas.document_index import DocumentIndex
from document_intelligence.schemas.block import Block

logger = get_logger(__name__)


class IngestPipeline:
    """
    Deterministic ingestion pipeline.

    Responsibilities:
    - detect file type
    - extract structural blocks
    - compute stable hashes
    - cache DocumentIndex
    """

    def __init__(self, cache: Optional[DocumentIndexCache] = None):
        self.cache = cache or DocumentIndexCache()

    def ingest(
        self,
        *,
        document_id: str,
        file_path: str,
    ) -> DocumentIndex:
        """
        Main ingest entrypoint.
        """

        path = Path(file_path)
        if not path.exists():
            logger.error("INGEST_FILE_NOT_FOUND | %s", file_path)
            raise FileNotFoundError(file_path)

        file_type = path.suffix.lower().lstrip(".")
        logger.info(
            "INGEST_START | doc_id=%s | type=%s | file=%s",
            document_id,
            file_type,
            path.name,
        )

        blocks = self._extract_blocks(path, file_type)
        hashed_blocks = self._hash_blocks(blocks)

        index = DocumentIndex(
            document_id=document_id,
            file_name=path.name,
            file_type=file_type,
            blocks=hashed_blocks,
        )
        index.build_index()

        self.cache.store(index)

        logger.info(
            "INGEST_COMPLETE | doc_id=%s | blocks=%d",
            document_id,
            len(index.blocks),
        )

        return index

    # -----------------------------------------------------

    def _extract_blocks(self, path: Path, file_type: str) -> List[Block]:
        """
        Dispatch to correct builder.
        """
        try:
            if file_type == "pdf":
                return PdfBuilder().build(path)
            if file_type == "docx":
                return DocxBuilder().build(path)
            if file_type == "pptx":
                return PptxBuilder().build(path)
            if file_type in {"xlsx", "xls"}:
                return XlsxBuilder().build(path)

            raise ValueError(f"Unsupported file type: {file_type}")

        except Exception:
            logger.exception(
                "INGEST_BUILD_FAILED | file=%s | type=%s",
                path.name,
                file_type,
            )
            raise

    # -----------------------------------------------------

    def _hash_blocks(self, blocks: List[Block]) -> List[Block]:
        """
        Compute stable content hash for each block.

        Hash rules:
        - text → raw string
        - dict/list → canonical JSON
        - None → empty string
        """
        for block in blocks:
            if block.content is None:
                raw = b""
            elif isinstance(block.content, (dict, list)):
                raw = json.dumps(
                    block.content,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            else:
                raw = str(block.content).encode("utf-8")

            block.content_hash = hashlib.sha256(raw).hexdigest()

        return blocks