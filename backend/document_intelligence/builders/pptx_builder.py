from pathlib import Path
from typing import List

from document_intelligence.schemas.block import Block
from core.logger import get_logger

logger = get_logger(__name__)


class PptxBuilder:
    def build(self, path: Path) -> List[Block]:
        logger.warning(
            "PPTX_BUILDER_NOT_IMPLEMENTED | file=%s",
            path.name,
        )
        return []