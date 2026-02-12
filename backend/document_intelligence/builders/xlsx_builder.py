from pathlib import Path
from typing import List

from document_intelligence.schemas.block import Block
from core.logger import get_logger

logger = get_logger(__name__)


class XlsxBuilder:
    def build(self, path: Path) -> List[Block]:
        logger.warning(
            "XLSX_BUILDER_NOT_IMPLEMENTED | file=%s",
            path.name,
        )
        return []